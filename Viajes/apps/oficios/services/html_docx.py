"""
HTML del editor (Quill) → párrafos de python-docx.

No es un conversor genérico: cubre lo que produce la barra del editor
(p, br, strong/b, em/i, u, s, listas, sangrías y alineación con clases `ql-*`).

Convenciones del texto (decisión del usuario: los guiones NO se calculan):

  - Un párrafo cuyo texto es solo `[[ HACE CONSTAR ]]` es un **separador**: el título
    centrado, en negritas, con guiones a los dos lados hasta los márgenes.
  - `[[ ]]` (vacío) es una línea completa de guiones.
  - Un párrafo que termina en ` --` se **rellena** con guiones hasta el margen.
  - Un párrafo que termina en ` __` se completa con una línea para escribir a mano.
  - `[[ A | B ]]` es un separador con varios títulos (ej. `[[ CONSTE | SE CIERRA … ]]`).
  - `[[ RENGLÓN ]]` es un renglón completo para escribir a mano.
  - Los párrafos entre `[[ RECUADRO ]]` y `[[ /RECUADRO ]]` van dentro de un recuadro con
    borde (ej. el motivo de rechazo del 11); entre `[[ TABLA ]]` y `[[ /TABLA ]]`, cada
    párrafo es una fila con borde (ej. los datos del 09).
  - `[[ FIRMA: leyenda ]]` es una línea de firma con la leyenda debajo (ej. el acuse del 13).
  - `[[ NUEVA HOJA ]]` empieza otra hoja con el encabezado institucional (ej. el 13).
  - En una `[[ TABLA ]]`, ` || ` separa celdas de la misma fila (ej. "Fecha … || Nacionalidad …").
  - `[[ FIRMA: A || B ]]` son dos firmas lado a lado.
  - `[[ EVIDENCIAS ]]` es donde van las evidencias de la persona (09 y 05).
  - Lo que va entre `«…»` EN MAYÚSCULAS se tiene que llenar en la app: no deja imprimir (ver `pendientes`).

Los guiones los dibuja Word/LibreOffice con tabuladores con relleno (`leader="hyphen"`),
así que se ajustan solos al ancho de la página, la impresora y la fuente.

`limpiar_html` deja solo las etiquetas y atributos de esa lista; se aplica al guardar
y antes de convertir.
"""
import re
from html import escape

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Cm, Emu, Pt
from lxml import html as lxml_html

SEPARADOR_RE = re.compile(r'\[\[(.*?)\]\]', re.S)
INICIO_BLOQUE_RE = re.compile(r'\[\[\s*(RECUADRO|TABLA)\s*\]\]', re.I)
FIN_BLOQUE_RE = re.compile(r'\[\[\s*/\s*(RECUADRO|TABLA)\s*\]\]', re.I)
FIRMA_RE = re.compile(r'\[\[\s*FIRMA\s*:\s*(.*?)\s*\]\]', re.I | re.S)
RENGLON_RE = re.compile(r'\[\[\s*RENGL[OÓ]N\s*\]\]', re.I)
NUEVA_HOJA_RE = re.compile(r'\[\[\s*NUEVA\s+HOJA\s*\]\]', re.I)
POR_LLENAR_RE = re.compile(r'«([^»]*)»')
ESPACIO_FIRMA_PT = 26          # hueco para la rúbrica de una [[ FIRMA: … ]]
SANGRIA_FIRMA_CM = 5.0         # la línea de una [[ FIRMA: … ]] deja esto libre de cada lado…
LINEA_FIRMA_MINIMA_CM = 7.0    # …pero la línea mide al menos esto (ej. las dos firmas lado a lado del 03)
# LibreOffice no dibuja el relleno de un tabulador que cierra el párrafo dentro de una celda;
# con un espacio de ancho cero después sí (en Word no se nota).
TAB_CON_RELLENO = '\t\u200b'
MARGENES_CELDA = Cm(0.38)  # márgenes izquierdo + derecho por defecto de una celda de Word
RELLENO_RE = re.compile(r'(^|\s)(--|__)\s*$')  # ' --' guiones; ' __' línea para escribir
ESPACIOS_RE = re.compile(r'[ \t\r\n]+')
# Árabe (y escrituras afines de derecha a izquierda): tramos de letras árabes, incluidos los
# espacios y signos entre palabras árabes, para marcarlos como RTL en Word.
_AR = '\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF'
ARABE_RE = re.compile(f'[{_AR}]+(?:[\\s\u060C\u061B\u061F.,:;!?()«»"-]*[{_AR}]+)*')
LETRA_ARABE_RE = re.compile(f'[{_AR}]')

