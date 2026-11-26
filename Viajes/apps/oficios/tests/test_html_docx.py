from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm
from django.test import SimpleTestCase

from ..services.html_docx import EscritorHTML, limpiar_html

ANCHO = Cm(18.41)
TWIP = 635  # Word guarda las posiciones en twips: redondea hasta 1 twip (635 EMU)


def escribir(html):
    document = Document()
    EscritorHTML(document, ANCHO).escribir(html)
    return document.paragraphs


class LimpiarHTMLTests(SimpleTestCase):

    def test_quita_lo_ejecutable_y_conserva_el_texto(self):
        limpio = limpiar_html(
            '<p onclick="x()" style="color:red">Hola <script>alert(1)</script>'
            '<a href="javascript:x">liga</a><img src=x onerror=y></p><style>p{}</style>'
        )
        self.assertEqual(limpio, '<p>Hola liga</p>')

    def test_conserva_clases_de_quill_y_listas(self):
        limpio = limpiar_html(
            '<p class="ql-align-justify otra">a</p><ol><li data-list="bullet" class="ql-indent-1" id="z">b</li></ol>'
        )
        self.assertEqual(limpio, '<p class="ql-align-justify">a</p><ol><li data-list="bullet" class="ql-indent-1">b</li></ol>')

    def test_texto_suelto_y_vacio(self):
        self.assertEqual(limpiar_html('solo <b>texto</b> & más'), 'solo <b>texto</b> &amp; más')
        self.assertEqual(limpiar_html(''), '')


class EscritorHTMLTests(SimpleTestCase):

    def test_marcas_y_alineacion(self):
        [p] = escribir('<p class="ql-align-justify">En <strong>Tijuana</strong>, <em>hoy</em> <u>sí</u>.</p>')
        self.assertEqual(p.text, 'En Tijuana, hoy sí.')
        self.assertEqual(p.alignment, WD_ALIGN_PARAGRAPH.JUSTIFY)
        negritas = [r.text for r in p.runs if r.bold]
        self.assertEqual(negritas, ['Tijuana'])
        self.assertTrue(any(r.italic for r in p.runs if r.text == 'hoy'))
        self.assertTrue(any(r.underline for r in p.runs if r.text == 'sí'))

    def test_separador_con_titulo(self):
        [p] = escribir('<p class="ql-align-justify">[[ HACE CONSTAR ]]</p>')
        tabs = list(p.paragraph_format.tab_stops)
        self.assertEqual([t.alignment for t in tabs], [WD_TAB_ALIGNMENT.CENTER, WD_TAB_ALIGNMENT.RIGHT])
        self.assertTrue(all(t.leader == WD_TAB_LEADER.DASHES for t in tabs))
        self.assertAlmostEqual(tabs[1].position, ANCHO, delta=TWIP)
        self.assertEqual(p.text, '\t HACE CONSTAR \t\u200b')
        self.assertTrue([r for r in p.runs if r.text == ' HACE CONSTAR '][0].bold)
        self.assertEqual(p.alignment, WD_ALIGN_PARAGRAPH.LEFT)

    def test_linea_completa_de_guiones(self):
        [p] = escribir('<p>[[ ]]</p>')
        tabs = list(p.paragraph_format.tab_stops)
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0].leader, WD_TAB_LEADER.DASHES)
        self.assertEqual(p.text, '\t\u200b')

    def test_relleno_al_final_del_parrafo(self):
        [p] = escribir('<p>publicado en 2012. <strong>--</strong></p>')
        self.assertEqual(p.text, 'publicado en 2012.\t\u200b')
        [tab] = list(p.paragraph_format.tab_stops)
        self.assertEqual((tab.alignment, tab.leader), (WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DASHES))
        self.assertAlmostEqual(tab.position, ANCHO, delta=TWIP)

    def test_guiones_en_medio_no_son_relleno(self):
        [p] = escribir('<p>uno -- dos</p>')
        self.assertEqual(p.text, 'uno -- dos')
        self.assertEqual(len(p.paragraph_format.tab_stops), 0)

    def test_listas_salto_y_entidades(self):
        parrafos = escribir(
            '<ol><li data-list="ordered">uno</li><li data-list="ordered">dos</li>'
            '<li data-list="bullet">viñeta</li></ol><p>a<br>b &amp; c</p><p><br></p>'
        )
        # `<p><br></p>` es UN renglón vacío (como en el editor), no un salto + marca de párrafo.
        self.assertEqual([p.text for p in parrafos], ['1.\tuno', '2.\tdos', '•\tviñeta', 'a\nb & c', ''])

    def test_espacios_y_saltos_del_codigo_fuente(self):
        [p] = escribir('<p>En\n   Tijuana,\tB.C.</p>')
        self.assertEqual(p.text, 'En Tijuana, B.C.')
