"""
Captura de tiempos de atención por fecha.

Se guarda un único registro por fecha (update_or_create). El reporte de
inadmitidos consume estos datos para mostrar las filas de Hora Inicio,
Hora Fin y Tiempos de atención (FMA, Mexicanos, Extranjeros, Revisiones
Secundarias).

FMA / Mexicanos / Extranjeros guardan la HORA DE TÉRMINO de su conteo (input
`<rubro>` en formato 'HH:MM', opcional); su duración se deriva en el reporte
SIEMPRE desde Hora Inicio. Revisiones Secundarias se captura aparte con su
propia ventana (`rs_hora_inicio` / `rs_hora_fin`).
"""
from datetime import date, datetime

from django.contrib import messages
from apps.cuentas.roles import flujo_principal_required
from django.http import JsonResponse
from django.shortcuts import redirect

from ..models import TiemposAtencion

FECHA_MINIMA = date(2026, 5, 20)

# Rubros que se capturan como una sola hora de término (FMA, Mexicanos,
# Extranjeros). Revisiones Secundarias ya no está aquí: tiene su propia ventana.
RUBROS = [
    ('fma', 'tiempo_fma'),
    ('mexicanos', 'tiempo_mexicanos'),
    ('extranjeros', 'tiempo_extranjeros'),
]


_HORA_INVALIDA = object()


def _hora_rubro(post, prefijo):
    """Lee `<prefijo>` como 'HH:MM'.

    Devuelve un `time`, `None` si viene vacío (rubro sin capturar) o
    `_HORA_INVALIDA` si el formato no es válido.
    """
    raw = (post.get(prefijo) or '').strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, '%H:%M').time()
    except ValueError:
        return _HORA_INVALIDA


@flujo_principal_required
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
        messages.error(request, ' Fecha u hora inválida.')
        return redirect('admin_list')

    if fecha < FECHA_MINIMA:
        messages.error(
            request,
            f' La fecha debe ser desde {FECHA_MINIMA.strftime("%d/%m/%Y")} en adelante.'
        )
        return redirect('admin_list')

    valores = {}
    for prefijo, campo in RUBROS:
        v = _hora_rubro(request.POST, prefijo)
        if v is _HORA_INVALIDA:
            messages.error(request, ' Hora de rubro inválida. Usa el formato HH:MM.')
            return redirect('admin_list')
        valores[campo] = v

    # Ventana propia de Revisiones Secundarias (Hora Inicio / Hora Fin).
    for prefijo, campo in (('rs_hora_inicio', 'rs_hora_inicio'), ('rs_hora_fin', 'rs_hora_fin')):
        v = _hora_rubro(request.POST, prefijo)
        if v is _HORA_INVALIDA:
            messages.error(request, ' Hora de Revisiones Secundarias inválida. Usa el formato HH:MM.')
            return redirect('admin_list')
        valores[campo] = v

    # Conteo de personas atendidas en la fila FMA (opcional, entero >= 0).
    # Es independiente de los registros marcados como SR.
    personas_raw = (request.POST.get('fma_personas') or '').strip()
    if not personas_raw:
        valores['fma_personas'] = None
    else:
        try:
            personas = int(personas_raw)
            if personas < 0:
                raise ValueError
        except ValueError:
            messages.error(request, ' Personas (FMA) inválido. Usa un número entero mayor o igual a 0.')
            return redirect('admin_list')
        valores['fma_personas'] = personas

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
    messages.success(request, f' Tiempos {accion} para {fecha.strftime("%d/%m/%Y")}.')
    return redirect('admin_list')


@flujo_principal_required
def obtener_tiempos_atencion(request, fecha):
    """Devuelve en JSON los tiempos guardados para una fecha, para precargar el modal."""
    try:
        f = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'existe': False, 'error': 'fecha_invalida'}, status=400)

    try:
        t = TiemposAtencion.objects.select_related('usuario').get(fecha=f)
    except TiemposAtencion.DoesNotExist:
        return JsonResponse({'existe': False})

    def _hhmm(valor):
        return valor.strftime('%H:%M') if valor else ''

    return JsonResponse({
        'existe': True,
        'hora_inicio': t.hora_inicio.strftime('%H:%M'),
        'hora_fin': t.hora_fin.strftime('%H:%M'),
        'fma': _hhmm(t.tiempo_fma),
        'fma_personas': t.fma_personas if t.fma_personas is not None else '',
        'mexicanos': _hhmm(t.tiempo_mexicanos),
        'extranjeros': _hhmm(t.tiempo_extranjeros),
        'rs_hora_inicio': _hhmm(t.rs_hora_inicio),
        'rs_hora_fin': _hhmm(t.rs_hora_fin),
        'usuario': t.usuario.username if t.usuario else '',
        'fecha_modificacion': t.fecha_modificacion.strftime('%d/%m/%Y %H:%M'),
    })
