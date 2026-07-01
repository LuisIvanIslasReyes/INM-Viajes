"""
Extracción de texto plano de los documentos para el buscador de palabras.

Se extrae siempre desde un PDF con pypdf (dependencia pura Python, sin binarios):
si el documento original es PDF se usa directamente; si es Word se usa el PDF de
vista previa generado por LibreOffice. Si no hay PDF disponible (conversión
fallida) o el PDF no tiene capa de texto (escaneado), se degrada con gracia y el
documento simplemente no participa en la búsqueda por contenido.
"""
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Tope defensivo para no inflar la BD con PDFs enormes.
MAX_CARACTERES = 300_000


def extraer_texto(redaccion):
    """Devuelve el texto plano del documento (str, puede ser '')."""
    if redaccion.es_pdf and redaccion.archivo:
        archivo = redaccion.archivo
    elif redaccion.archivo_pdf:
        archivo = redaccion.archivo_pdf
    else:
        return ''

    try:
        with archivo.open('rb') as fh:
            reader = PdfReader(fh)
            paginas = (page.extract_text() or '' for page in reader.pages)
            # Colapsa saltos de línea y espacios múltiples para snippets legibles.
            texto = ' '.join(' '.join(paginas).split())
        return texto[:MAX_CARACTERES]
    except Exception as exc:
        logger.warning('No se pudo extraer texto de la redacción %s: %s', redaccion.pk, exc)
        return ''


def actualizar_texto(redaccion):
    """Extrae y persiste el texto del documento. Devuelve True si quedó texto."""
    redaccion.texto_contenido = extraer_texto(redaccion)
    redaccion.save(update_fields=['texto_contenido'])
    return bool(redaccion.texto_contenido)
