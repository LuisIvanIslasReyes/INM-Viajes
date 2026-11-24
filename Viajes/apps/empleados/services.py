"""
Sincronización de la réplica de empleados contra la Estancia.

    GET {ESTANCIA_EMPLEADOS_URL}        Header: X-API-Key: {ESTANCIA_API_KEY}

Dos modos (los dos los ofrece la Estancia en el mismo endpoint):

**Completa** — `?incluir_bajas=1&page_size=1000&page=N`. Trae todo el catálogo y
marca inactivo a quien ya no venga (también a los borrados físicamente en la
Estancia, que la incremental no ve). Corre de noche y con el botón "Sincronizar
ahora", y siempre que no haya un `proximo_desde` del que partir.

**Incremental** — `?modificado_desde=<proximo_desde anterior>&page_size=1000`. Solo
lo que cambió (bajas incluidas). La Estancia pagina por cursor: `next` trae
`modificado_desde` + `despues_de_id`; aquí se toman esos dos parámetros y se
aplican a NUESTRA URL base, en vez de seguir el `next` tal cual, porque detrás de
nginx la Estancia puede armar el `next` con otro host o sin el prefijo.

Ambos modos devuelven `proximo_desde`. Se guarda el MENOR de todas las páginas (el
de la primera): un cambio que entra mientras se recorren las páginas queda
cubierto la próxima vez. Por eso pueden llegar filas repetidas; el upsert por
`id_estancia` lo absorbe.

Si la Estancia aún no devuelve `proximo_desde` (versión vieja), la siguiente vez se
hace otra completa: nunca se pide una incremental sin un punto de partida.

Reglas de seguridad:
  - Si la descarga falla a medias, no se toca la réplica (todo o nada).
  - En la completa, si la Estancia responde 0 empleados y aquí hay activos, se
    aborta: casi seguro es un error de configuración.
"""
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import NamedTuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Empleado, SincronizacionEmpleados

Modo = SincronizacionEmpleados.Modo

PAGE_SIZE = 1000
MAX_PAGINAS = 50  # tope de seguridad: 50 000 filas

# Campo local → campo en la respuesta de la Estancia.
MAPEO = {
    'numero_empleado': 'employee_number',
    'titulo_academico': 'academic_title',
    'nombres': 'nombres',
    'apellidos': 'apellidos',
    'sexo': 'sexo',
    'plaza': 'plaza',
    'plaza_descripcion': 'plaza_descripcion',
    'jerarquia': 'jerarquia',
    'municipio_id_estancia': 'municipio_id',
    'municipio': 'municipio',
    'estado_estancia': 'estado_actual',
}
CAMPOS_ACTUALIZABLES = list(MAPEO) + ['modificado_en_estancia', 'activo']


class ErrorSincronizacion(Exception):
    """Fallo esperado (red, credenciales, respuesta inválida) con mensaje para el usuario."""


class Descarga(NamedTuple):
    filas: list
    proximo_desde: object  # datetime consciente, o None si la Estancia no lo manda


def _url(base, params):
    partes = urllib.parse.urlsplit(base)
    query = dict(urllib.parse.parse_qsl(partes.query))
    query.update(params)
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(query)))


def _fecha(valor):
    try:
        fecha = parse_datetime(valor or '')
    except ValueError:
        return None
    if fecha is not None and timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha)
    return fecha


def _pedir(url, clave, timeout, contexto):
    req = urllib.request.Request(url, headers={
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
    return datos


def _cursor_siguiente(siguiente):
    """Del `next` de la incremental solo interesan `modificado_desde` y `despues_de_id`."""
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(siguiente).query))
    cursor = {k: query[k] for k in ('modificado_desde', 'despues_de_id') if query.get(k)}
    if 'modificado_desde' not in cursor or 'despues_de_id' not in cursor:
        raise ErrorSincronizacion('La Estancia devolvió un "next" incremental sin cursor.')
    return cursor


