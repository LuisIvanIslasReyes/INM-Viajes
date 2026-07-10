"""
Vistas del módulo Redacciones (biblioteca documental compartida).

- Consulta / descarga / vista previa: todos los roles autenticados (incluye General).
- Subida / edición / eliminación: solo SuperUser y Aeropuerto
  (@puede_gestionar_redacciones_required).
"""
import os
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from apps.cuentas.roles import puede_gestionar_redacciones_required
from .forms import RedaccionForm
from .models import Pais, Redaccion, ResolucionChoices
from .utils.busqueda import extraer_palabras, resaltar, snippet
from .utils.conversion import generar_preview
from .utils.extraccion import actualizar_texto


@login_required
def biblioteca(request):
    """Biblioteca con filtros combinables: Búsqueda + Resolución + Tema + País + Fecha."""
    docs = Redaccion.objects.select_related('pais', 'subido_por')

    # Buscador de palabras: cada palabra debe aparecer en título, tema, país
    # o dentro del contenido del documento (texto extraído del PDF).
    q = (request.GET.get('q') or '').strip()
    palabras = extraer_palabras(q)
    for palabra in palabras:
        docs = docs.filter(
            Q(titulo__icontains=palabra)
            | Q(tema__icontains=palabra)
            | Q(pais__nombre__icontains=palabra)
            | Q(texto_contenido__icontains=palabra)
        )

    resolucion = (request.GET.get('resolucion') or '').strip()
    if resolucion in ResolucionChoices.values:
        docs = docs.filter(resolucion=resolucion)

    tema = (request.GET.get('tema') or '').strip()
    if tema:
        docs = docs.filter(tema__icontains=tema)

    pais_id = (request.GET.get('pais') or '').strip()
    if pais_id.isdigit():
        docs = docs.filter(pais_id=int(pais_id))

    # Rango de fechas de creación (inclusive). Puede venir solo una de las dos.
    # Los límites se calculan como datetimes en Python: el lookup __date en MySQL
    # depende de CONVERT_TZ, que devuelve NULL si el servidor no tiene cargadas
    # las tablas de zonas horarias.
    fecha_desde = (request.GET.get('fecha_desde') or '').strip()
    fecha_hasta = (request.GET.get('fecha_hasta') or '').strip()
    desde = parse_date(fecha_desde)
    hasta = parse_date(fecha_hasta)
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
    tz = timezone.get_current_timezone()
    if desde:
        docs = docs.filter(
            fecha_creacion__gte=datetime.combine(desde, time.min, tzinfo=tz)
        )
    if hasta:
        docs = docs.filter(
            fecha_creacion__lt=datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=tz)
        )

    paginator = Paginator(docs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Match finder: resalta las coincidencias en los metadatos y arma un
    # fragmento del contenido donde aparece la primera palabra encontrada.
    if palabras:
        for doc in page_obj:
            doc.titulo_res = resaltar(doc.titulo, palabras)
            doc.tema_res = resaltar(doc.tema, palabras)
            doc.pais_res = resaltar(doc.pais.nombre, palabras)
            doc.snippet = snippet(doc.texto_contenido, palabras)

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'q': q,
        'paises': Pais.objects.all(),
        'temas': Redaccion.objects.order_by('tema').values_list('tema', flat=True).distinct(),
        'resoluciones': ResolucionChoices.choices,
        'resolucion': resolucion,
        'tema': tema,
        'pais_id': pais_id,
        'fecha_desde': fecha_desde if desde else '',
        'fecha_hasta': fecha_hasta if hasta else '',
        'querystring': params.urlencode(),
        'total': paginator.count,
    }
    return render(request, 'redacciones/biblioteca.html', context)


@puede_gestionar_redacciones_required
def subir(request):
    """Alta de documento (solo SuperUser/Aeropuerto). Genera vista previa PDF."""
    if request.method == 'POST':
        form = RedaccionForm(request.POST, request.FILES)
        if form.is_valid():
            redaccion = form.save(commit=False)
            redaccion.subido_por = request.user
            redaccion.save()

            # Vista previa: los PDF se muestran directo; los Word se convierten.
            if not redaccion.es_pdf:
                if not generar_preview(redaccion):
                    messages.warning(
                        request,
                        'El documento se guardó, pero no se pudo generar la vista previa. '
                        'Estará disponible para descarga.'
                    )
            actualizar_texto(redaccion)
            messages.success(request, f'Documento "{redaccion.titulo}" agregado a la biblioteca.')
            return redirect('redacciones:detalle', pk=redaccion.pk)
    else:
        form = RedaccionForm()

    temas = Redaccion.objects.order_by('tema').values_list('tema', flat=True).distinct()
    return render(request, 'redacciones/subir.html', {'form': form, 'temas': temas})


