"""
Vistas relacionadas con la captura manual de menores de edad
que no vienen en el manifiesto Excel de China.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time

from ..models import UploadBatch, Registro
from ..utils.paises import get_paises


GENERO_MAP = {'Hombre': 'M', 'Mujer': 'F', 'Otro': 'X'}
TIPO_VUELO_MAP = {
    'Local':    {'tipo_vuelo': 'PEK-TIJ', 'aeropuerto_llegada': 'TIJ'},
    'Transito': {'tipo_vuelo': 'PEK-MEX', 'aeropuerto_llegada': 'MEX'},
}


def _resolver_pais(nacionalidad_input):
    """Busca en el catálogo el país cuyo nombre coincide (case-insensitive)
    con lo que tecleó el usuario. Devuelve (nombre_canonico, codigo) o
    (input_original, '') si no hay match."""
    if not nacionalidad_input:
        return nacionalidad_input, ''
    objetivo = nacionalidad_input.strip().upper()
    for p in get_paises():
        if p['nombre'].upper() == objetivo:
            return p['nombre'], p['codigo']
    return nacionalidad_input, ''


@login_required
def crear_menor(request):
    """Captura manual de un menor de edad. Crea Registro asociado al
    UploadBatch del mismo día+tipo (o crea uno especial sin archivo)."""
    if request.method != 'POST':
        return redirect('admin_list')

    nombre = request.POST.get('nombre', '').strip()
    documento = request.POST.get('numero_documento', '').strip()
    genero_label = request.POST.get('genero', '').strip()
    nacionalidad = request.POST.get('nacionalidad', '').strip()
    fecha_str = request.POST.get('fecha_vuelo', '').strip()
    tipo_label = request.POST.get('tipo', '').strip()

    if not all([nombre, genero_label, nacionalidad, fecha_str, tipo_label]):
        messages.error(request, '❌ Faltan campos requeridos para registrar al menor.')
        return redirect('admin_list')

    if genero_label not in GENERO_MAP or tipo_label not in TIPO_VUELO_MAP:
        messages.error(request, '❌ Género o tipo de vuelo inválido.')
        return redirect('admin_list')

    try:
        fecha_vuelo = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, '❌ Fecha de vuelo inválida.')
        return redirect('admin_list')

    genero = GENERO_MAP[genero_label]
    tipo_info = TIPO_VUELO_MAP[tipo_label]
    tipo_vuelo = tipo_info['tipo_vuelo']
    aeropuerto_llegada = tipo_info['aeropuerto_llegada']
    pais_emision, codigo_pais = _resolver_pais(nacionalidad)

    # Reutilizar batch del día+tipo si existe; si no, crear uno sin archivo.
    batch = UploadBatch.objects.filter(
        fecha_vuelo=fecha_vuelo,
        tipo_vuelo=tipo_vuelo,
    ).order_by('-fecha_carga').first()

    if batch is None:
        batch = UploadBatch.objects.create(
            archivo=None,
            usuario=request.user,
            vuelo_numero='HU7925',
            tipo_vuelo=tipo_vuelo,
            fecha_vuelo=fecha_vuelo,
        )

    vuelo_fecha_dt = timezone.make_aware(datetime.combine(fecha_vuelo, time.min))

    registro = Registro.objects.create(
        batch=batch,
        vuelo_numero='HU7925',
        vuelo_fecha=vuelo_fecha_dt,
        aeropuerto_salida='PEK',
        aeropuerto_llegada=aeropuerto_llegada,
        nombre_pasajero=nombre,
        numero_documento=documento or None,
        numero_asiento='MENOR',
        estado_checkin='MENOR',
        numero_ticket='',
        genero=genero,
        pais_emision=pais_emision,
        codigo_pais_emision=codigo_pais,
        es_menor=True,
    )
    registro.numero_ticket = f'MENOR-{registro.id}'
    registro.save(update_fields=['numero_ticket'])

    messages.success(
        request,
        f'✅ Menor "{nombre}" capturado en vuelo {tipo_vuelo} del {fecha_vuelo.strftime("%d/%m/%Y")}.'
    )
    return redirect('admin_list')