def descargar_empleados(modificado_desde=None):
    """Descarga de la Estancia: completa (incluye bajas) o, con `modificado_desde`,
    solo lo que cambió desde esa fecha. Devuelve `Descarga(filas, proximo_desde)`."""
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

    if modificado_desde is None:
        params = {'incluir_bajas': '1', 'page_size': str(PAGE_SIZE), 'page': '1'}
    else:
        params = {'modificado_desde': modificado_desde.isoformat(), 'page_size': str(PAGE_SIZE)}

    filas, proximos = [], []
    for pagina in range(1, MAX_PAGINAS + 1):
        datos = _pedir(_url(base, params), clave, timeout, contexto)
        filas.extend(datos['results'])
        proximos.append(_fecha(datos.get('proximo_desde')))
        siguiente = datos.get('next')
        if not siguiente:
            # Si alguna página no lo trajo, no hay punto de partida confiable.
            proximo = None if None in proximos else min(proximos)
            return Descarga(filas, proximo)
        if modificado_desde is None:
            params['page'] = str(pagina + 1)
        else:
            params.update(_cursor_siguiente(siguiente))
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
    # `actualizado` (D-144) incluye cambios de plaza, jerarquía y municipio.
    valores['modificado_en_estancia'] = _fecha(fila.get('actualizado') or fila.get('fecha_modificacion'))
    valores['activo'] = valores['estado_estancia'] != 'BAJA'
    return id_estancia, valores


def aplicar_empleados(filas, ahora=None, desactivar_ausentes=True):
    """Aplica `filas` a la réplica. Devuelve (creados, actualizados, desactivados).

    `desactivar_ausentes=False` en la incremental: ahí no venir no significa nada.
    """
    ahora = ahora or timezone.now()
    entrantes = dict(_valores(f) for f in filas)  # si se repite un id, gana la última

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
        desactivados = 0
        if desactivar_ausentes:
            desactivados = (
                Empleado.objects.filter(activo=True)
                .exclude(id_estancia__in=entrantes.keys())
                .update(activo=False, sincronizado_en=ahora)
            )
        # Los que siguen igual también quedan "vistos" en esta sincronización.
        Empleado.objects.filter(id_estancia__in=entrantes.keys()).update(sincronizado_en=ahora)

    return len(nuevos), len(cambiados), desactivados


def _punto_de_partida():
    """`proximo_desde` de la última sincronización exitosa, o None (→ completa)."""
    ultima = SincronizacionEmpleados.objects.filter(exitosa=True).first()
    return ultima.proximo_desde if ultima else None


def sincronizar(origen=SincronizacionEmpleados.Origen.PROGRAMADA, usuario=None, completa=False):
    """Descarga y aplica el catálogo. Siempre deja registro en `SincronizacionEmpleados`.

    Por defecto es incremental si hay un punto de partida; `completa=True` (o no
    tenerlo) baja todo. Devuelve el registro. Lanza `ErrorSincronizacion` si falló
    (el registro queda guardado con `exitosa=False` y el mensaje).
    """
    desde = None if completa else _punto_de_partida()
    modo = Modo.COMPLETA if desde is None else Modo.INCREMENTAL
    registro = SincronizacionEmpleados.objects.create(origen=origen, usuario=usuario, modo=modo)
    try:
        descarga = descargar_empleados(modificado_desde=desde)
        if modo == Modo.COMPLETA and not descarga.filas and Empleado.objects.filter(activo=True).exists():
            raise ErrorSincronizacion(
                'La Estancia devolvió 0 empleados; no se desactivó a nadie. Revisa la configuración.'
            )
        registro.recibidos = len(descarga.filas)
        registro.creados, registro.actualizados, registro.desactivados = aplicar_empleados(
            descarga.filas, desactivar_ausentes=(modo == Modo.COMPLETA),
        )
        registro.proximo_desde = descarga.proximo_desde
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
