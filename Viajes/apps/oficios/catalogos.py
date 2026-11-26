"""
Catálogos pequeños para precargar datos del vuelo en la persona (siempre editables).

- Aerolínea por el prefijo IATA del vuelo: 'HU7925' → 'HAINAN AIRLINES'.
- Origen por el aeropuerto de salida del Excel: 'PEK' → 'PEKÍN, CHINA'.

Si el código no está, la aerolínea queda vacía y el origen queda con el código.
"""
import re

AEROLINEAS = {
    'HU': 'HAINAN AIRLINES', 'CA': 'AIR CHINA', 'MU': 'CHINA EASTERN AIRLINES',
    'CZ': 'CHINA SOUTHERN AIRLINES', '3U': 'SICHUAN AIRLINES', 'HO': 'JUNEYAO AIRLINES',
    'AM': 'AEROMÉXICO', 'Y4': 'VOLARIS', 'VB': 'VIVA AEROBUS',
}

AEROPUERTOS = {
    'PEK': 'PEKÍN, CHINA', 'PKX': 'PEKÍN, CHINA', 'PVG': 'SHANGHÁI, CHINA', 'SHA': 'SHANGHÁI, CHINA',
    'CAN': 'CANTÓN, CHINA', 'SZX': 'SHENZHEN, CHINA', 'CTU': 'CHENGDÚ, CHINA', 'TFU': 'CHENGDÚ, CHINA',
    'HKG': 'HONG KONG, CHINA', 'MEX': 'CIUDAD DE MÉXICO, MÉXICO', 'NLU': 'CIUDAD DE MÉXICO, MÉXICO',
    'TIJ': 'TIJUANA, MÉXICO', 'GDL': 'GUADALAJARA, MÉXICO', 'MTY': 'MONTERREY, MÉXICO',
}

_PREFIJO_RE = re.compile(r'^\s*([A-Z0-9]{2})\s*\d')


def aerolinea_de_vuelo(vuelo):
    """'HU7925' → 'HAINAN AIRLINES'; '' si no se reconoce."""
    prefijo = _PREFIJO_RE.match((vuelo or '').upper())
    return AEROLINEAS.get(prefijo.group(1), '') if prefijo else ''


def origen_de_aeropuerto(codigo):
    codigo = (codigo or '').strip().upper()
    return AEROPUERTOS.get(codigo, codigo)
