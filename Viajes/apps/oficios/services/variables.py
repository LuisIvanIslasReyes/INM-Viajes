"""
Sustitución de `{{variables}}` en el HTML de un oficio.

Mismo formato que la Estancia (`_sustituir_variables` de Oficios/services/pdf_renderer.py):
`{{nombre}}`, con espacios opcionales dentro de las llaves. Una variable desconocida
se queda literal, para que se vea en la vista previa y no se imprima en silencio vacía.
"""
import re
from html import escape

VARIABLE_RE = re.compile(r'\{\{\s*([a-z0-9_]+)\s*\}\}')


def variables_usadas(html):
    """Nombres de variables que aparecen en el texto, en orden y sin repetir."""
    return list(dict.fromkeys(VARIABLE_RE.findall(html or '')))


def sustituir(html, contexto):
    """Devuelve (html con valores, desconocidas). Los valores se escapan como HTML."""
    desconocidas = []

    def reemplazo(match):
        nombre = match.group(1)
        if nombre not in contexto:
            desconocidas.append(nombre)
            return match.group(0)
        valor = contexto[nombre]
        return escape('' if valor is None else str(valor))

    return VARIABLE_RE.sub(reemplazo, html or ''), list(dict.fromkeys(desconocidas))
