"""
Arma el .docx de uno o varios oficios (una sección por oficio).

Lo fijo lo pone el código: hoja membretada de fondo, bloque institucional, título,
"Ciudad, fecha." y la tabla de firmas. Lo editable es el cuerpo (HTML del editor,
con las variables ya sustituidas), que escribe `html_docx.EscritorHTML`.

El PDF sale de convertir este mismo .docx con LibreOffice (services/pdf.py): un solo
renderizador, para que el Word y el PDF no puedan diferir.

Medidas tomadas de los Word oficiales de la USB: carta, cuerpo a 10 pt, márgenes
laterales de 1.59 cm. El superior (3.4 cm) y el inferior (4 cm) dejan libres la bandera y el
arte del pie de la hoja membretada ("2026 Margarita Maza").
"""
import io
from dataclasses import dataclass, field

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Emu, Pt

from ..models import HojaMembretada, PlantillaOficio
from . import evidencias
from .contexto import contexto_para
from .html_docx import EscritorHTML, borde_superior
from .variables import sustituir

FUENTE = 'Noto Sans'
# Noto Sans no trae chino ni árabe. Word y LibreOffice usan estas para esos caracteres;
# las dos vienen con Windows (si faltan, LibreOffice toma otra que los tenga).
FUENTE_ASIA = 'Microsoft YaHei'
FUENTE_COMPLEJA = 'Arial'  # árabe (escritura de derecha a izquierda)
CUERPO_PT = 10
INTERLINEADO = 1.0   # sencillo, como los Word oficiales (Noto Sans a 10 pt ≈ 13.6 pt por renglón)
PAGINA_CM = (21.59, 27.94)
MARGENES_CM = {'top': 3.4, 'bottom': 4.0, 'left': 1.59, 'right': 1.59}
# Posición y tamaño de la hoja membretada tal como la ancla el Word oficial (header2.xml
# del 02): un poco más chica que la página y subida ~0.45 cm. Así la bandera de arriba a
# la derecha no choca con el bloque institucional. En EMU (1 cm = 360 000).
MEMBRETE_EMU = {'x': 47625, 'y': -161925, 'ancho': 7769860, 'alto': 9886950}
SANGRIA_LINEA_FIRMA_CM = 0.9  # la línea de firma mide el ancho de la columna menos esto por lado
ESPACIO_RUBRICA_PT = 18     # hueco para la rúbrica sobre la línea
ESPACIO_ENTRE_FIRMAS_PT = 4
ESPACIO_ANTES_FIRMAS_PT = 10
ESPACIO_BLOQUES_PT = 8      # después del bloque institucional, del título y de la fecha

Bloque = PlantillaOficio.BloqueFirmas


@dataclass
class Pieza:
    """Lo necesario para imprimir un oficio (ya con las variables sustituidas en el cuerpo)."""

    titulo: str
    cuerpo_html: str
    bloque_firmas: str
    lleva_fecha: bool
    contexto: dict = field(default_factory=dict)
    tamano_pt: float = CUERPO_PT
    leyenda_persona: str = ''  # bajo la firma de la persona (traducciones): 'NOMBRE Y FIRMA / 姓名和签名'
    tipo_evidencias: str = ''  # '' | VERIFICACION | FOTO (services/evidencias.py)
    evidencias: list = field(default_factory=list)


def formato_de(plantilla, variante=None):
    """Lo que no es texto pero sí se imprime (se congela al imprimir). Con traducción, su título y leyenda."""
    return {
        'titulo': (variante.titulo if variante and variante.titulo else plantilla.titulo),
        'bloque_firmas': plantilla.bloque_firmas,
        'lleva_fecha': plantilla.lleva_fecha,
        'tamano_letra_pt': float(plantilla.tamano_letra_pt),
        'leyenda_persona': variante.leyenda_firma_persona if variante else '',
    }


def formato_de_instancia(instancia):
    plantilla = instancia.plantilla
    formato = formato_de(plantilla, plantilla.variante(instancia.idioma))
    if plantilla.evidencias:
        formato['tipo_evidencias'] = plantilla.evidencias
        formato['evidencias'] = evidencias.datos(instancia.persona, plantilla)
    return formato


