"""
Captura de tiempos de atención por fecha.

Se guarda un único registro por fecha (update_or_create). El reporte de
inadmitidos consume estos datos para mostrar las filas de Hora Inicio,
Hora Fin y Tiempos de atención (FMA, Mexicanos, Extranjeros, Revisiones
Secundarias).

Cada rubro acepta un input opcional de horas (`<rubro>_h`) sumado al de
minutos (`<rubro>_min`); el almacenamiento es siempre minutos totales.
"""
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..models import TiemposAtencion

FECHA_MINIMA = date(2026, 5, 20)

RUBROS = [
    ('fma', 'tiempo_fma'),
    ('mexicanos', 'tiempo_mexicanos'),
    ('extranjeros', 'tiempo_extranjeros'),
    ('revisiones_secundarias', 'tiempo_revisiones_secundarias'),
]


def _minutos_rubro(post, prefijo):
    """Lee `<prefijo>_h` (opcional) y `<prefijo>_min` y devuelve minutos totales."""
    try:
        h = int(post.get(f'{prefijo}_h') or 0)
        m = int(post.get(f'{prefijo}_min') or 0)
    except ValueError:
        return None
    if h < 0 or m < 0:
        return None
    return h * 60 + m


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

    valores = {}
    for prefijo, campo in RUBROS:
        v = _minutos_rubro(request.POST, prefijo)
        if v is None:
            messages.error(request, '❌ Tiempos inválidos. Ingresa números no negativos.')
            return redirect('admin_list')
        valores[campo] = v

    _, creado = TiemposAtencion.objects.update_or_create(
        fecha=fecha,
        defaults={
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin,
            'usuario': request.user,
            **valores,
        },
    )

    accion = 'capturados' if creado else 'actualizados'
    messages.success(request, f'✅ Tiempos {accion} para {fecha.strftime("%d/%m/%Y")}.')
    return redirect('admin_list')
