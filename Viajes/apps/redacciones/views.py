"""
Vistas del módulo Redacciones (biblioteca documental compartida).

- Consulta / descarga / vista previa: todos los roles autenticados (incluye General).
- Subida: solo SuperUser y Aeropuerto (@puede_subir_required).
"""
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.cuentas.roles import puede_subir_required
from .forms import RedaccionForm
from .models import Pais, Redaccion, ResolucionChoices
from .utils.conversion import generar_preview


@login_required
def biblioteca(request):
    """Biblioteca con filtros combinables: Resolución + Tema + País."""
    docs = Redaccion.objects.select_related('pais', 'subido_por')

    resolucion = (request.GET.get('resolucion') or '').strip()
    if resolucion in ResolucionChoices.values:
        docs = docs.filter(resolucion=resolucion)

    tema = (request.GET.get('tema') or '').strip()
    if tema:
        docs = docs.filter(tema__icontains=tema)

    pais_id = (request.GET.get('pais') or '').strip()
    if pais_id.isdigit():
        docs = docs.filter(pais_id=int(pais_id))

    paginator = Paginator(docs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'paises': Pais.objects.all(),
        'temas': Redaccion.objects.order_by('tema').values_list('tema', flat=True).distinct(),
        'resoluciones': ResolucionChoices.choices,
        'resolucion': resolucion,
        'tema': tema,
        'pais_id': pais_id,
        'querystring': params.urlencode(),
        'total': paginator.count,
    }
    return render(request, 'redacciones/biblioteca.html', context)


@puede_subir_required
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
            messages.success(request, f'Documento "{redaccion.titulo}" agregado a la biblioteca.')
            return redirect('redacciones:detalle', pk=redaccion.pk)
    else:
        form = RedaccionForm()

    temas = Redaccion.objects.order_by('tema').values_list('tema', flat=True).distinct()
    return render(request, 'redacciones/subir.html', {'form': form, 'temas': temas})


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
