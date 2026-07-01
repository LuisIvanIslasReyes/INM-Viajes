"""
Conversión de documentos Word a PDF para la vista previa, usando LibreOffice
headless (`soffice --headless --convert-to pdf`).

En Windows Server 2019 (offline): instalar LibreOffice desde el .msi transferido y
configurar la ruta del binario en settings, p.ej.:

    SOFFICE_BIN = r"C:\\Program Files\\LibreOffice\\program\\soffice.exe"

Si la conversión no está disponible o falla (binario ausente, timeout, error),
se degrada con gracia: no se genera la vista previa y la interfaz ofrece solo la
descarga del documento original.
"""
import logging
import os
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.core.files import File

logger = logging.getLogger(__name__)

TIMEOUT_SEG = 60


def _soffice_bin():
    return getattr(settings, 'SOFFICE_BIN', 'soffice')


def _convertir_a_pdf(ruta_origen):
    """
    Convierte el documento en `ruta_origen` a PDF con LibreOffice headless.
    Devuelve la ruta del PDF generado (en un directorio temporal) o None si falla.
    """
    outdir = tempfile.mkdtemp(prefix='redaccion_pdf_')
    try:
        subprocess.run(
            [_soffice_bin(), '--headless', '--convert-to', 'pdf',
             '--outdir', outdir, ruta_origen],
            check=True, timeout=TIMEOUT_SEG,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
        logger.warning('Conversión a PDF fallida para %s: %s', ruta_origen, exc)
        shutil.rmtree(outdir, ignore_errors=True)
        return None

    base = os.path.splitext(os.path.basename(ruta_origen))[0]
    pdf_path = os.path.join(outdir, base + '.pdf')
    if not os.path.exists(pdf_path):
        logger.warning('LibreOffice no generó PDF para %s', ruta_origen)
        shutil.rmtree(outdir, ignore_errors=True)
        return None
    return pdf_path


def generar_preview(redaccion):
    """
    Genera y guarda el PDF de vista previa para una Redacción de tipo Word.
    Devuelve True si se generó, False si se degrada a solo-descarga.
    No lanza excepciones: cualquier fallo se registra y devuelve False.
    """
    if redaccion.es_pdf or not redaccion.archivo:
        return False

    pdf_path = _convertir_a_pdf(redaccion.archivo.path)
    if not pdf_path:
        return False

    try:
        nombre = os.path.splitext(os.path.basename(redaccion.archivo.name))[0] + '.pdf'
        with open(pdf_path, 'rb') as fh:
            redaccion.archivo_pdf.save(nombre, File(fh), save=True)
        return True
    except OSError as exc:
        logger.warning('No se pudo guardar el PDF de vista previa: %s', exc)
        return False
    finally:
        shutil.rmtree(os.path.dirname(pdf_path), ignore_errors=True)
