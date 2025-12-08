"""
Vistas relacionadas con reportes y descarga de archivos
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from django.db.models import Q
from collections import OrderedDict
import os

from ..models import Registro, UploadBatch


@login_required
def date_range_report(request):
    """Vista de reporte por rango de fechas - Solo muestra registros con SR, R o I"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # FILTRO PRINCIPAL: Solo registros que tienen SR, R o I
    # (Los que no tienen nada están OK y no se muestran aquí)
    registros = Registro.objects.filter(
        Q(segunda_revision=True) | Q(rechazado=True) | Q(internacion=True)
    ).select_related('batch', 'batch__usuario').order_by('-vuelo_fecha', 'vuelo_numero')
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        registros = registros.filter(vuelo_fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(vuelo_fecha__lte=fecha_fin)
    
    # Agrupar por fecha
    registros_por_fecha = OrderedDict()
    for registro in registros:
        fecha = registro.vuelo_fecha
        if fecha not in registros_por_fecha:
            registros_por_fecha[fecha] = []
        registros_por_fecha[fecha].append(registro)
    
    # Calcular totales por fecha
    estadisticas_por_fecha = []
    for fecha, regs in registros_por_fecha.items():
        estadisticas_por_fecha.append({
            'fecha': fecha,
            'registros': regs,
            'total': len(regs),
            'segunda_revisions': sum(1 for r in regs if r.segunda_revision),
            'rechazados': sum(1 for r in regs if r.rechazado),
            'internaciones': sum(1 for r in regs if r.internacion),
        })
    
    context = {
        'fecha_inicio': fecha_inicio if fecha_inicio else '',
        'fecha_fin': fecha_fin if fecha_fin else '',
        'estadisticas_por_fecha': estadisticas_por_fecha,
        'total_registros': registros.count(),
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/date_range_report.html', context)


@login_required
def download_batch_file(request, batch_id):
    """Vista para descargar el archivo Excel de un batch"""
    batch = get_object_or_404(UploadBatch, id=batch_id)
    
    # Verificar que el archivo existe
    if not batch.archivo or not os.path.exists(batch.archivo.path):
        messages.error(request, '❌ El archivo no existe en el servidor.')
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
        messages.error(request, f'❌ Error al descargar el archivo: {str(e)}')
        return redirect('batch_list')