@puede_gestionar_redacciones_required
def editar(request, pk):
    """Edición de metadatos y, opcionalmente, reemplazo del archivo (solo SuperUser/Aeropuerto)."""
    redaccion = get_object_or_404(Redaccion, pk=pk)

    if request.method == 'POST':
        # form.is_valid() (construct_instance) sustituye redaccion.archivo por el
        # archivo nuevo subido, así que capturamos AQUÍ la referencia al anterior
        # para poder borrarlo del storage recién guardado el nuevo.
        archivo_anterior = redaccion.archivo.name or ''
        storage_anterior = redaccion.archivo.storage

        form = RedaccionForm(request.POST, request.FILES, instance=redaccion)
        form.fields['archivo'].required = False
        if form.is_valid():
            reemplaza_archivo = 'archivo' in request.FILES
            if reemplaza_archivo:
                # El preview (archivo_pdf) no está en el form, así que aquí sigue
                # apuntando al anterior: se puede borrar antes de guardar.
                if redaccion.archivo_pdf:
                    redaccion.archivo_pdf.delete(save=False)
                redaccion.archivo_pdf = None

            redaccion = form.save()

            if reemplaza_archivo:
                # Ya persistido el nuevo archivo, borramos el anterior del storage.
                if archivo_anterior and archivo_anterior != redaccion.archivo.name:
                    storage_anterior.delete(archivo_anterior)
                if not redaccion.es_pdf and not generar_preview(redaccion):
                    messages.warning(
                        request,
                        'El documento se actualizó, pero no se pudo generar la vista previa. '
                        'Estará disponible para descarga.'
                    )
                actualizar_texto(redaccion)
            messages.success(request, f'Documento "{redaccion.titulo}" actualizado.')
            return redirect('redacciones:detalle', pk=redaccion.pk)
    else:
        form = RedaccionForm(instance=redaccion)
        form.fields['archivo'].required = False

    temas = Redaccion.objects.order_by('tema').values_list('tema', flat=True).distinct()
    return render(request, 'redacciones/editar.html', {
        'form': form, 'redaccion': redaccion, 'temas': temas,
    })


@puede_gestionar_redacciones_required
@require_POST
def eliminar(request, pk):
    """Elimina el documento y sus archivos asociados (solo SuperUser/Aeropuerto)."""
    redaccion = get_object_or_404(Redaccion, pk=pk)
    titulo = redaccion.titulo
    if redaccion.archivo:
        redaccion.archivo.delete(save=False)
    if redaccion.archivo_pdf:
        redaccion.archivo_pdf.delete(save=False)
    redaccion.delete()
    messages.success(request, f'Documento "{titulo}" eliminado de la biblioteca.')
    return redirect('redacciones:biblioteca')


@login_required
def detalle(request, pk):
    """Ficha del documento con vista previa (PDF) y descarga."""
    redaccion = get_object_or_404(
        Redaccion.objects.select_related('pais', 'subido_por'), pk=pk
    )
    return render(request, 'redacciones/detalle.html', {'redaccion': redaccion})


@login_required
@xframe_options_sameorigin
def preview(request, pk):
    """
    Sirve el PDF de vista previa embebible en un iframe del mismo origen.

    Necesario porque XFrameOptionsMiddleware pone X-Frame-Options: DENY en las
    respuestas de media, lo que impide mostrarlas en un iframe. El decorador
    lo sobrescribe a SAMEORIGIN solo para esta vista.
    """
    redaccion = get_object_or_404(Redaccion, pk=pk)
    if redaccion.es_pdf and redaccion.archivo:
        archivo = redaccion.archivo
    elif redaccion.archivo_pdf:
        archivo = redaccion.archivo_pdf
    else:
        raise Http404('Sin vista previa disponible')
    return FileResponse(archivo.open('rb'), content_type='application/pdf')


@login_required
def descargar(request, pk):
    """Descarga del archivo original."""
    redaccion = get_object_or_404(Redaccion, pk=pk)
    return FileResponse(
        redaccion.archivo.open('rb'),
        as_attachment=True,
        filename=os.path.basename(redaccion.archivo.name),
    )
