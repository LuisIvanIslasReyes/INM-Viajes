"""
Vistas de Oficios. Solo SuperUser y Aeropuerto (`flujo_principal_required`).

Las reglas viven en services/expedientes.py; aquí solo hay formularios y redirecciones.
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.cuentas.roles import flujo_principal_required
from apps.uploader.models import Registro

from .forms import (
    BusquedaRegistrosForm,
    EvidenciaForm,
    FirmasForm,
    OficioForm,
    PersonaForm,
    PlantillaForm,
    VarianteForm,
)
from .models import (
    Evidencia,
    Expediente,
    Idioma,
    OficioInstancia,
    PersonaExpediente,
    PlantillaOficio,
    PlantillaOficioIdioma,
)
from .services import expedientes as servicio
from .services.contexto import VARIABLES
from .services.html_docx import limpiar_html
from .services.pdf import docx_a_pdf

LIMITE_REGISTROS = 100
TITULOS_SEPARADOR = ['HACE CONSTAR', 'FUNDAMENTO', 'CONSTE', 'ACUERDA', 'CÚMPLASE', 'SE CIERRA Y SE AUTORIZA LO ACTUADO']


# ---------------------------------------------------------------- expedientes

@flujo_principal_required
def lista(request):
    q = (request.GET.get('q') or '').strip()
    qs = Expediente.objects.annotate(num_personas=Count('personas')).prefetch_related(
        Prefetch('personas', queryset=PersonaExpediente.objects.only('nombre', 'expediente_id', 'orden')),
    ).select_related('firmante').order_by('-creado_en', '-pk')  # annotate() ignora Meta.ordering
    if q:
        qs = qs.filter(
            Q(folio__icontains=q) | Q(personas__nombre__icontains=q) | Q(personas__documento__icontains=q)
        ).distinct()
    page_obj = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'oficios/lista.html', {'page_obj': page_obj, 'busqueda': q})


def _buscar_registros(form):
    if not form.is_valid():
        return Registro.objects.none()
    datos = form.cleaned_data
    qs = Registro.objects.select_related('batch')
    for palabra in (datos.get('q') or '').split():
        qs = qs.filter(Q(nombre_pasajero__icontains=palabra) | Q(numero_documento__icontains=palabra))
    if datos.get('vuelo'):
        qs = qs.filter(vuelo_numero__icontains=datos['vuelo'].strip())
    if datos.get('fecha'):
        qs = qs.filter(vuelo_fecha__date=datos['fecha'])
    if datos.get('solo_marcados'):
        qs = qs.filter(Q(segunda_revision=True) | Q(rechazado=True))
    return qs.order_by('-vuelo_fecha', 'nombre_pasajero')[:LIMITE_REGISTROS]


@flujo_principal_required
def nuevo(request):
    """Buscar pasajeros del vuelo y crear un expediente (o agregarlos a uno existente)."""
    destino = None
    if request.GET.get('expediente') or request.POST.get('expediente'):
        destino = get_object_or_404(Expediente, pk=request.GET.get('expediente') or request.POST.get('expediente'))

    if request.method == 'POST':
        ids = [i for i in request.POST.getlist('registros') if i.isdigit()]
        registros = list(Registro.objects.filter(pk__in=ids).order_by('vuelo_fecha', 'nombre_pasajero'))
        if destino:
            creadas = servicio.agregar_registros(destino, registros)
            messages.success(request, f'Se agregaron {len(creadas)} persona(s) al expediente {destino.folio}.')
            return redirect('oficios:detalle', pk=destino.pk)
        if not registros and request.POST.get('accion') != 'vacio':
            messages.error(request, 'Elige al menos un pasajero, o crea el expediente vacío para capturar a mano.')
            return redirect(request.get_full_path())
        expediente = servicio.crear_expediente(request.user, registros)
        messages.success(request, f'Expediente {expediente.folio} creado.')
        return redirect('oficios:detalle', pk=expediente.pk)

    datos = request.GET.copy()
    if 'buscar' not in datos:
        datos['solo_marcados'] = 'on'
    form = BusquedaRegistrosForm(datos)
    buscando = any((datos.get(c) or '').strip() for c in ('q', 'vuelo', 'fecha'))
    registros = _buscar_registros(form) if buscando else []
    return render(request, 'oficios/nuevo.html', {
        'form': form, 'registros': registros, 'buscando': buscando, 'destino': destino,
        'limite': LIMITE_REGISTROS,
    })


def _detalle_context(expediente, firmas_form=None, nueva_form=None, persona_forms=None):
    plantillas = list(PlantillaOficio.objects.filter(activo=True))
    personas = list(expediente.personas.select_related('motivo_rechazo').prefetch_related(
        Prefetch('oficios', queryset=OficioInstancia.objects.select_related('plantilla')),
    ))
    persona_forms = persona_forms or {}
    for persona in personas:
        persona.form = persona_forms.get(persona.pk) or PersonaForm(instance=persona, prefix=f'p{persona.pk}')
        por_plantilla = {o.plantilla_id: o for o in persona.oficios.all()}
        persona.formatos = [(p, por_plantilla.get(p.pk)) for p in plantillas]
        persona.tiene_impresos = any(o.estado == OficioInstancia.Estado.IMPRESO for o in por_plantilla.values())
        persona.secciones_evidencia = _secciones_evidencia(persona, plantillas, por_plantilla)
    sugeridos = servicio.FORMATOS_SUGERIDOS.get(expediente.resultado, set())
    return {
        'expediente': expediente,
        'personas': personas,
        'plantillas_familia': [(p, p.numero in sugeridos) for p in plantillas],
        'hay_oficios': any(instancia for p in personas for _plantilla, instancia in p.formatos),
        'firmas_form': firmas_form or FirmasForm(instance=expediente),
        'nueva_form': nueva_form or PersonaForm(prefix='nueva'),
    }


def _secciones_evidencia(persona, plantillas, por_plantilla):
    """Por cada formato que lleva evidencias: las de la persona, si están bloqueadas y las fotos de Cámara."""
    con_evidencia = [p for p in plantillas if p.evidencias]
    if not con_evidencia:
        return []
    todas = list(persona.evidencias.all())
    camara = list(persona.registro.fotos_rechazo.all()) if persona.registro_id else []
    secciones = []
    for plantilla in con_evidencia:
        oficio = por_plantilla.get(plantilla.pk)
        propias = [e for e in todas if e.plantilla_id == plantilla.pk]
        usadas = {e.foto_rechazo_id for e in propias}
        secciones.append({
            'plantilla': plantilla,
            'evidencias': propias,
            'bloqueada': bool(oficio and oficio.estado == OficioInstancia.Estado.IMPRESO),
            'form': EvidenciaForm(tipo=plantilla.evidencias, prefix=f'ev{persona.pk}_{plantilla.pk}'),
            'camara': [f for f in camara if f.pk not in usadas],
        })
    return secciones


@flujo_principal_required
def detalle(request, pk):
    expediente = get_object_or_404(Expediente.objects.select_related('firmante', 'testigo_1', 'testigo_2'), pk=pk)
    return render(request, 'oficios/detalle.html', _detalle_context(expediente))


@require_POST
@flujo_principal_required
def guardar_firmas(request, pk):
    expediente = get_object_or_404(Expediente, pk=pk)
    form = FirmasForm(request.POST, instance=expediente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Firmante y testigos guardados.')
        return redirect('oficios:detalle', pk=pk)
    messages.error(request, ' '.join(form.non_field_errors()) or 'Revisa el firmante y los testigos.')
    return render(request, 'oficios/detalle.html', _detalle_context(expediente, firmas_form=form))


@require_POST
@flujo_principal_required
def agregar_persona(request, pk):
    expediente = get_object_or_404(Expediente, pk=pk)
    form = PersonaForm(request.POST, prefix='nueva')
    if form.is_valid():
        persona = form.save(commit=False)
        persona.expediente = expediente
        persona.orden = servicio.siguiente_orden(expediente)
        persona.save()
        messages.success(request, f'{persona.nombre} agregado al expediente.')
        return redirect('oficios:detalle', pk=pk)
    messages.error(request, 'Revisa los datos de la persona nueva.')
    return render(request, 'oficios/detalle.html', _detalle_context(expediente, nueva_form=form))


@require_POST
@flujo_principal_required
def editar_persona(request, pk):
    persona = get_object_or_404(PersonaExpediente, pk=pk)
    form = PersonaForm(request.POST, instance=persona, prefix=f'p{persona.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Datos de {persona.nombre} guardados.')
        return redirect(reverse('oficios:detalle', args=[persona.expediente_id]) + f'#persona-{persona.pk}')
    messages.error(request, f'Revisa los datos de {persona.nombre}.')
    return render(request, 'oficios/detalle.html',
                  _detalle_context(persona.expediente, persona_forms={persona.pk: form}))


@require_POST
@flujo_principal_required
def quitar_persona(request, pk):
    persona = get_object_or_404(PersonaExpediente, pk=pk)
    expediente_id = persona.expediente_id
    if persona.oficios.filter(estado=OficioInstancia.Estado.IMPRESO).exists():
        messages.error(request, f'{persona.nombre} ya tiene oficios impresos; no se puede quitar.')
    else:
        persona.delete()
        messages.success(request, f'{persona.nombre} se quitó del expediente.')
    return redirect('oficios:detalle', pk=expediente_id)


@require_POST
@flujo_principal_required
def crear_borradores(request, pk):
    persona = get_object_or_404(PersonaExpediente, pk=pk)
    ids = [i for i in request.POST.getlist('plantillas') if i.isdigit()]
    plantillas = PlantillaOficio.objects.filter(activo=True, pk__in=ids)
    creados = servicio.crear_borradores(persona, plantillas, request.user)
    if creados:
        messages.success(request, f'{len(creados)} borrador(es) creados para {persona.nombre}.')
        _avisar_sin_traduccion(request, creados)
    else:
        messages.info(request, 'No se creó ningún borrador: elige formatos que la persona aún no tenga.')
    return redirect(reverse('oficios:detalle', args=[persona.expediente_id]) + f'#persona-{persona.pk}')


@require_POST
@flujo_principal_required
def crear_borradores_familia(request, pk):
    expediente = get_object_or_404(Expediente, pk=pk)
    ids = [i for i in request.POST.getlist('plantillas') if i.isdigit()]
    plantillas = PlantillaOficio.objects.filter(activo=True, pk__in=ids)
    creados = servicio.crear_borradores_familia(expediente, plantillas, request.user)
    if creados:
        _avisar_sin_traduccion(request, OficioInstancia.objects.filter(
            persona__expediente=expediente).select_related('persona', 'plantilla').order_by('-pk')[:creados])
        messages.success(request, f'{creados} borrador(es) creados para la familia.')
    else:
        messages.info(request, 'No se creó ningún borrador: elige formatos que aún no tengan.')
    return redirect('oficios:detalle', pk=pk)


def _avisar_sin_traduccion(request, instancias):
    """Avisa qué borradores quedaron en español porque su formato no tiene traducción al idioma de la persona."""
    sin = [i for i in instancias if i.idioma != i.persona.idioma]
    if sin:
        detalle = ', '.join(f'{i.plantilla.clave} ({i.persona.get_idioma_display().lower()})' for i in sin)
        messages.info(request, f'Sin traducción, quedaron en español: {detalle}.')


# ---------------------------------------------------------------- evidencias (09 y 05)

def _volver_a_persona(persona):
    return redirect(reverse('oficios:detalle', args=[persona.expediente_id]) + f'#persona-{persona.pk}')


@require_POST
@flujo_principal_required
def evidencia_agregar(request, persona_pk, plantilla_pk):
    persona = get_object_or_404(PersonaExpediente, pk=persona_pk)
    plantilla = get_object_or_404(PlantillaOficio, pk=plantilla_pk)
    form = EvidenciaForm(request.POST, request.FILES, tipo=plantilla.evidencias, prefix=f'ev{persona.pk}_{plantilla.pk}')
    if not form.is_valid():
        messages.error(request, 'Revisa la evidencia: ' + ' '.join(e for errs in form.errors.values() for e in errs))
        return _volver_a_persona(persona)
    evidencia = form.save(commit=False)
    evidencia.persona, evidencia.plantilla = persona, plantilla
    try:
        servicio.guardar_evidencia(evidencia, request.user)
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        messages.success(request, f'Evidencia agregada al {plantilla.clave} de {persona.nombre}.')
    return _volver_a_persona(persona)


@flujo_principal_required
def evidencia_editar(request, pk):
    evidencia = get_object_or_404(Evidencia.objects.select_related('persona', 'plantilla'), pk=pk)
    persona, plantilla = evidencia.persona, evidencia.plantilla
    form = EvidenciaForm(request.POST or None, request.FILES or None, instance=evidencia, tipo=plantilla.evidencias)
    if request.method == 'POST' and form.is_valid():
        try:
            servicio.guardar_evidencia(form.save(commit=False), request.user)
        except servicio.ErrorOficio as e:
            messages.error(request, str(e))
        else:
            messages.success(request, 'Evidencia guardada.')
        return _volver_a_persona(persona)
    return render(request, 'oficios/evidencia.html', {
        'evidencia': evidencia, 'form': form, 'persona': persona, 'plantilla': plantilla,
        'bloqueada': servicio.evidencias_bloqueadas(persona, plantilla),
    })


@require_POST
@flujo_principal_required
def evidencia_quitar(request, pk):
    evidencia = get_object_or_404(Evidencia.objects.select_related('persona', 'plantilla'), pk=pk)
    persona = evidencia.persona
    try:
        servicio.quitar_evidencia(evidencia)
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        messages.success(request, 'Evidencia quitada.')
    return _volver_a_persona(persona)


@require_POST
@flujo_principal_required
def evidencia_camara(request, persona_pk, plantilla_pk):
    """Usa como evidencia una foto que ya está en la app Cámara para este pasajero."""
    from apps.camara.models import FotoRechazo
    persona = get_object_or_404(PersonaExpediente, pk=persona_pk)
    plantilla = get_object_or_404(PlantillaOficio, pk=plantilla_pk)
    foto = get_object_or_404(FotoRechazo, pk=request.POST.get('foto'))
    try:
        servicio.importar_de_camara(persona, plantilla, foto, request.user)
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        messages.success(request, 'Foto de Cámara agregada como evidencia.')
    return _volver_a_persona(persona)


# ---------------------------------------------------------------- paquete

def _oficios_del_expediente(expediente):
    return list(OficioInstancia.objects.filter(persona__expediente=expediente).select_related(
        'plantilla', 'persona', 'persona__motivo_rechazo', 'persona__expediente__firmante',
        'persona__expediente__testigo_1', 'persona__expediente__testigo_2', 'testigo_1', 'testigo_2',
    ))


@flujo_principal_required
def paquete(request, pk):
    """Elegir varios oficios del expediente → un solo Word o PDF (o marcarlos como impresos)."""
    expediente = get_object_or_404(Expediente, pk=pk)
    oficios = servicio.ordenar_paquete(_oficios_del_expediente(expediente))

    if request.method == 'POST':
        ids = {int(i) for i in request.POST.getlist('oficios') if i.isdigit()}
        elegidos = [o for o in oficios if o.pk in ids]
        accion = request.POST.get('accion')
        if not elegidos:
            messages.error(request, 'Elige al menos un oficio.')
        elif accion == 'imprimir':
            impresos, errores = servicio.imprimir_varios(elegidos, request.user)
            if impresos:
                messages.success(request, f'{len(impresos)} oficio(s) marcados como impresos.')
            for instancia, error in errores:
                messages.error(request, f'{instancia.plantilla.clave} · {instancia.persona.nombre}: {error}')
            if not impresos and not errores:
                messages.info(request, 'Los oficios elegidos ya estaban impresos.')
        elif accion in ('word', 'pdf'):
            docx = servicio.render_paquete(elegidos)
            if accion == 'word':
                respuesta = HttpResponse(
                    docx, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )
                nombre = servicio.nombre_paquete(expediente, elegidos, 'docx')
                respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
                return respuesta
            pdf = docx_a_pdf(docx, nombre='paquete')
            if pdf is not None:
                respuesta = HttpResponse(pdf, content_type='application/pdf')
                nombre = servicio.nombre_paquete(expediente, elegidos, 'pdf')
                respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
                return respuesta
            messages.error(request, 'No se pudo generar el PDF (LibreOffice no está disponible). Descarga el Word.')
        return redirect('oficios:paquete', pk=pk)

    personas = []
    for oficio in oficios:
        if not personas or personas[-1][0].pk != oficio.persona_id:
            personas.append((oficio.persona, []))
        personas[-1][1].append(oficio)
    return render(request, 'oficios/paquete.html', {'expediente': expediente, 'personas': personas})


# ---------------------------------------------------------------- oficio

def _oficio_o_404(pk):
    return get_object_or_404(
        OficioInstancia.objects.select_related(
            'plantilla', 'persona__expediente__firmante', 'persona__expediente__testigo_1',
            'persona__expediente__testigo_2', 'persona__motivo_rechazo', 'testigo_1', 'testigo_2',
        ),
        pk=pk,
    )


@flujo_principal_required
def oficio(request, pk):
    instancia = _oficio_o_404(pk)
    form = OficioForm(request.POST or None, instance=instancia)
    if request.method == 'POST':
        if not instancia.editable:
            messages.error(request, 'El oficio ya está impreso. Reábrelo para cambiarlo.')
            return redirect('oficios:oficio', pk=pk)
        if form.is_valid():
            datos = form.cleaned_data
            # El ModelForm ya copió los valores a `instancia`: se recarga para que el servicio compare.
            instancia.refresh_from_db()
            cambios = servicio.guardar_borrador(
                instancia, request.user, datos['contenido_html'], datos['fecha_oficio'],
                datos['testigo_1'], datos['testigo_2'],
            )
            messages.success(request, 'Oficio guardado.' if cambios else 'No había cambios que guardar.')
            return redirect('oficios:oficio', pk=pk)
        messages.error(request, 'Revisa los datos del oficio.')

    errores, avisos = servicio.revisar(instancia)
    expediente = instancia.persona.expediente
    return render(request, 'oficios/oficio.html', {
        'instancia': instancia,
        'expediente': expediente,
        'form': form,
        'errores': errores,
        'avisos': avisos,
        'variables': VARIABLES,
        'titulos_separador': TITULOS_SEPARADOR,
        'historial': instancia.historial.select_related('usuario')[:20],
        'idiomas_disponibles': [(Idioma.ESPANOL, 'Español')] + [
            (v.idioma, v.get_idioma_display()) for v in instancia.plantilla.variantes.filter(activo=True)
        ],
        'testigos_expediente': [expediente.testigo_1, expediente.testigo_2],
    })


@flujo_principal_required
def oficio_docx(request, pk):
    instancia = _oficio_o_404(pk)
    respuesta = HttpResponse(
        servicio.docx_de(instancia),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    respuesta['Content-Disposition'] = f'attachment; filename="{servicio.nombre_archivo(instancia, "docx")}"'
    return respuesta


@flujo_principal_required
def oficio_pdf(request, pk):
    instancia = _oficio_o_404(pk)
    pdf = docx_a_pdf(servicio.docx_de(instancia))
    if pdf is None:
        messages.error(request, 'No se pudo generar el PDF (LibreOffice no está disponible). Descarga el Word.')
        return redirect('oficios:oficio', pk=pk)
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    modo = 'inline' if request.GET.get('inline') == '1' else 'attachment'
    respuesta['Content-Disposition'] = f'{modo}; filename="{servicio.nombre_archivo(instancia, "pdf")}"'
    return respuesta


@require_POST
@flujo_principal_required
def oficio_recargar(request, pk):
    """Reemplaza el texto del borrador por el de la plantilla, en el idioma elegido."""
    instancia = _oficio_o_404(pk)
    idioma = request.POST.get('idioma') or Idioma.ESPANOL
    try:
        final = servicio.recargar_texto(instancia, idioma, request.user)
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        if final != idioma:
            messages.info(request, 'Ese formato no tiene traducción a ese idioma: se recargó en español.')
        else:
            messages.success(request, 'Texto recargado desde la plantilla.')
    return redirect('oficios:oficio', pk=pk)


@require_POST
@flujo_principal_required
def oficio_imprimir(request, pk):
    instancia = _oficio_o_404(pk)
    try:
        servicio.imprimir(instancia, request.user)
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        messages.success(request, 'Oficio marcado como impreso. Quedó congelado tal como se imprimió.')
    return redirect('oficios:oficio', pk=pk)


@require_POST
@flujo_principal_required
def oficio_reabrir(request, pk):
    instancia = _oficio_o_404(pk)
    try:
        servicio.reabrir(instancia, request.user, request.POST.get('motivo'))
    except servicio.ErrorOficio as e:
        messages.error(request, str(e))
    else:
        messages.success(request, 'Oficio reabierto como borrador.')
    return redirect('oficios:oficio', pk=pk)


@require_POST
@flujo_principal_required
def oficio_eliminar(request, pk):
    instancia = _oficio_o_404(pk)
    persona = instancia.persona
    if not instancia.editable:
        messages.error(request, 'Un oficio impreso no se elimina. Reábrelo primero si hay que corregirlo.')
        return redirect('oficios:oficio', pk=pk)
    instancia.delete()
    messages.success(request, f'Borrador {instancia.plantilla.clave} de {persona.nombre} eliminado.')
    return redirect(reverse('oficios:detalle', args=[persona.expediente_id]) + f'#persona-{persona.pk}')


# ---------------------------------------------------------------- plantillas

@flujo_principal_required
def plantillas(request):
    lista = PlantillaOficio.objects.prefetch_related('variantes')
    return render(request, 'oficios/plantillas.html', {
        'plantillas': lista,
        'idiomas': [c for c in Idioma.choices if c[0] != Idioma.ESPANOL],
    })


@flujo_principal_required
def plantilla_editar(request, pk):
    plantilla = get_object_or_404(PlantillaOficio, pk=pk)
    form = PlantillaForm(request.POST or None, instance=plantilla)
    if request.method == 'POST' and form.is_valid():
        plantilla = form.save(commit=False)
        plantilla.contenido_html = limpiar_html(form.cleaned_data['contenido_html'])
        plantilla.modificado_por = request.user
        plantilla.save()
        servicio.guardar_version(plantilla, request.user)
        messages.success(request, f'Plantilla {plantilla.clave} guardada. Aplica a los borradores que se creen desde ahora.')
        return redirect('oficios:plantillas')
    return render(request, 'oficios/plantilla.html', {
        'plantilla': plantilla, 'form': form, 'variables': VARIABLES, 'titulos_separador': TITULOS_SEPARADOR,
        'versiones': plantilla.historial.filter(idioma=Idioma.ESPANOL).select_related('usuario')[:10],
    })


@flujo_principal_required
def plantilla_idioma(request, pk, idioma):
    """Crear o editar la traducción de una plantilla. Se empieza con el texto en español."""
    plantilla = get_object_or_404(PlantillaOficio, pk=pk)
    if idioma not in dict(Idioma.choices) or idioma == Idioma.ESPANOL:
        messages.error(request, 'Idioma no válido.')
        return redirect('oficios:plantillas')
    variante = plantilla.variantes.filter(idioma=idioma).first()
    nueva = variante is None
    if nueva:
        variante = PlantillaOficioIdioma(
            plantilla=plantilla, idioma=idioma, titulo=f'{plantilla.titulo} / ',
            contenido_html=plantilla.contenido_html, leyenda_firma_persona='NOMBRE Y FIRMA / ',
        )
    form = VarianteForm(request.POST or None, instance=variante)
    if request.method == 'POST' and form.is_valid():
        variante = form.save(commit=False)
        contenido = limpiar_html(form.cleaned_data['contenido_html'])
        # Igual al español: se guarda vacío para que siga al español si este cambia.
        variante.contenido_html = '' if contenido == plantilla.contenido_html else contenido
        variante.modificado_por = request.user
        variante.save()
        servicio.guardar_version(plantilla, request.user, variante)
        faltan, desconocidas = servicio.comparar_variables(
            plantilla.contenido_html, variante.contenido_html or plantilla.contenido_html)
        messages.success(request, f'Traducción al {variante.get_idioma_display().lower()} de la plantilla '
                                  f'{plantilla.clave} guardada. Se usa en los borradores que se creen desde ahora.')
        if faltan or desconocidas:
            messages.warning(request, 'Revisa las variables de la traducción (ver el aviso).')
        return redirect('oficios:plantilla_idioma', pk=pk, idioma=idioma)

    texto = variante.contenido_html or plantilla.contenido_html
    faltan, desconocidas = servicio.comparar_variables(plantilla.contenido_html, texto)
    return render(request, 'oficios/plantilla_idioma.html', {
        'texto': texto, 'igual_al_espanol': not nueva and not variante.contenido_html,
        'plantilla': plantilla, 'variante': variante, 'nueva': nueva, 'form': form,
        'idioma_nombre': dict(Idioma.choices)[idioma],
        'faltan': faltan, 'desconocidas': desconocidas,
        'base_desactualizada': (not nueva and plantilla.modificado_en and variante.modificado_en
                                and plantilla.modificado_en > variante.modificado_en),
        'variables': VARIABLES, 'titulos_separador': TITULOS_SEPARADOR,
        'versiones': plantilla.historial.filter(idioma=idioma).select_related('usuario')[:10],
    })
