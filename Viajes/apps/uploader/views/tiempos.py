"""
Captura de tiempos de atención por fecha.

Se guarda un único registro por fecha (update_or_create). El reporte de
inadmitidos consume estos datos para mostrar las filas de Hora Inicio,
Hora Fin y Tiempos de atención (Extranjeros, Mexicanos, FMA).
"""
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..models import TiemposAtencion

FECHA_MINIMA = date(2026, 5, 20)


def _minutos(valor):
    try:
        m = int(valor or 0)
    except ValueError:
        return None
    if m < 0:
        return None
    return m


@login_required
def capturar_tiempos_atencion(request):
    if request.method != 'POST':
        return redirect('admin_list')

    fecha_str = request.POST.get('fecha', '').strip()
    hora_inicio_str = request.POST.get('hora_inicio', '').strip()
    hora_fin_str = request.POST.get('hora_fin', '').strip()

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
    except ValueError:
        messages.error(request, '❌ Fecha u hora inválida.')
        return redirect('admin_list')

    if fecha < FECHA_MINIMA:
        messages.error(
            request,
            f'❌ La fecha debe ser desde {FECHA_MINIMA.strftime("%d/%m/%Y")} en adelante.'
        )
        return redirect('admin_list')

    extranjeros = _minutos(request.POST.get('extranjeros_min'))
    mexicanos = _minutos(request.POST.get('mexicanos_min'))
    fma = _minutos(request.POST.get('fma_min'))

    if extranjeros is None or mexicanos is None or fma is None:
        messages.error(request, '❌ Tiempos inválidos. Ingresa un número de minutos no negativo.')
        return redirect('admin_list')

    obj, creado = TiemposAtencion.objects.update_or_create(
        fecha=fecha,
        defaults={
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'tiempo_extranjeros': extranjeros,
            'tiempo_mexicanos': mexicanos,
            'tiempo_fma': fma,
            'usuario': request.user,
        },
    )

    accion = 'capturados' if creado else 'actualizados'
    messages.success(request, f'✅ Tiempos {accion} para {fecha.strftime("%d/%m/%Y")}.')
    return redirect('admin_list')
