"""
Variables que puede usar el texto de un oficio, y su valor para una instancia.

`VARIABLES` es el catálogo que ve el editor (clave, etiqueta, ejemplo). `contexto_para`
arma el diccionario real. Lo que se imprime del firmante sale de la réplica de
empleados: `nombre_para_oficio`, `cargo` (plaza en femenino si firma una mujer) y
`fundamento` (por plaza o asignado a mano).
"""
import re

from ..models import IDIOMA_EN_TEXTO, DatosOficina

MESES = (
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
)


def fecha_larga(fecha):
    """'27 de noviembre de 2026' (sin depender del locale del servidor)."""
    if not fecha:
        return ''
    return f'{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}'


def fecha_corta(fecha):
    return f'{fecha:%d/%m/%Y}' if fecha else ''


# (clave, etiqueta, ejemplo) — el orden es el del panel del editor.
VARIABLES = [
    # Oficina
    ('ciudad', 'Ciudad (dentro del texto)', 'Tijuana, B.C.'),
    ('ciudad_encabezado', 'Ciudad (junto a la fecha)', 'Tijuana, Baja California'),
    ('fecha_larga', 'Fecha del oficio', '27 de noviembre de 2026'),
    ('aeropuerto', 'Aeropuerto', 'AEROPUERTO INTERNACIONAL DE TIJUANA'),
    ('entidad', 'Entidad', 'BAJA CALIFORNIA'),
    ('terminal', 'Terminal', 'SALA INTERNACIONAL'),
    ('domicilio', 'Domicilio de la oficina', 'Carretera Aeropuerto s/n, …'),
    # Firmante
    ('firmante_nombre', 'Firmante: nombre', 'LIC. MELISSA GALLEGOS'),
    ('firmante_cargo', 'Firmante: cargo', 'JEFA DE DEPARTAMENTO'),
    ('firmante_fundamento', 'Firmante: fundamento', 'Artículo 23, fracciones I, II, III y IV'),
    ('firmante_adscrito', 'Firmante: adscrito / adscrita', 'adscrita'),
    ('firmante_el_la', 'Firmante: el / la', 'la'),
    # Testigos
    ('testigo1_nombre', 'Testigo 1: nombre', 'SAMANTHA MORALES'),
    ('testigo1_cargo', 'Testigo 1: cargo', 'AGENTE FEDERAL DE MIGRACIÓN'),
    ('testigo2_nombre', 'Testigo 2: nombre', 'JAVIER DUARTE'),
    ('testigo2_cargo', 'Testigo 2: cargo', 'AGENTE FEDERAL DE MIGRACIÓN'),
    # Persona extranjera
    ('extranjero_nombre', 'Extranjero: nombre', 'QIAO WEIBING'),
    ('extranjero_nacionalidad', 'Extranjero: nacionalidad', 'china'),
    ('extranjero_fecha_nacimiento', 'Extranjero: fecha de nacimiento', '14/04/1994'),
    ('extranjero_documento', 'Extranjero: pasaporte o documento', 'EG2830939'),
    ('extranjero_idioma', 'Extranjero: idioma', 'chino'),
    ('vuelo', 'Vuelo', 'HU7925'),
    ('fecha_arribo', 'Fecha de arribo', '17 de noviembre de 2026'),
    ('origen', 'Origen del vuelo', 'PEKÍN, CHINA'),
    ('aerolinea', 'Aerolínea', 'HAINAN AIRLINES'),
    ('sala_entrevista', 'No. de sala de entrevista', '1'),
    ('numero_acta', 'Número de acta', 'ORBC/AIMMTJ/AR000316/2026'),
    ('motivo_rechazo', 'Motivo de rechazo (oficio 11)', 'Falta de visa válida y vigente (…)'),
]
CLAVES = {clave for clave, _etiqueta, _ejemplo in VARIABLES}


# Nivel de la plaza al final del puesto: 'AGENTE FEDERAL DE MIGRACIÓN "B"', 'TÉCNICO OPERATIVO C'.
NIVEL_RE = re.compile(r'\s+["“”\']?[A-E]["“”\']?$')


def cargo_impreso(cargo):
    """El cargo como se imprime en los oficios: sin el nivel de la plaza (decisión del usuario, 25/11)."""
    return NIVEL_RE.sub('', (cargo or '').strip())


def _empleado(empleado, prefijo):
    if not empleado:
        return {f'{prefijo}_nombre': '', f'{prefijo}_cargo': ''}
    return {f'{prefijo}_nombre': empleado.nombre_para_oficio, f'{prefijo}_cargo': cargo_impreso(empleado.cargo)}


def contexto_para(instancia):
    """Todas las variables con su valor para esta instancia (cadenas; '' si falta el dato)."""
    persona = instancia.persona
    expediente = persona.expediente
    oficina = DatosOficina.actual()
    firmante = expediente.firmante
    testigo_1, testigo_2 = instancia.testigos

    contexto = {
        'ciudad': oficina.ciudad,
        'ciudad_encabezado': oficina.ciudad_encabezado,
        'fecha_larga': fecha_larga(instancia.fecha_oficio),
        'aeropuerto': oficina.aeropuerto,
        'entidad': oficina.entidad,
        'terminal': oficina.terminal,
        'domicilio': oficina.domicilio,
        'firmante_fundamento': firmante.fundamento if firmante else '',
        'firmante_adscrito': 'adscrita' if firmante and firmante.es_mujer else 'adscrito',
        'firmante_el_la': 'la' if firmante and firmante.es_mujer else 'el',
        'extranjero_nombre': persona.nombre,
        'extranjero_nacionalidad': persona.nacionalidad,
        'extranjero_fecha_nacimiento': fecha_corta(persona.fecha_nacimiento),
        'extranjero_documento': persona.documento,
        'extranjero_idioma': IDIOMA_EN_TEXTO.get(persona.idioma, ''),
        'vuelo': persona.vuelo,
        'fecha_arribo': fecha_larga(persona.fecha_arribo),
        'origen': persona.origen,
        'aerolinea': persona.aerolinea,
        'sala_entrevista': persona.sala_entrevista,
        'numero_acta': persona.numero_acta,
        'motivo_rechazo': persona.motivo_rechazo.texto if persona.motivo_rechazo_id else '',
    }
    contexto.update(_empleado(firmante, 'firmante'))
    contexto.update(_empleado(testigo_1, 'testigo1'))
    contexto.update(_empleado(testigo_2, 'testigo2'))
    return contexto
