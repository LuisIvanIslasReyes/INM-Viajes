import datetime
import io
from decimal import Decimal

from docx import Document
from django.test import SimpleTestCase, TestCase

from ..models import DatosOficina, MotivoRechazo, OficioInstancia, PlantillaOficio
from ..services.contexto import CLAVES, contexto_para, fecha_larga
from ..services.docx_oficio import Pieza, pieza_de, render_docx
from ..services.variables import sustituir, variables_usadas
from .utils import Escenario, empleado


class VariablesTests(SimpleTestCase):

    def test_sustituye_escapa_y_reporta_desconocidas(self):
        html, desconocidas = sustituir(
            '<p>{{nombre}} y {{ nombre }} de {{pais}} {{nada}} {{nada}}</p>',
            {'nombre': 'A <b>&', 'pais': None},
        )
        self.assertEqual(html, '<p>A &lt;b&gt;&amp; y A &lt;b&gt;&amp; de  {{nada}} {{nada}}</p>')
        self.assertEqual(desconocidas, ['nada'])

    def test_variables_usadas_sin_repetir(self):
        self.assertEqual(variables_usadas('{{a}} {{b}} {{ a }}'), ['a', 'b'])

    def test_fecha_larga(self):
        self.assertEqual(fecha_larga(datetime.date(2026, 11, 7)), '7 de noviembre de 2026')
        self.assertEqual(fecha_larga(None), '')


class ContextoTests(TestCase):

    def setUp(self):
        self.e = Escenario(idioma='zh')
        self.instancia = OficioInstancia.objects.create(
            persona=self.e.persona, plantilla=self.e.p02, fecha_oficio=datetime.date(2026, 11, 25),
        )

    def test_valores(self):
        c = contexto_para(self.instancia)
        self.assertEqual(set(c), CLAVES)  # el panel del editor ofrece exactamente lo que existe
        self.assertEqual(c['firmante_nombre'], 'LIC. MELISSA GALLEGOS')
        self.assertEqual(c['firmante_cargo'], 'JEFA DE DEPARTAMENTO')
        self.assertEqual(c['firmante_fundamento'], 'Artículo 23, fracciones I, II, III y IV')
        self.assertEqual((c['firmante_adscrito'], c['firmante_el_la']), ('adscrita', 'la'))
        self.assertEqual(c['testigo1_nombre'], 'SAMANTHA MORALES')
        self.assertEqual(c['fecha_larga'], '25 de noviembre de 2026')
        self.assertEqual(c['extranjero_fecha_nacimiento'], '14/04/1994')
        self.assertEqual(c['extranjero_idioma'], 'chino')
        self.assertEqual(c['aeropuerto'], 'AEROPUERTO INTERNACIONAL DE TIJUANA')
        self.assertEqual(c['motivo_rechazo'], '')

    def test_testigo_propio_del_oficio_y_firmante_hombre(self):
        otro = empleado(9, 'PEDRO', 'SUSTITUTO', plaza='REPRESENTANTE LOCAL')
        self.instancia.testigo_2 = otro
        self.e.expediente.firmante = otro
        c = contexto_para(self.instancia)
        self.assertEqual(c['testigo1_nombre'], 'SAMANTHA MORALES')
        self.assertEqual(c['testigo2_nombre'], 'LIC. PEDRO SUSTITUTO')
        self.assertEqual((c['firmante_adscrito'], c['firmante_el_la']), ('adscrito', 'el'))
        self.assertEqual(c['firmante_fundamento'], 'Artículo 14, apartado B, fracciones I, II y III')

    def test_sin_firmante_ni_testigos(self):
        exp = self.e.expediente
        exp.firmante = exp.testigo_1 = exp.testigo_2 = None
        c = contexto_para(self.instancia)
        self.assertEqual((c['firmante_nombre'], c['firmante_fundamento'], c['testigo1_nombre']), ('', '', ''))

    def test_motivo_y_datos_de_oficina(self):
        self.e.persona.motivo_rechazo = MotivoRechazo.objects.get(orden=2)
        DatosOficina.objects.update(aeropuerto='AEROPUERTO DE PRUEBA')
        c = contexto_para(self.instancia)
        self.assertTrue(c['motivo_rechazo'].startswith('Falta de visa válida y vigente'))
        self.assertEqual(c['aeropuerto'], 'AEROPUERTO DE PRUEBA')


class SiembraTests(TestCase):

    def test_plantillas_motivos_y_oficina(self):
        self.assertEqual(list(PlantillaOficio.objects.values_list('numero', 'bloque_firmas')),
                         [(2, 'CONSTANCIA'), (3, 'NINGUNO'), (4, 'NINGUNO'), (Decimal('4.1'), 'NINGUNO'),
                          (5, 'AUTORIDAD_PERSONA'), (7, 'CONSTANCIA'), (8, 'CONSTANCIA'), (9, 'AUTORIDAD_PERSONA'),
                          (11, 'NOTIFICACION'), (12, 'CONSTANCIA'), (13, 'EMPRESA'), (14, 'ACUERDO')])
        self.assertEqual(MotivoRechazo.objects.count(), 6)
        self.assertEqual(DatosOficina.objects.count(), 1)
        for plantilla in PlantillaOficio.objects.all():
            with self.subTest(plantilla=plantilla.clave):
                self.assertLessEqual(set(variables_usadas(plantilla.contenido_html)), CLAVES)