ETIQUETAS_BLOQUE = {'p', 'div', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
ETIQUETAS_LISTA = {'ol', 'ul'}
MARCAS = {
    'strong': 'bold', 'b': 'bold',
    'em': 'italic', 'i': 'italic',
    'u': 'underline',
    's': 'strike', 'strike': 'strike', 'del': 'strike',
    'sup': 'superscript',
}
PERMITIDAS = ETIQUETAS_BLOQUE | ETIQUETAS_LISTA | set(MARCAS) | {'li', 'br', 'span'}
SE_BORRAN_CON_CONTENIDO = {'script', 'style', 'iframe', 'object', 'embed', 'head', 'title', 'meta', 'link'}

ALINEACION = {
    'ql-align-center': WD_ALIGN_PARAGRAPH.CENTER,
    'ql-align-right': WD_ALIGN_PARAGRAPH.RIGHT,
    'ql-align-justify': WD_ALIGN_PARAGRAPH.JUSTIFY,
}
SANGRIA_CM = 1.27
# Texto chico del editor (clase ql-size-small): 1.5 pt menos que el cuerpo (ej. la traducción a
# 8 pt con el español a 9.5 pt, como en los Word oficiales; las notas al pie del 03).
TAMANO_CHICO_PT = 8           # si no se sabe el tamaño del cuerpo
DIFERENCIA_CHICO_PT = 1.5
CELDA_RE = re.compile(r'\s*\|\|\s*')     # separador de celdas en una fila de [[ TABLA ]]
EVIDENCIAS_RE = re.compile(r'\[\[\s*EVIDENCIAS\s*\]\]', re.I)


def _raiz(html):
    return lxml_html.fragment_fromstring(html or '', create_parent='div')


def limpiar_html(html):
    """Deja solo el subconjunto que sabe imprimir el conversor (y nada ejecutable)."""
    raiz = _raiz(html)
    for el in list(raiz.iterdescendants()):
        if not isinstance(el.tag, str):  # comentarios, instrucciones
            el.drop_tree()
            continue
        etiqueta = el.tag.lower()
        if etiqueta in SE_BORRAN_CON_CONTENIDO:
            el.drop_tree()
            continue
        if etiqueta not in PERMITIDAS:
            el.drop_tag()
            continue
        for atributo in list(el.attrib):
            if atributo == 'class':
                clases = [c for c in el.attrib['class'].split() if c.startswith('ql-')]
                if clases:
                    el.attrib['class'] = ' '.join(clases)
                else:
                    del el.attrib['class']
            elif not (atributo == 'data-list' and etiqueta == 'li'):
                del el.attrib[atributo]
    partes = [escape(raiz.text)] if raiz.text else []
    partes += [lxml_html.tostring(hijo, encoding='unicode') for hijo in raiz]
    return ''.join(partes)


def pendientes(html):
    """Campos «EN MAYÚSCULAS» que faltan por llenar (sin repetir, en orden).

    Solo cuentan los que no tienen minúsculas: en ruso y francés «…» también son comillas
    normales (ej. «Vasco Translator V4 (electronic translator)» en la traducción oficial).
    """
    texto = _raiz(html).text_content() if (html or '').strip() else ''
    campos = (m.strip() for m in POR_LLENAR_RE.findall(texto))
    return list(dict.fromkeys(c for c in campos if any(x.isalpha() for x in c) and c == c.upper()))


def _clases(el):
    return (el.get('class') or '').split()


def _texto(cadena):
    return ESPACIOS_RE.sub(' ', cadena or '')


class EscritorHTML:
    """Escribe el HTML como párrafos en `contenedor` (un Document o una celda de tabla)."""

    def __init__(self, contenedor, ancho_util, al_nueva_hoja=None, tamano_pt=None, al_evidencias=None):
        self.contenedor = contenedor
        self.ancho = Emu(int(ancho_util))
        # Qué hacer con [[ NUEVA HOJA ]] (lo pone docx_oficio: salto + encabezado institucional).
        self.al_nueva_hoja = al_nueva_hoja
        # Qué hacer con [[ EVIDENCIAS ]] (docx_oficio: un bloque por evidencia de la persona).
        self.al_evidencias = al_evidencias
        self.tamano_pt = tamano_pt
        self.chico_pt = max(5.0, tamano_pt - DIFERENCIA_CHICO_PT) if tamano_pt else TAMANO_CHICO_PT

    def _hijo(self, contenedor, ancho):
        """Escritor para una celda: mismo tamaño de letra; sin nueva hoja ni evidencias."""
        return EscritorHTML(contenedor, ancho, tamano_pt=self.tamano_pt)

    def escribir(self, html):
        raiz = _raiz(limpiar_html(html))
        if raiz.text and raiz.text.strip():
            self._parrafo_de_texto(raiz.text)
        self._elementos(list(raiz))

    def _elementos(self, elementos):
        """Escribe los bloques en orden; lo que va entre [[ RECUADRO ]]/[[ TABLA ]] y su cierre va con borde."""
        tipo, dentro = None, None  # bloque con borde abierto: 'RECUADRO' o 'TABLA', y sus elementos
        for el in elementos:
            texto = el.text_content().strip()
            inicio = INICIO_BLOQUE_RE.fullmatch(texto)
            if inicio:
                if dentro is not None:
                    self._con_borde(tipo, dentro)
                tipo, dentro = inicio.group(1).upper(), []
                continue
            if FIN_BLOQUE_RE.fullmatch(texto):
                if dentro is not None:
                    self._con_borde(tipo, dentro)
                tipo, dentro = None, None
                continue  # un cierre suelto no se imprime
            if dentro is not None:
                dentro.append(el)
                continue
            self._bloque(el)
            if el.tail and el.tail.strip():
                self._parrafo_de_texto(el.tail)
        if dentro is not None:  # sin cerrar: llega hasta el final
            self._con_borde(tipo, dentro)

    def _con_borde(self, tipo, elementos):
        """RECUADRO: una sola celda con todo. TABLA: una fila por párrafo."""
        if not elementos:
            return
        if tipo == 'TABLA':
            filas = [_celdas(el) for el in elementos]  # cada párrafo una fila; ' || ' separa celdas
        else:
            filas = [[elementos]]
        columnas = max(len(f) for f in filas)
        tabla = self.contenedor.add_table(rows=len(filas), cols=columnas)
        tabla.style = 'Table Grid'
        for fila, celdas in zip(tabla.rows, filas):
            destinos = list(fila.cells)
            if len(celdas) < columnas:  # la última celda abarca las columnas que sobran
                ultima = destinos[len(celdas) - 1].merge(destinos[-1])
                destinos = destinos[:len(celdas) - 1] + [ultima]
            for celda, contenido in zip(destinos, celdas):
                ancho = int(self.ancho * (columnas - len(celdas) + 1 if celda is destinos[-1] else 1) / columnas)
                self._hijo(celda, Emu(ancho) - MARGENES_CELDA)._elementos(contenido)
                _quitar_vacio_inicial(celda)

    # ---- bloques ----

    def _bloque(self, el):
        etiqueta = el.tag.lower()
        if etiqueta in ETIQUETAS_LISTA:
            self._lista(el, ordenada_por_defecto=(etiqueta == 'ol'))
        elif etiqueta == 'li':
            self._lista_items([el], ordenada_por_defecto=False)
        else:  # p, div, h*, o un elemento suelto en línea
            self._parrafo(el, negritas=etiqueta.startswith('h') and etiqueta in ETIQUETAS_BLOQUE)

    def _parrafo_de_texto(self, texto):
        self.contenedor.add_paragraph().add_run(_texto(texto).strip())

    def _parrafo(self, el, negritas=False, prefijo='', sangria_cm=0.0):
        texto = _texto(el.text_content())
        marcador = texto.strip()
        if not prefijo:
            if NUEVA_HOJA_RE.fullmatch(marcador):
                if self.al_nueva_hoja:
                    self.al_nueva_hoja()
                return None  # dentro de un recuadro no aplica: se ignora
            if EVIDENCIAS_RE.fullmatch(marcador):
                if self.al_evidencias:
                    self.al_evidencias()
                return None
            firma = FIRMA_RE.fullmatch(marcador)
            if firma:
                return self._firma(firma.group(1))
        parrafo = self.contenedor.add_paragraph()
        clases = _clases(el)
        for clase in clases:
            if clase in ALINEACION:
                parrafo.alignment = ALINEACION[clase]
            elif clase.startswith('ql-indent-') and clase[10:].isdigit():
                sangria_cm += SANGRIA_CM * int(clase[10:])
        if sangria_cm:
            parrafo.paragraph_format.left_indent = Cm(sangria_cm)

        if not prefijo and RENGLON_RE.fullmatch(marcador):
            self._relleno(parrafo, WD_TAB_LEADER.LINES)
            return parrafo
        separador = SEPARADOR_RE.fullmatch(marcador)
        if separador and not prefijo:
            self._separador(parrafo, separador.group(1).strip())
            return parrafo

        if prefijo:
            parrafo.add_run(prefijo)
        if not texto.strip() and all(isinstance(h.tag, str) and h.tag.lower() == 'br' for h in el):
            return parrafo  # `<p><br></p>` de Quill: un renglón vacío, no un salto dentro del párrafo
        inicial = frozenset({'bold'}) if negritas else frozenset()
        self._en_linea(parrafo, el, inicial, es_raiz=True)
        if es_mayormente_arabe(texto):
            # Párrafo en árabe: de derecha a izquierda y, si no se eligió otra, alineado a la derecha.
            _bidi(parrafo)
            if not any(c in ALINEACION for c in clases):
                parrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        relleno = RELLENO_RE.search(texto)
        if relleno:
            caracter = relleno.group(2)[0]
            self._quitar_relleno_final(parrafo, caracter)
            self._relleno(parrafo, WD_TAB_LEADER.DASHES if caracter == '-' else WD_TAB_LEADER.LINES)
        return parrafo

    def _lista(self, el, ordenada_por_defecto):
        self._lista_items([li for li in el if isinstance(li.tag, str) and li.tag.lower() == 'li'],
                          ordenada_por_defecto)

    def _lista_items(self, items, ordenada_por_defecto):
        contador = {}
        for li in items:
            tipo = li.get('data-list') or ('ordered' if ordenada_por_defecto else 'bullet')
            nivel = next((int(c[10:]) for c in _clases(li) if c.startswith('ql-indent-') and c[10:].isdigit()), 0)
            if tipo == 'ordered':
                contador[nivel] = contador.get(nivel, 0) + 1
                for mas_profundo in [n for n in contador if n > nivel]:
                    del contador[mas_profundo]
                prefijo = f'{contador[nivel]}.\t'
            else:
                prefijo = '•\t'
            parrafo = self._parrafo(li, prefijo=prefijo, sangria_cm=0.63 * (nivel + 1))
            formato = parrafo.paragraph_format
            formato.first_line_indent = Cm(-0.63)
            formato.tab_stops.add_tab_stop(Cm(0.63 * (nivel + 1)))

    # ---- en línea ----

    def _en_linea(self, parrafo, el, marcas, es_raiz=False):
        if el.text:
            self._run(parrafo, el.text, marcas)
        for hijo in el:
            if isinstance(hijo.tag, str):
                etiqueta = hijo.tag.lower()
                if etiqueta == 'br':
                    parrafo.add_run().add_break()
                elif etiqueta in ETIQUETAS_LISTA or etiqueta == 'li':
                    # Lista anidada dentro de un párrafo: se aplana como texto.
                    self._en_linea(parrafo, hijo, marcas)
                else:
                    extra = MARCAS.get(etiqueta)
                    nuevas = marcas | {extra} if extra else marcas
                    if 'ql-size-small' in _clases(hijo):
                        nuevas = nuevas | {'chico'}
                    self._en_linea(parrafo, hijo, nuevas)
            if hijo.tail:
                self._run(parrafo, hijo.tail, marcas)

    def _run(self, parrafo, texto, marcas):
        texto = _texto(texto)
        if not texto:
            return
        # El árabe va en runs propios marcados RTL; lo demás, tal cual.
        posicion = 0
        tramos = []
        for arabe in ARABE_RE.finditer(texto):
            tramos += [(texto[posicion:arabe.start()], False), (arabe.group(0), True)]
            posicion = arabe.end()
        tramos.append((texto[posicion:], False))
        for tramo, rtl in tramos:
            if not tramo:
                continue
            run = parrafo.add_run(tramo)
            run.bold = True if 'bold' in marcas else None
            run.italic = True if 'italic' in marcas else None
            run.underline = True if 'underline' in marcas else None
            if 'strike' in marcas:
                run.font.strike = True
            if rtl:
                run.font.rtl = True
            if 'superscript' in marcas:
                run.font.superscript = True
            if 'chico' in marcas:
                run.font.size = Pt(self.chico_pt)

    # ---- guiones ----

    def _separador(self, parrafo, titulos):
        """Guiones de margen a margen con uno o varios títulos (`A | B`) repartidos a lo ancho."""
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        tabs = parrafo.paragraph_format.tab_stops
        titulos = [t.strip() for t in titulos.split('|') if t.strip()]
        for i, _titulo in enumerate(titulos, start=1):
            posicion = Emu(int(self.ancho * i / (len(titulos) + 1)))
            tabs.add_tab_stop(posicion, WD_TAB_ALIGNMENT.CENTER, WD_TAB_LEADER.DASHES)
        tabs.add_tab_stop(self.ancho, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DASHES)
        for titulo in titulos:
            parrafo.add_run('\t')
            parrafo.add_run(f' {titulo} ').bold = True
        parrafo.add_run(TAB_CON_RELLENO)

    def _relleno(self, parrafo, leader=WD_TAB_LEADER.DASHES):
        parrafo.paragraph_format.tab_stops.add_tab_stop(self.ancho, WD_TAB_ALIGNMENT.RIGHT, leader)
        parrafo.add_run(TAB_CON_RELLENO)

    @staticmethod
    def _quitar_relleno_final(parrafo, caracter='-'):
        """Quita el ' --' (o ' __') del final y los espacios que lo preceden (puede venir partido en varios runs)."""
        por_quitar = 2
        for run in reversed(parrafo.runs):
            texto = run.text.rstrip()
            while por_quitar and texto.endswith(caracter):
                texto = texto[:-1]
                por_quitar -= 1
            texto = texto.rstrip()
            run.text = texto
            if texto and not por_quitar:
                break  # ya se llegó a texto real

    def _firma(self, leyenda):
        """Hueco para la rúbrica, línea centrada y la leyenda en negritas debajo.

        Con `A || B`, dos firmas lado a lado (ej. persona y acompañantes en el 03).
        """
        leyendas = CELDA_RE.split(leyenda) if '||' in leyenda else None
        if leyendas:
            tabla = self.contenedor.add_table(rows=1, cols=len(leyendas))
            for celda, texto in zip(tabla.rows[0].cells, leyendas):
                celda.width = Emu(int(self.ancho / len(leyendas)))
                self._hijo(celda, Emu(int(self.ancho / len(leyendas))) - MARGENES_CELDA)._firma(texto)
                _quitar_vacio_inicial(celda)
            return None
        linea = self.contenedor.add_paragraph()
        linea.alignment = WD_ALIGN_PARAGRAPH.CENTER
        formato = linea.paragraph_format
        formato.space_before = Pt(ESPACIO_FIRMA_PT)
        sangria = max(0, min(int(Cm(SANGRIA_FIRMA_CM)), (int(self.ancho) - int(Cm(LINEA_FIRMA_MINIMA_CM))) // 2))
        sangria = Emu(sangria)
        formato.left_indent = formato.right_indent = sangria
        borde_superior(linea)
        if leyenda:
            linea.add_run(leyenda).bold = True
        return linea


# Hijos de <w:pPr> que van DESPUÉS de <w:pBdr> según el esquema de OOXML (Word rechaza otro orden).
_DESPUES_DE_PBDR = (
    'w:shd', 'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap', 'w:overflowPunct',
    'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN', 'w:bidi', 'w:adjustRightInd', 'w:snapToGrid',
    'w:spacing', 'w:ind', 'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
    'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl', 'w:divId', 'w:cnfStyle',
    'w:rPr', 'w:sectPr', 'w:pPrChange',
)


def _celdas(el):
    """Las celdas de una fila de [[ TABLA ]]: el párrafo partido en ' || ' (cada una un <p> con la misma clase).

    El separador debe ir fuera de negritas/cursivas; si cae dentro, el parser cierra la
    etiqueta abierta y la celda siguiente pierde ese formato.
    """
    interior = (escape(el.text) if el.text else '') + ''.join(
        lxml_html.tostring(h, encoding='unicode') for h in el)
    if '||' not in interior:
        return [[el]]
    clase = el.get('class')
    atributo = f' class="{clase}"' if clase else ''
    return [[lxml_html.fragment_fromstring(f'<p{atributo}>{pieza}</p>')] for pieza in CELDA_RE.split(interior)]


def _quitar_vacio_inicial(celda):
    """La celda nace con un párrafo vacío: si ya se escribió algo, sobra."""
    if len(celda.paragraphs) > 1 and not celda.paragraphs[0].text and not celda.paragraphs[0]._p.xpath('.//w:drawing'):
        vacio = celda.paragraphs[0]._element
        vacio.getparent().remove(vacio)


def es_mayormente_arabe(texto):
    letras = [c for c in texto if c.isalpha()]
    return bool(letras) and len(LETRA_ARABE_RE.findall(texto)) > len(letras) / 2


# Hijos de <w:pPr> que van DESPUÉS de <w:bidi>.
_DESPUES_DE_BIDI = (
    'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind', 'w:contextualSpacing', 'w:mirrorIndents',
    'w:suppressOverlap', 'w:jc', 'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap',
    'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange',
)


def _bidi(parrafo):
    ppr = parrafo._p.get_or_add_pPr()
    ppr.insert_element_before(parse_xml(f'<w:bidi {nsdecls("w")}/>'), *_DESPUES_DE_BIDI)


def borde_superior(parrafo):
    """Línea sobre el párrafo (la línea de firma)."""
    ppr = parrafo._p.get_or_add_pPr()
    borde = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr>'
    )
    ppr.insert_element_before(borde, *_DESPUES_DE_PBDR)
