"""
Sincronización de la réplica de empleados contra la Estancia.

    GET {ESTANCIA_EMPLEADOS_URL}?incluir_bajas=1&page_size=1000&page=N
    Header: X-API-Key: {ESTANCIA_API_KEY}

Se pide el catálogo COMPLETO cada vez (son cientos de filas): así no dependemos de
fechas de modificación (un cambio de jerarquía en la Estancia no mueve la fecha del
empleado) y quien deje de aparecer se marca inactivo.

Reglas de seguridad:
  - Si la descarga falla a medias, no se toca la réplica (todo o nada).
  - Si la Estancia responde 0 empleados y aquí hay activos, se aborta: casi seguro es
    un error de configuración, y no queremos dejar a todos inactivos.
"""
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Empleado, SincronizacionEmpleados

PAGE_SIZE = 1000
MAX_PAGINAS = 50  # tope de seguridad: 50 000 empleados

# Campo local → campo en la respuesta de la Estancia.
MAPEO = {
    'numero_empleado': 'employee_number',
    'titulo_academico': 'academic_title',
    'nombres': 'nombres',
    'apellidos': 'apellidos',
    'sexo': 'sexo',
    'plaza': 'plaza',
    'cargo': 'jerarquia',
    'municipio_id_estancia': 'municipio_id',
    'municipio': 'municipio',
    'estado_estancia': 'estado_actual',
}
CAMPOS_ACTUALIZABLES = list(MAPEO) + ['modificado_en_estancia', 'activo']


class ErrorSincronizacion(Exception):
    """Fallo esperado (red, credenciales, respuesta inválida) con mensaje para el usuario."""


def _url_pagina(base, pagina):
    partes = urllib.parse.urlsplit(base)
    query = dict(urllib.parse.parse_qsl(partes.query))
    query.update({'incluir_bajas': '1', 'page_size': str(PAGE_SIZE), 'page': str(pagina)})
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(query)))


def descargar_empleados():
    """Devuelve la lista completa de empleados de la Estancia (incluye bajas)."""
    base = getattr(settings, 'ESTANCIA_EMPLEADOS_URL', '')
    clave = getattr(settings, 'ESTANCIA_API_KEY', '')
    if not base or not clave:
        raise ErrorSincronizacion(
            'Falta configurar ESTANCIA_EMPLEADOS_URL y ESTANCIA_API_KEY en el .env de Viajes.'
        )
    timeout = getattr(settings, 'ESTANCIA_API_TIMEOUT', 15)
    contexto = None
    if base.startswith('https') and not getattr(settings, 'ESTANCIA_API_VERIFICAR_SSL', True):
        contexto = ssl._create_unverified_context()

    resultados = []
    for pagina in range(1, MAX_PAGINAS + 1):
        req = urllib.request.Request(_url_pagina(base, pagina), headers={
            'X-API-Key': clave,
            'Accept': 'application/json',
            'User-Agent': 'INM-Viajes/sincronizar-empleados',
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=contexto) as resp:
                datos = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise ErrorSincronizacion('La Estancia rechazó la API key (401).') from e
            raise ErrorSincronizacion(f'La Estancia respondió HTTP {e.code}.') from e
        except urllib.error.URLError as e:
            raise ErrorSincronizacion(f'No se pudo conectar con la Estancia: {e.reason}') from e
        except (TimeoutError, OSError) as e:
            raise ErrorSincronizacion(f'No se pudo conectar con la Estancia: {e}') from e
        except ValueError as e:
            raise ErrorSincronizacion('La Estancia respondió algo que no es JSON.') from e

        if not isinstance(datos, dict) or not isinstance(datos.get('results'), list):
            raise ErrorSincronizacion('Respuesta inesperada de la Estancia (falta "results").')
        resultados.extend(datos['results'])
        if not datos.get('next'):
            return resultados
    raise ErrorSincronizacion(f'La Estancia devolvió más de {MAX_PAGINAS} páginas; se abortó.')


def _valores(fila):
    """Convierte una fila de la Estancia en los valores del modelo local."""
    try:
        id_estancia = int(fila['id_empleado'])
    except (KeyError, TypeError, ValueError) as e:
        raise ErrorSincronizacion(f'Fila sin id_empleado válido: {fila!r}') from e
    valores = {campo: fila.get(origen) for campo, origen in MAPEO.items()}
    for campo in MAPEO:
        if campo != 'municipio_id_estancia' and valores[campo] is None:
            valores[campo] = ''
    valores['modificado_en_estancia'] = parse_datetime(fila.get('fecha_modificacion') or '')
    valores['activo'] = valores['estado_estancia'] != 'BAJA'
    return id_estancia, valores


def aplicar_empleados(filas, ahora=None):
    """Aplica `filas` a la réplica. Devuelve (creados, actualizados, desactivados)."""
    ahora = ahora or timezone.now()
    entrantes = dict(_valores(f) for f in filas)

    with transaction.atomic():
        existentes = {e.id_estancia: e for e in Empleado.objects.select_for_update()}
        nuevos, cambiados = [], []
        for id_estancia, valores in entrantes.items():
            actual = existentes.get(id_estancia)
            if actual is None:
                nuevos.append(Empleado(id_estancia=id_estancia, sincronizado_en=ahora, **valores))
                continue
            if any(getattr(actual, c) != v for c, v in valores.items()):
                for c, v in valores.items():
                    setattr(actual, c, v)
                cambiados.append(actual)

        Empleado.objects.bulk_create(nuevos)
        Empleado.objects.bulk_update(cambiados, CAMPOS_ACTUALIZABLES)
        desactivados = (
            Empleado.objects.filter(activo=True)
            .exclude(id_estancia__in=entrantes.keys())
            .update(activo=False, sincronizado_en=ahora)
        )
        # Los que siguen igual también quedan "vistos" en esta sincronización.
        Empleado.objects.filter(id_estancia__in=entrantes.keys()).update(sincronizado_en=ahora)

    return len(nuevos), len(cambiados), desactivados


def sincronizar(origen=SincronizacionEmpleados.Origen.PROGRAMADA, usuario=None):
    """Descarga y aplica el catálogo. Siempre deja registro en `SincronizacionEmpleados`.

    Devuelve el registro. Lanza `ErrorSincronizacion` si falló (el registro queda
    guardado con `exitosa=False` y el mensaje).
    """
    registro = SincronizacionEmpleados.objects.create(origen=origen, usuario=usuario)
    try:
        filas = descargar_empleados()
        if not filas and Empleado.objects.filter(activo=True).exists():
            raise ErrorSincronizacion(
                'La Estancia devolvió 0 empleados; no se desactivó a nadie. Revisa la configuración.'
            )
        registro.recibidos = len(filas)
        registro.creados, registro.actualizados, registro.desactivados = aplicar_empleados(filas)
        registro.exitosa = True
    except ErrorSincronizacion as e:
        registro.error = str(e)
        raise
    finally:
        registro.terminada_en = timezone.now()
        registro.save()
    return registro


def ultima_sincronizacion_exitosa():
    return SincronizacionEmpleados.objects.filter(exitosa=True).first()
