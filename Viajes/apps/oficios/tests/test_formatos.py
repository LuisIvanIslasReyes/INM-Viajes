"""Marcadores del texto (renglón, tabla, firma, nueva hoja, varios títulos, «…») y los formatos 08–14."""
import datetime
import io
from decimal import Decimal

from docx import Document
from docx.enum.text import WD_TAB_LEADER
from docx.shared import Cm
from django.test import SimpleTestCase, TestCase

from ..models import MotivoRechazo, OficioInstancia, PlantillaOficio
from ..services import expedientes as servicio
from ..services.contexto import CLAVES
from ..services.docx_oficio import pieza_de, render_docx
from ..services.html_docx import EscritorHTML, pendientes
from ..services.variables import variables_usadas
from .utils import Escenario, MediaTemporalMixin, registro, usuarios

ANCHO = Cm(18.41)


def _escribir(html, al_nueva_hoja=None):
    document = Document()
    EscritorHTML(document, ANCHO, al_nueva_hoja=al_nueva_hoja).escribir(html)
    return document


def _abrir(docx_bytes):
    return Document(io.BytesIO(docx_bytes))


class MarcadoresTests(SimpleTestCase):

    def test_renglon_y_linea_al_final(self):
        doc = _escribir('<p>[[ RENGLÓN ]]</p><p>[[ renglon ]]</p><p>Hora: __</p>')
        textos = [p.text for p in doc.paragraphs]
        self.assertEqual(textos, ['\t\u200b', '\t\u200b', 'Hora:\t\u200b'])
        for p in doc.paragraphs:
            [tab] = list(p.paragraph_format.tab_stops)
            self.assertEqual(tab.leader, WD_TAB_LEADER.LINES)

    def test_separador_con_varios_titulos(self):
        [p] = _escribir('<p>[[ CONSTE | SE CIERRA Y SE AUTORIZA LO ACTUADO ]]</p>').paragraphs
        self.assertEqual(p.text, '\t CONSTE \t SE CIERRA Y SE AUTORIZA LO ACTUADO \t\u200b')
        self.assertEqual(len(p.paragraph_format.tab_stops), 3)
        self.assertTrue(all(t.leader == WD_TAB_LEADER.DASHES for t in p.paragraph_format.tab_stops))

    def test_tabla_una_fila_por_parrafo(self):
        doc = _escribir('<p>[[ TABLA ]]</p><p>Nombre: A</p><p>Nacionalidad: b</p><p>[[ /TABLA ]]</p><p>Fin</p>')
        [tabla] = doc.tables
        self.assertEqual([f.cells[0].text for f in tabla.rows], ['Nombre: A', 'Nacionalidad: b'])
        self.assertEqual(tabla.style.name, 'Table Grid')
        self.assertEqual([p.text for p in doc.paragraphs], ['Fin'])

    def test_firma(self):
        [p] = _escribir('<p>[[ FIRMA: NOMBRE Y FIRMA DEL REPRESENTANTE ]]</p>').paragraphs
        self.assertEqual(p.text, 'NOMBRE Y FIRMA DEL REPRESENTANTE')
        self.assertIn('<w:pBdr>', p._p.pPr.xml)
        self.assertTrue(p.runs[0].bold)

    def test_nueva_hoja_llama_al_encabezado_y_se_ignora_sin_el(self):
        llamadas = []
        doc = _escribir('<p>A</p><p>[[ NUEVA HOJA ]]</p><p>B</p>', al_nueva_hoja=lambda: llamadas.append(1))
        self.assertEqual(llamadas, [1])
        self.assertEqual([p.text for p in doc.paragraphs], ['A', 'B'])
        doc = _escribir('<p>[[ RECUADRO ]]</p><p>[[ NUEVA HOJA ]]</p><p>x</p><p>[[ /RECUADRO ]]</p>')
        self.assertEqual(doc.tables[0].rows[0].cells[0].text, 'x')

    def test_pendientes(self):
        self.assertEqual(pendientes('<p>vuelo «VUELO» a <strong>«DESTINO»</strong> y «VUELO»</p>'), ['VUELO', 'DESTINO'])
        self.assertEqual(pendientes(''), [])
        # En ruso y francés «…» también son comillas: con minúsculas no es un campo.
        self.assertEqual(pendientes('<p>marca «Vasco Translator V4 (electronic translator)» y «DESTINO» «123»</p>'),
                         ['DESTINO'])


class FormatosTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero)
        self.e.persona.motivo_rechazo = MotivoRechazo.objects.first()
        self.e.persona.numero_acta = 'ORBC/AIMMTJ/AR000316/2026'
        self.e.persona.fecha_arribo = datetime.date(2026, 11, 17)
        self.e.persona.origen = 'PEKÍN, CHINA'
        self.e.persona.aerolinea = 'HAINAN AIRLINES'
        self.e.persona.save()

    def _oficio(self, numero):
        plantilla = PlantillaOficio.objects.get(numero=numero)
        [oficio] = servicio.crear_borradores(self.e.persona, [plantilla], self.aero)
        return oficio

    def _documento(self, oficio):
        return _abrir(render_docx([pieza_de(oficio)]))

    def test_todas_las_plantillas_usan_variables_existentes(self):
        for plantilla in PlantillaOficio.objects.all():
            with self.subTest(plantilla=plantilla.clave):
                self.assertLessEqual(set(variables_usadas(plantilla.contenido_html)), CLAVES)

    def test_08_y_12_constancias(self):
        doc = self._documento(self._oficio(8))
        textos = [p.text for p in doc.paragraphs]
        self.assertEqual(textos[5], 'CONSTANCIA DE LLAMADA PERSONAL')
        self.assertTrue(textos[6].startswith('En Tijuana, Baja California, siendo el día'))  # sin línea de fecha
        self.assertIn('Nombre de la persona con quien se comunicó', '\n'.join(textos))

        doc = self._documento(self._oficio(12))
        cuerpo = '\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('firmar el acta de rechazo número ORBC/AIMMTJ/AR000316/2026', cuerpo)
        self.assertIn('\t CONSTE \t SE CIERRA Y SE AUTORIZA LO ACTUADO \t', cuerpo)
        self.assertEqual(len(doc.tables[0].rows), 2)  # constancia: autoridad/persona y testigos

    def test_09_tabla_recuadro_y_firmas_sin_testigos(self):
        oficio = self._oficio(9)
        doc = self._documento(oficio)
        datos, evidencia, firmas = doc.tables
        self.assertEqual(len(datos.rows), 4)
        self.assertEqual(datos.rows[1].cells[0].text, 'Nombre: WANG PRUEBA')
        # Sin evidencias capturadas: un bloque en blanco para llenar a mano.
        self.assertIn('Verificación realizada a:', evidencia.rows[0].cells[0].text)
        self.assertIn('(Fotografía del registro de llamadas', evidencia.rows[0].cells[0].text)
        self.assertEqual(len(firmas.rows), 1)
        self.assertIn('LA PERSONA EXTRANJERA', firmas.rows[0].cells[1].text)
        # No lleva testigos: imprime aunque el expediente no los tenga.
        self.e.expediente.testigo_1 = self.e.expediente.testigo_2 = None
        self.e.expediente.save()
        self.assertEqual(servicio.revisar(OficioInstancia.objects.get(pk=oficio.pk))[0], [])

    def test_13_dos_hojas_acuse_y_campos_por_llenar(self):
        oficio = self._oficio(13)
        doc = self._documento(oficio)
        cuerpo = '\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Fecha de arribo: 17 de noviembre de 2026.', cuerpo)
        self.assertIn('Origen: PEKÍN, CHINA', cuerpo)
        self.assertIn('se notifica a la aerolínea HAINAN AIRLINES', cuerpo)
        # La segunda hoja repite el encabezado institucional, con salto de página.
        encabezados = [p for p in doc.paragraphs if p.text == 'SECRETARÍA DE GOBERNACIÓN']
        self.assertEqual(len(encabezados), 2)
        self.assertTrue(encabezados[1].paragraph_format.page_break_before)
        [firmas] = doc.tables
        self.assertIn('NOMBRE Y FIRMA DEL REPRESENTANTE DE LA EMPRESA TRANSPORTISTA', firmas.rows[0].cells[0].text)
        # Lo que va entre «…» impide imprimir hasta llenarlo.
        errores, _ = servicio.revisar(oficio)
        self.assertEqual(len(errores), 1)
        self.assertIn('«NOMBRE DEL REPRESENTANTE»', errores[0])
        lleno = oficio.contenido_html
        for campo in servicio.pendientes(lleno):
            lleno = lleno.replace(f'«{campo}»', 'X')
        servicio.guardar_borrador(oficio, self.aero, lleno)
        self.assertEqual(servicio.revisar(oficio)[0], [])

    def test_14_firmas_de_tres_filas(self):
        doc = self._documento(self._oficio(14))
        [firmas] = doc.tables
        self.assertEqual(len(firmas.rows), 3)
        self.assertIn('LA AUTORIDAD MIGRATORIA', firmas.rows[0].cells[0].text)
        # Fila de en medio combinada: una sola firma centrada.
        medio = firmas.rows[1]
        self.assertEqual(medio.cells[0]._tc, medio.cells[1]._tc)
        self.assertIn('NOMBRE Y FIRMA DEL REPRESENTANTE DE LA AEROLÍNEA', medio.cells[0].text)
        self.assertIn('TESTIGO DE ASISTENCIA', firmas.rows[2].cells[1].text)
        cuerpo = '\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('\t ACUERDA \t', cuerpo)
        self.assertIn('en el acta No. ORBC/AIMMTJ/AR000316/2026', cuerpo)

    def test_precarga_arribo_origen_y_aerolinea(self):
        r = registro(self.aero, 'ARRIBO PRUEBA')
        datos = servicio.datos_desde_registro(r)
        self.assertEqual((datos['fecha_arribo'], datos['origen'], datos['aerolinea']),
                         (datetime.date(2026, 11, 24), 'PEKÍN, CHINA', 'HAINAN AIRLINES'))