def pieza_de(instancia, contexto=None):
    """La pieza de una instancia: con lo congelado si ya se imprimió, si no con los datos actuales."""
    if contexto is None:
        contexto = instancia.snap_contexto if instancia.snap_contexto else contexto_para(instancia)
    cuerpo, _desconocidas = sustituir(instancia.contenido_html, contexto)
    if instancia.snap_formato:
        # Lo congelado manda; lo que no se congelaba antes (versiones viejas) sale de la plantilla.
        formato = {**formato_de(instancia.plantilla), **instancia.snap_formato}
    else:
        formato = formato_de_instancia(instancia)
    return Pieza(
        titulo=formato['titulo'],
        cuerpo_html=cuerpo,
        bloque_firmas=formato['bloque_firmas'],
        lleva_fecha=formato['lleva_fecha'],
        contexto=contexto,
        tamano_pt=formato.get('tamano_letra_pt', CUERPO_PT),
        leyenda_persona=formato.get('leyenda_persona', ''),
        tipo_evidencias=formato.get('tipo_evidencias', ''),
        evidencias=formato.get('evidencias', []),
    )


def render_docx(piezas):
    """Bytes del .docx con una sección (página nueva) por pieza."""
    document = Document()
    _estilo_base(document)
    for i, pieza in enumerate(piezas):
        section = document.sections[0] if i == 0 else document.add_section(WD_SECTION.NEW_PAGE)
        _geometria(section)
        if i == 0:
            _hoja_membretada(section)  # las secciones siguientes heredan el encabezado
        ancho_util = section.page_width - section.left_margin - section.right_margin
        # python-docx inserta cada párrafo ANTES del <w:sectPr> final del cuerpo: lo de este
        # oficio empieza en la posición que hoy ocupa ese sectPr.
        inicio = len(document.element.body) - 1
        _encabezado_institucional(document, pieza.contexto)
        _titulo(document, pieza.titulo)
        if pieza.lleva_fecha:
            _fecha(document, pieza.contexto)
        EscritorHTML(
            document, ancho_util, tamano_pt=pieza.tamano_pt,
            al_nueva_hoja=lambda c=pieza.contexto: _encabezado_institucional(document, c, nueva_hoja=True),
            al_evidencias=lambda p=pieza, a=ancho_util: evidencias.dibujar(
                document, p.evidencias, p.tipo_evidencias, a),
        ).escribir(pieza.cuerpo_html)
        _firmas(document, pieza, ancho_util)
        _aplicar_tamano(document.element.body[inicio:], pieza.tamano_pt)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------- documento

def _aplicar_tamano(elementos, pt):
    """Tamaño de letra de un oficio (cada plantilla tiene el de su Word oficial: 9 a 10 pt).

    Se pone en cada run y no en el estilo Normal porque un paquete mezcla oficios con
    tamaños distintos. Lo que ya trae tamaño propio se respeta.
    """
    tamano = Pt(pt)
    for elemento in elementos:
        for run in elemento.iter(qn('w:r')):
            rpr = run.get_or_add_rPr()
            if rpr.sz_val is None:
                rpr.sz_val = tamano
            if rpr.find(qn('w:szCs')) is None:  # tamaño del árabe (escritura compleja)
                rpr.find(qn('w:sz')).addnext(parse_xml(f'<w:szCs {nsdecls("w")} w:val="{int(pt * 2)}"/>'))


def _estilo_base(document):
    normal = document.styles['Normal']
    normal.font.name = FUENTE
    normal.font.size = Pt(CUERPO_PT)
    rfonts = normal.element.get_or_add_rPr().get_or_add_rFonts()
    for atributo in ('w:ascii', 'w:hAnsi'):
        rfonts.set(qn(atributo), FUENTE)
    rfonts.set(qn('w:eastAsia'), FUENTE_ASIA)
    rfonts.set(qn('w:cs'), FUENTE_COMPLEJA)
    formato = normal.paragraph_format
    formato.space_before = Pt(0)
    formato.space_after = Pt(0)
    formato.line_spacing = INTERLINEADO


def _geometria(section):
    section.page_width, section.page_height = Cm(PAGINA_CM[0]), Cm(PAGINA_CM[1])
    section.top_margin = Cm(MARGENES_CM['top'])
    section.bottom_margin = Cm(MARGENES_CM['bottom'])
    section.left_margin = Cm(MARGENES_CM['left'])
    section.right_margin = Cm(MARGENES_CM['right'])
    section.header_distance = Cm(0.5)
    section.footer_distance = Cm(0.5)


