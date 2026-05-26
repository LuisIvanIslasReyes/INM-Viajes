"""
Utilidad para cargar el catálogo de países desde context/paises.json.
La lista se cachea en memoria con lru_cache para evitar leer el archivo
en cada request.
"""
import json
from functools import lru_cache
from django.conf import settings


@lru_cache(maxsize=1)
def get_paises():
    """Devuelve la lista de países como lista de dicts:
    [{'nombre': 'CHINA', 'codigo': 'CHN', 'nacionalidad': 'China', 'nacionalidad_m': 'Chino'}, ...]
    """
    ruta = settings.BASE_DIR.parent / 'context' / 'paises.json'
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)