def _abrir(docx_bytes):
    return Document(io.BytesIO(docx_bytes))


class DocxTests(TestCase):

    def setUp(self):
        self.e = Escenario()

    def _instancia(self, plantilla):
        return OficioInstancia.objects.create(
            persona=self.e.persona, plantilla=plantilla, contenido_html=plantilla.contenido_html,
            fecha_oficio=datetime.date(2026, 11, 25),
        )

    def test_constancia_02(self):
        documento = _abrir(render_docx([pieza_de(self._instancia(self.e.p02))]))
        textos = [p.text for p in documento.paragraphs]
        self.assertEqual(textos[:5], [
            'SECRETARÍA DE GOBERNACIÓN', 'INSTITUTO NACIONAL DE MIGRACIÓN',
            'OFICINA DE REPRESENTACIÓN EN BAJA CALIFORNIA', 'AEROPUERTO INTERNACIONAL DE TIJUANA',
            'SALA INTERNACIONAL',
        ])
        self.assertEqual(textos[5], 'CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO')
        self.assertEqual(textos[6], 'Tijuana, Baja California, 25 de noviembre de 2026.')
        cuerpo = '\n'.join(textos)
        self.assertIn('quien suscribe LIC. MELISSA GALLEGOS en su carácter de JEFA DE DEPARTAMENTO adscrita', cuerpo)
        self.assertIn('vigente (D.O.F. 21/03/2025) y Artículo 23, fracciones I, II, III y IV del ACUERDO', cuerpo)
        self.assertIn('\t HACE CONSTAR \t\u200b', textos)
        self.assertNotIn('{{', cuerpo)

        [tabla] = documento.tables
        self.assertEqual(len(tabla.rows), 2)
        celdas = [c.text for fila in tabla.rows for c in fila.cells]
        self.assertIn('LA AUTORIDAD MIGRATORIA', celdas[0])
        self.assertIn('JEFA DE DEPARTAMENTO', celdas[0])
        self.assertIn('WANG PRUEBA', celdas[1])
        self.assertIn('SAMANTHA MORALES', celdas[2])
        self.assertIn('JAVIER DUARTE', celdas[3])
        # La línea de firma es el borde superior del párrafo del nombre (sin renglón de guiones bajos).
        nombre = tabla.rows[0].cells[0].paragraphs[1]
        self.assertEqual(nombre.text, 'LIC. MELISSA GALLEGOS')
        self.assertIn('<w:pBdr>', nombre._p.pPr.xml)
        self.assertNotIn('___', celdas[0])
        # Las filas de firmas no se parten entre hojas.
        self.assertTrue(all(fila._tr.trPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cantSplit') is not None
                            for fila in tabla.rows))

    def test_hoja_membretada_detras_del_texto(self):
        documento = _abrir(render_docx([pieza_de(self._instancia(self.e.p02))]))
        xml = documento.sections[0].header._element.xml
        self.assertIn('behindDoc="1"', xml)
        self.assertIn('relativeFrom="page"', xml)
        self.assertEqual(len(documento.sections[0].header.part.package.image_parts), 1)

    def test_notificacion_11(self):
        self.e.persona.motivo_rechazo = MotivoRechazo.objects.get(orden=4)
        self.e.persona.save()
        documento = _abrir(render_docx([pieza_de(self._instancia(self.e.p11))]))
        cuerpo = '\n'.join(p.text for p in documento.paragraphs)
        self.assertIn('No. de sala de entrevista: 1', cuerpo)
        recuadro, firmas = documento.tables
        # El motivo va en un recuadro con borde, como en el Word oficial.
        self.assertEqual(recuadro.style.name, 'Table Grid')
        self.assertEqual([p.text for p in recuadro.rows[0].cells[0].paragraphs][0], 'Motivo de rechazo aplicable')
        self.assertIn('Incumplimiento de requisitos para la condición de estancia solicitada', recuadro.rows[0].cells[0].text)
        self.assertNotIn('RECUADRO', cuerpo)
        self.assertEqual(len(firmas.rows), 1)
        self.assertIn('ATENTAMENTE.', firmas.rows[0].cells[0].text)
        self.assertIn('Recibí original de la presente notificación.', firmas.rows[0].cells[1].text)

    def test_varias_piezas_una_seccion_por_oficio(self):
        piezas = [pieza_de(self._instancia(self.e.p02)), pieza_de(self._instancia(self.e.p11))]
        documento = _abrir(render_docx(piezas))
        self.assertEqual(len(documento.sections), 2)
        self.assertEqual(len(documento.tables), 3)  # firmas del 02; recuadro y firmas del 11

    def test_sin_firmas_ni_fecha(self):
        pieza = Pieza(titulo='LIBRE', cuerpo_html='<p>Hola</p>', bloque_firmas='NINGUNO', lleva_fecha=False,
                      contexto={'entidad': 'BC'})
        documento = _abrir(render_docx([pieza]))
        self.assertEqual(documento.tables, [])
        self.assertEqual([p.text for p in documento.paragraphs][-2:], ['LIBRE', 'Hola'])
