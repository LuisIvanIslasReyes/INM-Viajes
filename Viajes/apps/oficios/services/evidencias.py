"""
Evidencias de la persona en el oficio (09: verificación de información; 05: condición médica).

Sugerencia del usuario (25/11): el extranjero presenta de 1 a N evidencias y cada una lleva su
espacio. Donde el texto dice `[[ EVIDENCIAS ]]` va un bloque con borde por evidencia:

  - VERIFICACION (09): a quién se verificó, hora, ¿respuesta?, intentos, observaciones y foto.
  - FOTO (05): observaciones y foto.

Cada bloque es una fila que no se parte entre hojas; la foto se ajusta al ancho y a un alto
máximo sin deformarse. Sin evidencias sale un bloque en blanco (para llenar a mano, como hoy).
Al imprimir se congelan los datos (`snap_formato['evidencias']`); las fotos quedan dentro del .docx.
"""
import io
import logging

from django.core.files.storage import default_storage
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.shared import Cm, Emu, Pt
from PIL import Image, ImageOps, UnidentifiedImageError

from ..models import PlantillaOficio
from .html_docx import MARGENES_CELDA, TAB_CON_RELLENO

logger = logging.getLogger(__name__)

Tipo = PlantillaOficio.TipoEvidencia
# Alto máximo de la foto: en el 09 la captura del teléfono se lee mejor grande; en el 05 una
# evidencia con su foto deja que la constancia quepa en una hoja, como el Word oficial.
ALTO_MAXIMO_FOTO_CM = {Tipo.VERIFICACION: 7.0, Tipo.FOTO: 5.0}
LADO_MAXIMO_PX = 1400          # la foto se reduce antes de meterla al .docx
RENGLONES_SIN_FOTO = 5         # alto del espacio en blanco cuando no hay foto
CASILLA = {True: '☒', False: '☐'}


def datos(persona, plantilla):
    """Lo que se imprime de cada evidencia (y se congela al imprimir)."""
    return [
        {
            'verificacion_a': e.verificacion_a, 'hora': e.hora, 'respuesta': e.respuesta,
            'intentos': e.intentos, 'nota': e.nota, 'foto': e.foto.name if e.foto else '',
        }
        for e in persona.evidencias.filter(plantilla=plantilla)
    ]


def imagen_para_docx(nombre):
    """(BytesIO JPEG, ancho px, alto px) de la foto guardada, girada según EXIF y reducida; None si no se puede."""
    if not nombre:
        return None
    try:
        with default_storage.open(nombre, 'rb') as fh:
            imagen = ImageOps.exif_transpose(Image.open(fh))
            imagen = imagen.convert('RGB')
            imagen.thumbnail((LADO_MAXIMO_PX, LADO_MAXIMO_PX))
            salida = io.BytesIO()
            imagen.save(salida, format='JPEG', quality=85)
    except (FileNotFoundError, OSError, UnidentifiedImageError) as e:
        logger.warning('No se pudo leer la foto de evidencia %s: %s', nombre, e)
        return None
    salida.seek(0)
    return salida, imagen.width, imagen.height


def dibujar(document, evidencias, tipo, ancho_util):
    """Un bloque con borde por evidencia (o uno en blanco si no hay)."""
    lista = evidencias or [None]
    for numero, evidencia in enumerate(lista, start=1):
        tabla = document.add_table(rows=1, cols=1)
        tabla.style = 'Table Grid'
        fila = tabla.rows[0]
        fila._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        celda = fila.cells[0]
        celda.width = ancho_util
        ancho = Emu(int(ancho_util) - int(MARGENES_CELDA))
        _bloque(celda, evidencia, tipo, ancho, numero if len(lista) > 1 else None)
        espacio = document.add_paragraph()
        espacio.paragraph_format.space_after = Pt(2)


def _bloque(celda, evidencia, tipo, ancho, numero):
    e = evidencia or {}
    parrafos = []

    def parrafo(*tramos, alineacion=None):
        p = celda.paragraphs[0] if not parrafos else celda.add_paragraph()
        parrafos.append(p)
        if alineacion is not None:
            p.alignment = alineacion
        for texto, negritas in tramos:
            if texto:
                p.add_run(texto).bold = negritas
        return p

    if numero:
        parrafo((f'Evidencia {numero}', True))
    if tipo == Tipo.VERIFICACION:
        parrafo(('Verificación realizada a: ', True), (e.get('verificacion_a') or '', False))
        if not e.get('verificacion_a'):
            _linea(parrafos[-1], ancho)
        respuesta = e.get('respuesta') or ''
        intentos = e.get('intentos')
        parrafo(
            ('Hora: ', True), (e.get('hora') or '________', False),
            ('      ¿Se recibió respuesta?  Sí: ', True), (CASILLA[respuesta == 'SI'], False),
            ('   No: ', True), (CASILLA[respuesta == 'NO'], False),
            ('      Número de intentos: ', True), (str(intentos) if intentos is not None else '______', False),
        )
    parrafo(('Observaciones: ', True), (e.get('nota') or '', False))
    if not e.get('nota'):
        _linea(parrafos[-1], ancho)
        _linea(parrafo(), ancho)

    titulo = 'Evidencia documental:' if tipo == Tipo.VERIFICACION else 'Evidencia fotográfica:'
    parrafo((titulo, True))
    imagen = imagen_para_docx(e.get('foto'))
    if imagen:
        stream, ancho_px, alto_px = imagen
        alto_max = Cm(ALTO_MAXIMO_FOTO_CM.get(tipo, 7.0))
        # Al ancho disponible, sin pasar del alto máximo y sin deformar.
        ancho_emu = min(int(ancho), int(alto_max * ancho_px / alto_px))
        alto_emu = int(ancho_emu * alto_px / ancho_px)
        foto = parrafo(alineacion=WD_ALIGN_PARAGRAPH.CENTER)
        foto.add_run().add_picture(stream, width=Emu(ancho_emu), height=Emu(alto_emu))
    else:
        for _ in range(RENGLONES_SIN_FOTO):
            parrafo()
        leyenda = ('(Fotografía del registro de llamadas dentro del teléfono de oficina o de información '
                   'obtenida en páginas de internet)') if tipo == Tipo.VERIFICACION else '(Fotografía)'
        nota = parrafo(alineacion=WD_ALIGN_PARAGRAPH.CENTER)
        nota.add_run(leyenda).italic = True


def _linea(parrafo, ancho):
    """Completa el renglón con una línea para escribir a mano."""
    parrafo.paragraph_format.tab_stops.add_tab_stop(ancho, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.LINES)
    parrafo.add_run(TAB_CON_RELLENO)
