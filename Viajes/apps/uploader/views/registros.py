"""
Vistas relacionadas con la gestión de registros de pasajeros
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.http import JsonResponse
from django.urls import reverse
from datetime import datetime, timedelta, time, timezone as dt_timezone
import logging
from decouple import config

from ..models import Registro, UploadBatch, Notificacion, CasoEspecial
from ..utils.paises import get_paises

MESES_ES = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
    7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
}
@login_required
def update_registro(request, registro_id):
    """Vista para actualizar campos (TODOS pueden editar TODO)"""
    from urllib.parse import urlencode
    from django.urls import reverse
    
    if request.method == 'POST':
        try:
            registro = Registro.objects.get(id=registro_id)
            
            # ✅ SIN VALIDACIÓN DE PERMISOS - Todos pueden editar todo
            
            # Actualizar campos según la nueva lógica:
            # SR (Segunda Revisión) = segunda_revision
            # R (Rechazo) = rechazado
            # I (Internación) = internacion
            
            if 'segunda_revision' in request.POST:
                # Toggle Segunda Revisión
                registro.segunda_revision = request.POST.get('segunda_revision') == 'true'
                
                if not registro.segunda_revision:
                    # Si se desactiva SR, también desactivar R e I
                    registro.internacion = False
                    registro.rechazado = False
                    
            # R solo se puede activar si SR está activo
            elif 'rechazado' in request.POST:
                nuevo_valor = request.POST.get('rechazado') == 'true'

                # Si está intentando ACTIVAR R, validar que SR esté activo
                if nuevo_valor and not registro.segunda_revision:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': '⚠️ Debes marcar SR antes de poder rechazar.'})
                    messages.warning(request, '⚠️ Debes marcar "Segunda Revisión (SR)" antes de poder rechazar.')
                    params = request.GET.copy()
                    params['highlight'] = str(registro_id)
                    redirect_url = reverse('admin_list') + '?' + urlencode(params)
                    return redirect(redirect_url)

                # Si la validación pasa (o está desactivando), actualizar
                registro.rechazado = nuevo_valor
                # Si se marca como Rechazo, desmarcar Internación
                if registro.rechazado:
                    registro.internacion = False


            # I solo se puede activar si SR está activo
            elif 'internacion' in request.POST:
                nuevo_valor = request.POST.get('internacion') == 'true'

                # Si está intentando ACTIVAR I, validar que SR esté activo
                if nuevo_valor and not registro.segunda_revision:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': '⚠️ Debes marcar SR antes de marcar Internación.'})
                    messages.warning(request, '⚠️ Debes marcar "Segunda Revisión (SR)" antes de marcar Internación (I).')
                    params = request.GET.copy()
                    params['highlight'] = str(registro_id)
                    redirect_url = reverse('admin_list') + '?' + urlencode(params)
                    return redirect(redirect_url)

                # Si la validación pasa (o está desactivando), actualizar
                registro.internacion = nuevo_valor
                # Si se marca I, desmarcar Rechazo
                if registro.internacion:
                    registro.rechazado = False
            
            elif 'comentario' in request.POST:
                registro.comentario = request.POST.get('comentario')
            
            registro.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'segunda_revision': registro.segunda_revision,
                    'rechazado': registro.rechazado,
                    'internacion': registro.internacion,
                })

            messages.success(request, '✅ Registro actualizado exitosamente.')

            # Mantener TODOS los parámetros GET que venían en la URL
            params = request.GET.copy()

            # Agregar el parámetro highlight
            params['highlight'] = str(registro_id)

            # Construir la URL completa manteniendo búsqueda, filtros, paginación, etc.
            redirect_url = reverse('admin_list') + '?' + urlencode(params)
            return redirect(redirect_url)
            
        except Registro.DoesNotExist:
            messages.error(request, '❌ Registro no encontrado.')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {str(e)}')
    
    return redirect('admin_list')


@login_required
def admin_list(request):
    """Vista para ver y modificar registros (TODOS VEN TODO)"""
    # TODOS ven TODOS los registros
    registros = Registro.objects.select_related('batch', 'batch__usuario').all()
    batches = UploadBatch.objects.all().order_by('-fecha_carga')
    
    # Filtro de búsqueda por documento o pasajero
    search = request.GET.get('search')
    if search:
        registros = registros.filter(
            models.Q(numero_documento__icontains=search) |
            models.Q(nombre_pasajero__icontains=search)
        )
    
    # Filtro por batch
    batch_id = request.GET.get('batch')
    if batch_id:
        registros = registros.filter(batch_id=batch_id)
    
    # Filtro por Segunda Revisión (SR)
    segunda_revision = request.GET.get('segunda_revision')
    if segunda_revision == 'true':
        registros = registros.filter(segunda_revision=True)
    
    # Filtro por Rechazo (R)
    rechazado = request.GET.get('rechazado')
    if rechazado == 'true':
        registros = registros.filter(rechazado=True)
    
    # Filtro por Punto de Internación (PI)
    internacion = request.GET.get('internacion')
    if internacion == 'true':
        registros = registros.filter(internacion=True)
    
    # Paginación
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contar notificaciones no leídas para el usuario actual
    notificaciones_no_leidas = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).count()

    # Contar casos especiales pendientes (incluye urgentes sin_documento)
    casos_pendientes = CasoEspecial.objects.filter(estado='pendiente').count()
    casos_urgentes = CasoEspecial.objects.filter(estado='pendiente', razon='sin_documento').count()

    # Detectar si estamos en producción (cuando DJANGO_ENV != 'local')
    is_production = config('DJANGO_ENV', default='local') != 'local'

    context = {
        'page_obj': page_obj,
        'batches': batches,
        'is_superuser': request.user.is_superuser,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'casos_pendientes': casos_pendientes,
        'casos_urgentes': casos_urgentes,
        'is_production': is_production,
        'paises': get_paises(),
    }

    return render(request, 'uploader/admin_list.html', context)


@login_required
def generar_pin(request, fecha):
    """Vista para generar el PIN oficial del INM por fecha"""
    logger = logging.getLogger(__name__)
    
    # Convertir string de fecha a objeto date
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f'Fecha inválida recibida: {fecha} - Error: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Fecha inválida'}, status=400)
        messages.error(request, '❌ Fecha inválida.')
        return redirect('date_range_report')
    
    # Filtrar por rango de datetime en UTC para coincidir con cómo
    # date_range_report agrupa los registros (usa .date() sobre datetime UTC).
    # Evita el lookup __date que con USE_TZ=True convierte a la zona local
    # y desplaza la fecha de los registros antiguos (naive guardados como UTC).
    inicio_utc = datetime.combine(fecha_obj, time.min, tzinfo=dt_timezone.utc)
    fin_utc = inicio_utc + timedelta(days=1)
    registros_del_dia = Registro.objects.filter(
        vuelo_fecha__gte=inicio_utc,
        vuelo_fecha__lt=fin_utc,
    )

    if not registros_del_dia.exists():
        logger.warning(f'No se encontraron registros para la fecha: {fecha_obj}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': f'No se encontraron registros para la fecha {fecha_obj.strftime("%d/%m/%Y")}'}, status=404)
        messages.error(request, f'❌ No se encontraron registros para la fecha {fecha_obj.strftime("%d/%m/%Y")}')
        return redirect('date_range_report')

    # Desglose por destino para el PIN Binacional.
    # Se combinan varias señales porque batch.tipo_vuelo puede estar en
    # NULL (lotes cargados antes de la migración 0008 o cuando el primer
    # registro no contenía TIJ/MEX): tipo_vuelo del batch, nombre del
    # archivo cargado y aeropuerto_llegada en sus variantes habituales.
    filtro_tij = (
        models.Q(batch__tipo_vuelo='PEK-TIJ') |
        models.Q(batch__archivo__icontains='PEK-TIJ') |
        models.Q(aeropuerto_llegada__icontains='TIJ') |
        models.Q(aeropuerto_llegada__icontains='TIJUANA') |
        models.Q(aeropuerto_llegada__icontains='蒂华纳')
    )
    filtro_mex = (
        models.Q(batch__tipo_vuelo='PEK-MEX') |
        models.Q(batch__archivo__icontains='PEK-MEX') |
        models.Q(aeropuerto_llegada__icontains='MEX') |
        models.Q(aeropuerto_llegada__icontains='MEXICO') |
        models.Q(aeropuerto_llegada__icontains='MÉXICO') |
        models.Q(aeropuerto_llegada__icontains='墨西哥')
    )

    # El PIN reporta sólo arribos (HU7925 PEK→TIJ / PEK→MEX). Si el día
    # incluye cargas de regreso (HU7926 MEX→PEK) sus pasajeros no deben
    # entrar a ningún conteo, porque inflan el total y no pertenecen al
    # desglose local/tránsito.
    registros_arribos = registros_del_dia.filter(filtro_tij | filtro_mex).distinct()

    total_pasajeros = registros_arribos.count()

    registros_sr = registros_arribos.filter(segunda_revision=True)
    total_sr = registros_sr.count()

    registros_internacion = registros_sr.filter(internacion=True)
    total_internaciones = registros_internacion.count()

    registros_rechazo = registros_sr.filter(rechazado=True)
    total_rechazos = registros_rechazo.count()

    # Conexiones = pasajeros PEK→MEX (tránsito) que no fueron rechazados
    registros_mex = registros_arribos.filter(filtro_mex)
    rechazados_mex = registros_mex.filter(rechazado=True).count()
    total_conexiones = registros_mex.count() - rechazados_mex

    total_pekin_tijuana = registros_arribos.filter(filtro_tij).count()
    total_pekin_mexico = registros_arribos.filter(filtro_mex).count()
    
    # El PIN siempre reporta el vuelo HU7925 (Pekín → Tijuana), independientemente del Excel.
    vuelo_numero = 'HU7925'
    
    # Datos completos de personas rechazadas
    rechazados_detalle = []
    for registro in registros_rechazo:
        # Obtener las URLs de las fotos de rechazo
        fotos_urls = []
        fotos_rechazo = registro.fotos_rechazo.all()
        for foto in fotos_rechazo:
            fotos_urls.append(request.build_absolute_uri(foto.foto.url))
        
        rechazados_detalle.append({
            'nombre': registro.nombre_pasajero,
            'genero': 'HOMBRE' if registro.genero == 'M' else 'MUJER' if registro.genero == 'F' else 'N/A',
            'nacionalidad': registro.pais_emision or 'N/A',
            'pasaporte': registro.numero_documento,
            'fecha_nacimiento': registro.fecha_nacimiento.strftime('%d.%m.%Y') if registro.fecha_nacimiento else 'N/A',
            'fotos': fotos_urls
        })
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            return JsonResponse({
                'fecha': fecha_obj.strftime('%Y-%m-%d'),
                'vuelo_numero': vuelo_numero,
                'total_pasajeros': total_pasajeros,
                'total_pekin_tijuana': total_pekin_tijuana,
                'total_pekin_mexico': total_pekin_mexico,
                'total_sr': total_sr,
                'total_internaciones': total_internaciones,
                'total_rechazos': total_rechazos,
                'total_conexiones': total_conexiones,
                'rechazados_detalle': rechazados_detalle,
            })
        except Exception as e:
            logger.error(f'Error al generar JSON del PIN: {str(e)}')
            return JsonResponse({'error': 'Error al generar el PIN'}, status=500)
    
    # Si no es AJAX, renderizar template completo (para compatibilidad)
    context = {
        'fecha': fecha_obj,
        'vuelo_numero': vuelo_numero,
        'total_pasajeros': total_pasajeros,
        'total_sr': total_sr,
        'total_internaciones': total_internaciones,
        'total_rechazos': total_rechazos,
        'total_conexiones': total_conexiones,
        'rechazados_detalle': rechazados_detalle,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/pin_reporte.html', context)


DIAS_ES = {
    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
    4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
}


def _compute_inadmitidos_data(fecha_inicio, fecha_fin):
    """Calcula los datos del reporte de inadmitidos para un rango de fechas."""
    filtro_tij = (
        models.Q(batch__tipo_vuelo='PEK-TIJ') |
        models.Q(batch__archivo__icontains='PEK-TIJ') |
        models.Q(aeropuerto_llegada__icontains='TIJ') |
        models.Q(aeropuerto_llegada__icontains='TIJUANA') |
        models.Q(aeropuerto_llegada__icontains='蒂华纳')
    )
    filtro_mex = (
        models.Q(batch__tipo_vuelo='PEK-MEX') |
        models.Q(batch__archivo__icontains='PEK-MEX') |
        models.Q(aeropuerto_llegada__icontains='MEX') |
        models.Q(aeropuerto_llegada__icontains='MEXICO') |
        models.Q(aeropuerto_llegada__icontains='MÉXICO') |
        models.Q(aeropuerto_llegada__icontains='墨西哥')
    )

    dias = []
    dia_actual = fecha_inicio
    while dia_actual <= fecha_fin:
        dias.append(dia_actual)
        dia_actual += timedelta(days=1)

    dates, raw_dates = [], []
    totals_inadmitidos, totals_internaciones, totals_sr = [], [], []
    local, transito, total_pasajeros_list = [], [], []
    nationalities_by_day = {}
    motivos_rechazo = []

    for i, dia in enumerate(dias):
        raw_dates.append(dia.strftime('%Y-%m-%d'))
        dates.append(f"{dia.day}-{MESES_ES[dia.month]}-{dia.strftime('%y')}")

        inicio_utc = datetime.combine(dia, time.min, tzinfo=dt_timezone.utc)
        fin_utc = inicio_utc + timedelta(days=1)
        registros_dia = Registro.objects.filter(
            vuelo_fecha__gte=inicio_utc,
            vuelo_fecha__lt=fin_utc,
        ).select_related('batch')
        # Sólo arribos: excluir vuelos de regreso (HU7926 MEX→PEK) que pueden
        # estar cargados el mismo día y que inflarían el total.
        registros_arribos = registros_dia.filter(filtro_tij | filtro_mex).distinct()

        inadmitidos = registros_arribos.filter(segunda_revision=True, rechazado=True)
        totals_inadmitidos.append(inadmitidos.count())
        totals_internaciones.append(registros_arribos.filter(segunda_revision=True, internacion=True).count())
        totals_sr.append(registros_arribos.filter(segunda_revision=True).count())
        local.append(registros_arribos.filter(filtro_tij).distinct().count())
        transito.append(registros_arribos.filter(filtro_mex).distinct().count())
        total_pasajeros_list.append(registros_arribos.count())

        nats_hoy = set()
        nat_counts = (
            inadmitidos
            .order_by()
            .values('pais_emision')
            .annotate(count=Count('id', distinct=True))
        )
        for item in nat_counts:
            nat = item['pais_emision'] or 'Sin especificar'
            nats_hoy.add(nat)
            if nat not in nationalities_by_day:
                nationalities_by_day[nat] = [0] * i
            nationalities_by_day[nat].append(item['count'])

        for nat in list(nationalities_by_day.keys()):
            if nat not in nats_hoy:
                nationalities_by_day[nat].append(0)

        if dia == fecha_fin:
            for registro in inadmitidos:
                comentario = (registro.comentario or '').strip()
                if comentario and comentario.lower() != 'none':
                    motivos_rechazo.append({
                        'nombre': registro.nombre_pasajero or 'Sin nombre',
                        'nacionalidad': registro.pais_emision or 'Sin especificar',
                        'numero_documento': registro.numero_documento or 'Sin documento',
                        'fecha': dates[i],
                        'comentario': comentario,
                    })

    return {
        'vuelo': 'HU7925',
        'origen': 'China',
        'dates': dates,
        'raw_dates': raw_dates,
        'nationalities': nationalities_by_day,
        'totals_inadmitidos': totals_inadmitidos,
        'totals_internaciones': totals_internaciones,
        'totals_sr': totals_sr,
        'local': local,
        'transito': transito,
        'total_pasajeros': total_pasajeros_list,
        'motivos_rechazo': motivos_rechazo,
    }


@login_required
def inadmitidos_page(request):
    """Página principal del reporte de inadmitidos"""
    return render(request, 'uploader/inadmitidos_report.html', {
        'is_superuser': request.user.is_superuser,
    })


@login_required
def inadmitidos_data(request):
    """Endpoint AJAX que devuelve datos de inadmitidos por rango de fechas"""
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    if not fecha_inicio_str or not fecha_fin_str:
        return JsonResponse({'error': 'Se requieren fecha_inicio y fecha_fin'}, status=400)

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)

    if fecha_fin < fecha_inicio:
        return JsonResponse({'error': 'La fecha fin debe ser mayor o igual a la fecha inicio'}, status=400)

    data = _compute_inadmitidos_data(fecha_inicio, fecha_fin)
    return JsonResponse(data)


@login_required
def generar_inadmitidos_pdf(request):
    """Genera el reporte de inadmitidos como PDF con ReportLab"""
    from io import BytesIO
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    if not fecha_inicio_str or not fecha_fin_str:
        return HttpResponse('Se requieren fecha_inicio y fecha_fin', status=400)

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse('Formato de fecha inválido', status=400)

    if fecha_fin < fecha_inicio:
        return HttpResponse('La fecha fin debe ser mayor o igual a la fecha inicio', status=400)

    data = _compute_inadmitidos_data(fecha_inicio, fecha_fin)
    n = len(data['dates'])
    nats = list(data['nationalities'].keys())

    # Colores
    ROJO = HexColor('#700606')
    ROSA = HexColor('#FED8D8')
    GRIS = HexColor('#DDDDDD')
    BLANCO_GRIS = HexColor('#F3F3F2')

    # Orientación según cantidad de días
    pagesize = landscape(letter) if n > 5 else letter
    page_w = pagesize[0] - 72  # ancho disponible con márgenes de 36pt

    label_w = 165
    date_col_w = max((page_w - label_w) / n, 55) if n > 0 else page_w
    col_widths = [label_w] + [date_col_w] * n

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
    )

    # ─── Filas de la tabla ───
    rows = []

    # Fila 0: encabezado Vuelo / Origen
    if n >= 3:
        header_row = ['Vuelo:', data['vuelo'], 'Origen:', data['origen']] + [''] * (n - 3)
    elif n == 2:
        header_row = ['Vuelo:', data['vuelo'], f"Origen: {data['origen']}"]
    else:
        header_row = [f"Vuelo: {data['vuelo']}   Origen: {data['origen']}"] + [''] * n
    rows.append(header_row)

    # Fila 1: INADMITIDOS (span completo)
    rows.append(['INADMITIDOS'] + [''] * n)

    # Fila 2: días de la semana
    day_names = [DIAS_ES[datetime.strptime(r, '%Y-%m-%d').date().weekday()] for r in data['raw_dates']]
    rows.append([''] + day_names)

    # Fila 3: Nacionalidad + fechas
    rows.append(['Nacionalidad'] + data['dates'])

    # Filas de nacionalidades
    NAT_START = 4
    for nat in nats:
        rows.append([nat] + [str(v) for v in data['nationalities'][nat]])

    nat_count = len(nats)

    # 2 filas vacías
    blank1 = len(rows); rows.append([''] * (n + 1))
    blank2 = len(rows); rows.append([''] * (n + 1))

    # Total Inadmitidos
    r_total_inad = len(rows)
    rows.append(['Total Inadmitidos'] + [str(v) for v in data['totals_inadmitidos']])

    # Separador
    r_sep1 = len(rows); rows.append([''] * (n + 1))

    # Total Internaciones / Total SR
    r_total_int = len(rows)
    rows.append(['Total Internaciones:'] + [str(v) for v in data['totals_internaciones']])
    r_total_sr = len(rows)
    rows.append(['Total Segundas Revisiones:'] + [str(v) for v in data['totals_sr']])

    # Separador
    r_sep2 = len(rows); rows.append([''] * (n + 1))

    # Local / Tránsito / Total pasajeros
    r_local = len(rows); rows.append(['Local:'] + [str(v) for v in data['local']])
    r_trans = len(rows); rows.append(['En tr\xe1nsito:'] + [str(v) for v in data['transito']])
    r_total_pas = len(rows); rows.append(['Total pasajeros:'] + [str(v) for v in data['total_pasajeros']])

    # ─── Estilos ───
    cmd = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),

        # Fila 0: encabezado rojo
        ('BACKGROUND', (0, 0), (-1, 0), ROJO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        # Fila 1: INADMITIDOS rosado
        ('SPAN', (0, 1), (-1, 1)),
        ('BACKGROUND', (0, 1), (-1, 1), ROSA),
        ('TEXTCOLOR', (0, 1), (-1, 1), ROJO),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),

        # Fila 2: días de semana rojo
        ('BACKGROUND', (0, 2), (-1, 2), ROJO),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),

        # Fila 3: Nacionalidad/fechas rosado
        ('BACKGROUND', (0, 3), (-1, 3), ROSA),
        ('TEXTCOLOR', (0, 3), (-1, 3), ROJO),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
        ('ALIGN', (0, 3), (0, 3), 'LEFT'),

        # Total Inadmitidos rojo
        ('BACKGROUND', (0, r_total_inad), (-1, r_total_inad), ROJO),
        ('TEXTCOLOR', (0, r_total_inad), (-1, r_total_inad), colors.white),
        ('FONTNAME', (0, r_total_inad), (-1, r_total_inad), 'Helvetica-Bold'),

        # Total Internaciones / SR rosado
        ('BACKGROUND', (0, r_total_int), (-1, r_total_int), ROSA),
        ('TEXTCOLOR', (0, r_total_int), (-1, r_total_int), ROJO),
        ('FONTNAME', (0, r_total_int), (-1, r_total_int), 'Helvetica-Bold'),
        ('BACKGROUND', (0, r_total_sr), (-1, r_total_sr), ROSA),
        ('TEXTCOLOR', (0, r_total_sr), (-1, r_total_sr), ROJO),
        ('FONTNAME', (0, r_total_sr), (-1, r_total_sr), 'Helvetica-Bold'),

        # Local / Tránsito blanco-gris
        ('BACKGROUND', (0, r_local), (-1, r_local), BLANCO_GRIS),
        ('BACKGROUND', (0, r_trans), (-1, r_trans), BLANCO_GRIS),

        # Total pasajeros gris + negrita
        ('BACKGROUND', (0, r_total_pas), (-1, r_total_pas), GRIS),
        ('FONTNAME', (0, r_total_pas), (-1, r_total_pas), 'Helvetica-Bold'),

        # Separadores y filas vacías en blanco-gris
        ('BACKGROUND', (0, blank1), (-1, blank1), BLANCO_GRIS),
        ('BACKGROUND', (0, blank2), (-1, blank2), BLANCO_GRIS),
        ('BACKGROUND', (0, r_sep1), (-1, r_sep1), BLANCO_GRIS),
        ('BACKGROUND', (0, r_sep2), (-1, r_sep2), BLANCO_GRIS),
    ]

    # Span "China" en encabezado si hay columnas suficientes
    if n >= 3:
        cmd.append(('SPAN', (3, 0), (-1, 0)))

    # Colores alternos en filas de nacionalidades
    for i in range(nat_count):
        row_idx = NAT_START + i
        bg = BLANCO_GRIS if i % 2 == 0 else GRIS
        cmd.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))
        cmd.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))

    tabla = Table(rows, colWidths=col_widths)
    tabla.setStyle(TableStyle(cmd))

    elements = [tabla]

    # ─── Motivos de rechazo ───
    if data['motivos_rechazo']:
        elements.append(Spacer(1, 10))
        estilo_normal = ParagraphStyle('mn', fontName='Helvetica', fontSize=8, leading=12)
        motivos_rows = []
        for m in data['motivos_rechazo']:
            texto = f"<b>Extranjero de {m['nacionalidad']}</b> [{m['fecha']}] {m['nombre']}, {m['numero_documento']}: {m['comentario']}"
            motivos_rows.append([Paragraph(texto, estilo_normal)])

        encabezado_style = ParagraphStyle('mh', fontName='Helvetica-Bold', fontSize=8, leading=12)
        motivos_rows.insert(0, [Paragraph('Motivos de rechazo del día:', encabezado_style)])

        t_motivos = Table(motivos_rows, colWidths=[page_w])
        t_motivos.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), BLANCO_GRIS),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_motivos)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    nombre = f"Inadmitidos_HU7925_{fecha_inicio_str}_{fecha_fin_str}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response