def _hoja_membretada(section):
    ruta = HojaMembretada.ruta_actual()
    if not ruta or not ruta.exists():
        return
    with open(ruta, 'rb') as fh:
        _anclar_a_la_pagina(section.header.paragraphs[0], io.BytesIO(fh.read()), **MEMBRETE_EMU)


def _anclar_a_la_pagina(parrafo, stream, x, y, ancho, alto):
    """Imagen de página completa, detrás del texto, en el encabezado (se repite en cada hoja).

    python-docx solo inserta imágenes en línea; se inserta así y luego el `<wp:inline>` se
    cambia por un `<wp:anchor behindDoc="1">` contra la página. Mismo truco que
    `_anclar_a_la_pagina` en ProyectoEstancia/backend/apps/Oficios/services/docx_renderer.py.
    """
    inline = parrafo.add_run().add_picture(stream, width=Emu(ancho), height=Emu(alto))._inline
    anchor = parse_xml(
        f'<wp:anchor {nsdecls("wp")} distT="0" distB="0" distL="0" distR="0" '
        'simplePos="0" relativeHeight="0" behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="page"><wp:posOffset>{int(x)}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="page"><wp:posOffset>{int(y)}</wp:posOffset></wp:positionV>'
        '</wp:anchor>'
    )
    # El esquema OOXML fija el orden: extent, effectExtent, wrap, docPr, cNvGraphicFramePr, graphic.
    for etiqueta in ('wp:extent', 'wp:effectExtent'):
        nodo = inline.find(qn(etiqueta))
        if nodo is not None:
            anchor.append(nodo)
    anchor.append(parse_xml(f'<wp:wrapNone {nsdecls("wp")}/>'))
    for etiqueta in ('wp:docPr', 'wp:cNvGraphicFramePr', 'a:graphic'):
        nodo = inline.find(qn(etiqueta))
        if nodo is not None:
            anchor.append(nodo)
    inline.getparent().replace(inline, anchor)


# ---------------------------------------------------------------- partes fijas

def _encabezado_institucional(document, contexto, nueva_hoja=False):
    """Las 5 líneas de la oficina. Con `nueva_hoja` empieza otra hoja ([[ NUEVA HOJA ]] del 13)."""
    lineas = [
        'SECRETARÍA DE GOBERNACIÓN',
        'INSTITUTO NACIONAL DE MIGRACIÓN',
        f'OFICINA DE REPRESENTACIÓN EN {contexto.get("entidad", "")}'.strip(),
        contexto.get('aeropuerto', ''),
        contexto.get('terminal', ''),
    ]
    lineas = [linea for linea in lineas if linea]
    for i, linea in enumerate(lineas):
        parrafo = document.add_paragraph()
        if nueva_hoja and i == 0:
            parrafo.paragraph_format.page_break_before = True
        parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        parrafo.paragraph_format.line_spacing = 1.0
        parrafo.add_run(linea).bold = True
    document.paragraphs[-1].paragraph_format.space_after = Pt(ESPACIO_BLOQUES_PT + 3)


def _titulo(document, titulo):
    parrafo = document.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    parrafo.paragraph_format.space_after = Pt(ESPACIO_BLOQUES_PT)
    parrafo.add_run(titulo).bold = True


def _fecha(document, contexto):
    parrafo = document.add_paragraph()
    parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    parrafo.paragraph_format.space_after = Pt(ESPACIO_BLOQUES_PT)
    ciudad = contexto.get('ciudad_encabezado', '')
    fecha = contexto.get('fecha_larga', '')
    parrafo.add_run(f'{ciudad}, {fecha}.' if ciudad else f'{fecha}.').bold = True


# ---------------------------------------------------------------- firmas