class TamanoLetraTests(MediaTemporalMixin, TestCase):

    def test_cada_plantilla_con_el_tamano_de_su_word_y_congelado(self):
        tamanos = dict(PlantillaOficio.objects.values_list('numero', 'tamano_letra_pt'))
        self.assertEqual({n: float(t) for n, t in tamanos.items()},
                         {2: 9.5, 3: 7.0, 4: 8.0, Decimal('4.1'): 8.0, 5: 9.5, 7: 9.5, 8: 9.5, 9: 9.0, 11: 10.0,
                          12: 9.0, 13: 9.0, 14: 9.0})
        aero, _ = usuarios()
        e = Escenario(aero)
        [o02, o11] = servicio.crear_borradores(e.persona, [e.p02, e.p11], aero)
        doc = _abrir(render_docx([pieza_de(o02), pieza_de(o11)]))
        tamanos_02 = {r.font.size.pt for p in doc.paragraphs[:12] for r in p.runs if r.text.strip()}
        self.assertEqual(tamanos_02, {9.5})
        ultimo = [r for p in doc.paragraphs for r in p.runs if r.text.strip()][-1]
        self.assertEqual(ultimo.font.size.pt, 10.0)  # el 11, en la segunda sección
        servicio.imprimir(o02, aero)
        e.p02.tamano_letra_pt = 11
        e.p02.save()
        self.assertEqual(pieza_de(OficioInstancia.objects.get(pk=o02.pk)).tamano_pt, 9.5)
