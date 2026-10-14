"""
Vistas relacionadas con reportes y descarga de archivos
"""
from apps.cuentas.roles import flujo_principal_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import datetime, time, timedelta, timezone as dt_timezone
from urllib.parse import urlencode
import os

from ..models import Registro, UploadBatch


DIAS_POR_PAGINA = 15


def _parse_fecha(valor):
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _inicio_dia_utc(fecha):
    return datetime.combine(fecha, time.min, tzinfo=dt_timezone.utc)


@flujo_principal_required
def date_range_report(request):
    """Vista de reporte por rango de fechas - Muestra los días con vuelos, 15 por página"""
    fecha_inicio = _parse_fecha(request.GET.get('fecha_inicio'))
    fecha_fin = _parse_fecha(request.GET.get('fecha_fin'))
    if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    registros = Registro.objects.filter(vuelo_fecha__isnull=False)

    # Filtrar por rango de datetime en UTC (igual que generar_pin). El lookup
    # __date usa CONVERT_TZ en MySQL, que devuelve NULL si el servidor no tiene
    # cargadas las tablas de zona horaria y el filtro no encuentra nada.
    if fecha_inicio:
        registros = registros.filter(vuelo_fecha__gte=_inicio_dia_utc(fecha_inicio))
    if fecha_fin:
        registros = registros.filter(vuelo_fecha__lt=_inicio_dia_utc(fecha_fin) + timedelta(days=1))

    # Totales por día calculados en la BD; sin filtro, la página 1 son los
    # últimos 15 días con vuelos. TruncDate en UTC no genera CONVERT_TZ.
    dias = (
        registros
        .annotate(dia=TruncDate('vuelo_fecha', tzinfo=dt_timezone.utc))
        .values('dia')
        .annotate(
            total=Count('id'),
            segunda_revisions=Count('id', filter=Q(segunda_revision=True)),
            rechazados=Count('id', filter=Q(rechazado=True)),
            internaciones=Count('id', filter=Q(internacion=True)),
        )
        .order_by('-dia')
    )
    page_obj = Paginator(dias, DIAS_POR_PAGINA).get_page(request.GET.get('page'))
    dias_pagina = list(page_obj.object_list)

    # Solo se cargan los registros SR, R o I de los días de esta página
    especiales_por_fecha = {}
    if dias_pagina:
        especiales = (
            registros
            .filter(
                vuelo_fecha__gte=_inicio_dia_utc(dias_pagina[-1]['dia']),
                vuelo_fecha__lt=_inicio_dia_utc(dias_pagina[0]['dia']) + timedelta(days=1),
            )
            .filter(Q(segunda_revision=True) | Q(rechazado=True) | Q(internacion=True))
            .select_related('batch')
            .order_by('-vuelo_fecha', 'vuelo_numero')
        )
        for registro in especiales:
            especiales_por_fecha.setdefault(registro.vuelo_fecha.date(), []).append(registro)

    estadisticas_por_fecha = [
        {
            'fecha': dia['dia'],
            'registros': especiales_por_fecha.get(dia['dia'], []),  # Solo mostrar SR, R, I en la tabla
            'total': dia['total'],
            'segunda_revisions': dia['segunda_revisions'],
            'rechazados': dia['rechazados'],
            'internaciones': dia['internaciones'],
        }
        for dia in dias_pagina
    ]

    filtros = {}
    if fecha_inicio:
        filtros['fecha_inicio'] = fecha_inicio.isoformat()
    if fecha_fin:
        filtros['fecha_fin'] = fecha_fin.isoformat()

    context = {
        'fecha_inicio': filtros.get('fecha_inicio', ''),
        'fecha_fin': filtros.get('fecha_fin', ''),
        'estadisticas_por_fecha': estadisticas_por_fecha,
        'page_obj': page_obj,
        'querystring': urlencode(filtros),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'uploader/date_range_report.html', context)


@flujo_principal_required
def download_batch_file(request, batch_id):
    """Vista para descargar el archivo Excel de un batch"""
    batch = get_object_or_404(UploadBatch, id=batch_id)
    
    # Verificar que el archivo existe
    if not batch.archivo or not os.path.exists(batch.archivo.path):
        messages.error(request, ' El archivo no existe en el servidor.')
        return redirect('batch_list')
    
    try:
        # Abrir el archivo para descarga
        response = FileResponse(
            open(batch.archivo.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(batch.archivo.name)
        )
        return response
    except Exception as e:
        messages.error(request, f' Error al descargar el archivo: {str(e)}')
        return redirect('batch_list')