def _firmas(document, pieza, ancho_util):
    c = pieza.contexto
    if pieza.bloque_firmas == Bloque.CONSTANCIA:
        celdas = [
            [('LA AUTORIDAD MIGRATORIA', c.get('firmante_nombre', ''), c.get('firmante_cargo', '')),
             ('LA PERSONA EXTRANJERA', c.get('extranjero_nombre', ''), pieza.leyenda_persona)],
            [('TESTIGO DE ASISTENCIA', c.get('testigo1_nombre', ''), c.get('testigo1_cargo', '')),
             ('TESTIGO DE ASISTENCIA', c.get('testigo2_nombre', ''), c.get('testigo2_cargo', ''))],
        ]
    elif pieza.bloque_firmas == Bloque.NOTIFICACION:
        celdas = [[
            ('ATENTAMENTE.', c.get('firmante_nombre', ''), c.get('firmante_cargo', '')),
            # La persona firma sobre una línea a lo ancho de la columna, con la leyenda debajo.
            ('', 'Recibí original de la presente notificación.', '', False),
        ]]
    elif pieza.bloque_firmas == Bloque.AUTORIDAD_PERSONA:
        celdas = [[
            ('LA AUTORIDAD MIGRATORIA', c.get('firmante_nombre', ''), c.get('firmante_cargo', '')),
            ('LA PERSONA EXTRANJERA', c.get('extranjero_nombre', ''), pieza.leyenda_persona),
        ]]
    elif pieza.bloque_firmas == Bloque.ACUERDO:
        # Fila de en medio: una sola celda (combinada) con el representante de la aerolínea.
        celdas = [
            [('LA AUTORIDAD MIGRATORIA', c.get('firmante_nombre', ''), c.get('firmante_cargo', '')),
             ('LA PERSONA EXTRANJERA', c.get('extranjero_nombre', ''), pieza.leyenda_persona)],
            [('', 'NOMBRE Y FIRMA DEL REPRESENTANTE DE LA AEROLÍNEA', '', False)],
            [('TESTIGO DE ASISTENCIA', c.get('testigo1_nombre', ''), c.get('testigo1_cargo', '')),
             ('TESTIGO DE ASISTENCIA', c.get('testigo2_nombre', ''), c.get('testigo2_cargo', ''))],
        ]
    elif pieza.bloque_firmas == Bloque.EMPRESA:
        celdas = [[
            ('', 'NOMBRE Y FIRMA DEL REPRESENTANTE DE LA EMPRESA TRANSPORTISTA', ''),
            ('LA AUTORIDAD MIGRATORIA', c.get('firmante_nombre', ''), c.get('firmante_cargo', '')),
        ]]
    else:
        return

    # Sin párrafo vacío antes de la tabla (ocupa un renglón entero): el aire va en la primera fila.
    tabla = document.add_table(rows=len(celdas), cols=2)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.autofit = False
    ancho_columna = int(ancho_util / 2)
    for i, (fila, datos_fila) in enumerate(zip(tabla.rows, celdas)):
        # Una fila de firmas nunca se parte entre dos hojas: si no cabe, pasa completa.
        fila._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        fila.cells[0].width = fila.cells[1].width = ancho_columna
        celdas_fila = fila.cells
        if len(datos_fila) == 1:  # una sola firma centrada a todo lo ancho
            celdas_fila = [fila.cells[0].merge(fila.cells[1])]
        for celda, datos in zip(celdas_fila, datos_fila):
            _celda_firma(celda, *datos, antes=ESPACIO_ANTES_FIRMAS_PT if i == 0 else 0)


def _celda_firma(celda, rol, nombre, cargo, linea_angosta=True, antes=0):
    """Rol, hueco para la rúbrica, línea de firma, nombre y cargo.

    La línea es el borde superior del párrafo del nombre (no un renglón de guiones
    bajos): ahorra un renglón por fila, lo que hace caber constancias largas como el 07.
    El renglón del rol va aunque esté vacío, para que las líneas de las dos columnas
    queden a la misma altura.
    """
    parrafos = [(rol, antes, False), (nombre, ESPACIO_RUBRICA_PT, True)]
    if cargo:
        parrafos.append((cargo, 0, False))
    for i, (texto, espacio_antes, linea) in enumerate(parrafos):
        parrafo = celda.paragraphs[0] if i == 0 else celda.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        formato = parrafo.paragraph_format
        formato.line_spacing = 1.0
        if espacio_antes:
            formato.space_before = Pt(espacio_antes)
        if linea:
            if linea_angosta:
                formato.left_indent = formato.right_indent = Cm(SANGRIA_LINEA_FIRMA_CM)
            borde_superior(parrafo)
        if texto:
            parrafo.add_run(texto).bold = True
    celda.paragraphs[-1].paragraph_format.space_after = Pt(ESPACIO_ENTRE_FIRMAS_PT)
