"""
.docx → PDF con LibreOffice (el mismo `SOFFICE_BIN` que usa la vista previa de Redacciones).

Si LibreOffice no está o falla, devuelve None y la interfaz ofrece solo el Word.
"""
import os
import shutil
import tempfile

from apps.redacciones.utils.conversion import convertir_a_pdf


def docx_a_pdf(docx_bytes, nombre='oficio'):
    """Bytes del PDF, o None si no se pudo convertir."""
    carpeta = tempfile.mkdtemp(prefix='oficio_docx_')
    try:
        ruta_docx = os.path.join(carpeta, f'{nombre}.docx')
        with open(ruta_docx, 'wb') as fh:
            fh.write(docx_bytes)
        ruta_pdf = convertir_a_pdf(ruta_docx)
        if not ruta_pdf:
            return None
        try:
            with open(ruta_pdf, 'rb') as fh:
                return fh.read()
        finally:
            shutil.rmtree(os.path.dirname(ruta_pdf), ignore_errors=True)
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
