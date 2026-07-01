"""
Match finder del buscador de palabras de la biblioteca.

Localiza las coincidencias de cada palabra buscada dentro de un texto y las
devuelve como HTML seguro con <mark>. La comparación ignora mayúsculas y
acentos para ser consistente con las collations *_ci de MySQL (icontains):
si la BD consideró que el documento coincide, aquí se resalta lo mismo.
"""
import unicodedata

from django.utils.html import escape
from django.utils.safestring import mark_safe

RADIO_SNIPPET = 90  # caracteres de contexto a cada lado de la coincidencia


def extraer_palabras(consulta):
    """Separa la consulta en palabras no vacías."""
    return [p for p in (consulta or '').split() if p]


def _normalizar(texto):
    """Minúsculas y sin acentos, preservando posición a posición (1:1)."""
    out = []
    for ch in texto:
        base = unicodedata.normalize('NFD', ch)[0].lower()
        out.append(base[0] if base else ch)
    return ''.join(out)


def _spans(texto, palabras):
    """Rangos (inicio, fin) de todas las coincidencias, fusionando solapados."""
    texto_norm = _normalizar(texto)
    spans = []
    for palabra in palabras:
        palabra_norm = _normalizar(palabra)
        if not palabra_norm:
            continue
        inicio = 0
        while (i := texto_norm.find(palabra_norm, inicio)) != -1:
            spans.append((i, i + len(palabra_norm)))
            inicio = i + 1
    if not spans:
        return []
    spans.sort()
    fusionados = [spans[0]]
    for ini, fin in spans[1:]:
        if ini <= fusionados[-1][1]:
            fusionados[-1] = (fusionados[-1][0], max(fin, fusionados[-1][1]))
        else:
            fusionados.append((ini, fin))
    return fusionados


def resaltar(texto, palabras):
    """HTML seguro del texto con las coincidencias envueltas en <mark>."""
    texto = texto or ''
    spans = _spans(texto, palabras)
    partes = []
    cursor = 0
    for ini, fin in spans:
        partes.append(escape(texto[cursor:ini]))
        partes.append('<mark>{}</mark>'.format(escape(texto[ini:fin])))
        cursor = fin
    partes.append(escape(texto[cursor:]))
    return mark_safe(''.join(partes))


def snippet(texto, palabras, radio=RADIO_SNIPPET):
    """
    Fragmento del texto alrededor de la primera coincidencia, resaltado.
    Devuelve None si ninguna palabra aparece (p.ej. el match fue en el título).
    """
    texto = texto or ''
    spans = _spans(texto, palabras)
    if not spans:
        return None
    ini, fin = spans[0]
    desde = max(0, ini - radio)
    hasta = min(len(texto), fin + radio)
    # Ajusta los cortes al límite de palabra más cercano para no partir palabras.
    if desde > 0:
        espacio = texto.find(' ', desde, ini)
        if espacio != -1:
            desde = espacio + 1
    if hasta < len(texto):
        espacio = texto.rfind(' ', fin, hasta)
        if espacio != -1:
            hasta = espacio
    prefijo = '… ' if desde > 0 else ''
    sufijo = ' …' if hasta < len(texto) else ''
    return mark_safe(prefijo + resaltar(texto[desde:hasta], palabras) + sufijo)
