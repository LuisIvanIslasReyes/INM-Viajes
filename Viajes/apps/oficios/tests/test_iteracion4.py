"""Iteración 4: tablas de varias columnas, firma doble, notas al pie, evidencias (09/05) y formularios 03–05."""
import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from docx import Document
from docx.shared import Cm
from PIL import Image

from apps.camara.models import FotoRechazo

from ..models import Evidencia, OficioInstancia, PlantillaOficio
from ..services import expedientes as servicio
from ..services.docx_oficio import pieza_de, render_docx
from ..services.html_docx import EscritorHTML
from .utils import Escenario, MediaTemporalMixin, registro, usuarios

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def png(ancho=800, alto=600, color='red'):
    buffer = io.BytesIO()
    Image.new('RGB', (ancho, alto), color).save(buffer, format='PNG')
    return buffer.getvalue()


def _abrir(docx_bytes):
    return Document(io.BytesIO(docx_bytes))


def _escribir(html, **kwargs):
    document = Document()
    EscritorHTML(document, Cm(18), **kwargs).escribir(html)
    return document


class MotorTests(SimpleTestCase):

    def test_tabla_con_varias_columnas(self):
        doc = _escribir('<p>[[ TABLA ]]</p><p><strong>DATOS</strong></p>'
                        '<p><strong>Nombre:</strong> A || <strong>Nacionalidad:</strong> b</p>'
                        '<p>NUE || Tarjeta || Vigencia</p><p>[[ /TABLA ]]</p>')
        [tabla] = doc.tables
        self.assertEqual(len(tabla.columns), 3)
        datos, dos, tres = tabla.rows
        self.assertEqual(len({c._tc for c in datos.cells}), 1)  # una celda a todo lo ancho
        self.assertEqual([c.text for c in dos.cells][:2], ['Nombre: A', 'Nacionalidad: b'])
        self.assertEqual(dos.cells[1]._tc, dos.cells[2]._tc)   # la última abarca lo que sobra
        self.assertEqual([c.text for c in tres.cells], ['NUE', 'Tarjeta', 'Vigencia'])
        self.assertTrue(dos.cells[0].paragraphs[0].runs[0].bold)

    def test_firma_doble(self):
        doc = _escribir('<p>[[ FIRMA: Firma de la persona || Acompañantes ]]</p>')
        [tabla] = doc.tables
        izquierda, derecha = tabla.rows[0].cells
        self.assertEqual((izquierda.text, derecha.text), ('Firma de la persona', 'Acompañantes'))
        self.assertIn('<w:pBdr>', izquierda.paragraphs[0]._p.xml)

    def test_superindice_y_chico_relativo(self):
        doc = _escribir('<p>Ley<sup>1</sup> <span class="ql-size-small">nota</span></p>', tamano_pt=9.5)
        runs = doc.paragraphs[0].runs
        sup = [r for r in runs if r.text == '1'][0]
        chico = [r for r in runs if r.text == 'nota'][0]
        self.assertTrue(sup.font.superscript)
        self.assertEqual(chico.font.size.pt, 8.0)
        chico_03 = _escribir('<p><span class="ql-size-small">nota</span></p>', tamano_pt=8).paragraphs[0].runs[0]
        self.assertEqual(chico_03.font.size.pt, 6.5)

    def test_evidencias_llama_al_callback_y_se_ignora_dentro_de_celdas(self):
        llamadas = []
        doc = _escribir('<p>A</p><p>[[ EVIDENCIAS ]]</p><p>B</p>', al_evidencias=lambda: llamadas.append(1))
        self.assertEqual(llamadas, [1])
        self.assertEqual([p.text for p in doc.paragraphs], ['A', 'B'])


class EvidenciasTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero)
        self.p09 = PlantillaOficio.objects.get(numero=9)
        self.p05 = PlantillaOficio.objects.get(numero=5)
        [self.o09] = servicio.crear_borradores(self.e.persona, [self.p09], self.aero)

    def _evidencia(self, plantilla=None, foto=True, **datos):
        evidencia = Evidencia(persona=self.e.persona, plantilla=plantilla or self.p09, **datos)
        if foto:
            evidencia.foto = SimpleUploadedFile('llamadas.png', png(*([600, 1600] if foto == 'alta' else [])),
                                                content_type='image/png')
        return servicio.guardar_evidencia(evidencia, self.aero)

    def _bloques(self, oficio):
        doc = _abrir(render_docx([pieza_de(OficioInstancia.objects.get(pk=oficio.pk))]))
        datos, *bloques, firmas = doc.tables
        return doc, bloques

    def test_sin_evidencias_un_bloque_en_blanco_y_aviso(self):
        doc, bloques = self._bloques(self.o09)
        self.assertEqual(len(bloques), 1)
        self.assertEqual(len(doc.inline_shapes), 0)
        _errores, avisos = servicio.revisar(self.o09)
        self.assertIn('No hay evidencias capturadas: sale un espacio en blanco para llenarlo a mano.', avisos)

    def test_tres_evidencias_cada_una_con_su_espacio(self):
        self._evidencia(verificacion_a='Hotel DoubleTree', hora='19:19', respuesta='SI', intentos=1,
                        nota='Confirma la reservación.')
        self._evidencia(foto='alta', verificacion_a='Empresa MAHLE', respuesta='NO', intentos=3)
        self._evidencia(foto=False, verificacion_a='Aerolínea')
        doc, bloques = self._bloques(self.o09)
        self.assertEqual(len(bloques), 3)
        primero = bloques[0].rows[0].cells[0].text
        self.assertIn('Evidencia 1', primero)
        self.assertIn('Verificación realizada a: Hotel DoubleTree', primero)
        self.assertIn('Sí: ☒', primero)
        self.assertIn('Número de intentos: 1', primero)
        self.assertIn('Observaciones: Confirma la reservación.', primero)
        self.assertIn('(Fotografía del registro de llamadas', bloques[2].rows[0].cells[0].text)  # sin foto
        self.assertEqual(len(doc.inline_shapes), 2)
        alta = doc.inline_shapes[1]
        self.assertLessEqual(alta.height, Cm(7.0) + 1)      # alto máximo, sin deformar
        self.assertAlmostEqual(alta.width / alta.height, 600 / 1600, places=2)
        # Ningún bloque se parte entre hojas.
        self.assertTrue(all(b.rows[0]._tr.trPr.find(W + 'cantSplit') is not None for b in bloques))
        _errores, avisos = servicio.revisar(self.o09)
        self.assertIn('Hay evidencias sin foto: sale su recuadro vacío.', avisos)

    def test_paquete_con_un_09_de_tres_evidencias(self):
        for nombre in ('Hotel', 'Empresa', 'Aerolínea'):
            self._evidencia(verificacion_a=nombre)
        [o02] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        doc = _abrir(servicio.render_paquete([self.o09, o02]))
        self.assertEqual(len(doc.sections), 2)  # 02 y luego 09, cada uno en su sección
        bloques = [t for t in doc.tables if 'Verificación realizada a:' in t.rows[0].cells[0].text]
        self.assertEqual([b.rows[0].cells[0].text.split('\n')[0] for b in bloques],
                         ['Evidencia 1', 'Evidencia 2', 'Evidencia 3'])
        self.assertEqual(len(doc.inline_shapes), 3)

    def test_05_solo_foto_y_observaciones(self):
        self._evidencia(plantilla=self.p05, nota='Herida en la mano.')
        [o05] = servicio.crear_borradores(self.e.persona, [self.p05], self.aero)
        doc, bloques = self._bloques(o05)
        texto = bloques[0].rows[0].cells[0].text
        self.assertNotIn('Verificación realizada a', texto)
        self.assertIn('Observaciones: Herida en la mano.', texto)
        self.assertIn('Evidencia fotográfica:', texto)
        self.assertEqual(len(doc.inline_shapes), 1)

    def test_impreso_congela_y_bloquea(self):
        self._evidencia(verificacion_a='Hotel')
        servicio.imprimir(self.o09, self.aero)
        oficio = OficioInstancia.objects.get(pk=self.o09.pk)
        self.assertEqual(oficio.snap_formato['evidencias'][0]['verificacion_a'], 'Hotel')
        with self.assertRaisesMessage(servicio.ErrorOficio, 'ya está impreso'):
            self._evidencia(verificacion_a='Otra')
        with self.assertRaisesMessage(servicio.ErrorOficio, 'ya está impreso'):
            servicio.quitar_evidencia(Evidencia.objects.get())
        # Lo impreso sale con lo congelado aunque se cambie el dato directo en la base.
        Evidencia.objects.update(verificacion_a='CAMBIADO')
        self.assertEqual(pieza_de(oficio).evidencias[0]['verificacion_a'], 'Hotel')

    def test_formato_sin_evidencias_no_acepta(self):
        with self.assertRaisesMessage(servicio.ErrorOficio, 'no lleva evidencias'):
            self._evidencia(plantilla=self.e.p02)

    def test_importar_de_camara(self):
        r = registro(self.aero, 'PASAJERO CAMARA')
        self.e.persona.registro = r
        self.e.persona.save()
        foto = FotoRechazo.objects.create(registro=r, foto=SimpleUploadedFile('cam.png', png(), 'image/png'),
                                          notas='Pantalla del teléfono', usuario_captura=self.aero)
        evidencia = servicio.importar_de_camara(self.e.persona, self.p09, foto, self.aero)
        self.assertEqual((evidencia.foto_rechazo, evidencia.nota), (foto, 'Pantalla del teléfono'))
        self.assertTrue(evidencia.foto.name.startswith('oficios/evidencias/'))
        otra = FotoRechazo.objects.create(registro=registro(self.aero, 'OTRO'),
                                          foto=SimpleUploadedFile('x.png', png(), 'image/png'))
        with self.assertRaisesMessage(servicio.ErrorOficio, 'no es de este pasajero'):
            servicio.importar_de_camara(self.e.persona, self.p09, otra, self.aero)


class EvidenciasVistasTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, self.general = usuarios()
        self.client.force_login(self.aero)
        self.e = Escenario(self.aero)
        self.p09 = PlantillaOficio.objects.get(numero=9)

    def test_agregar_editar_y_quitar(self):
        url = reverse('oficios:evidencia_agregar', args=[self.e.persona.pk, self.p09.pk])
        prefijo = f'ev{self.e.persona.pk}_{self.p09.pk}'
        resp = self.client.post(url, {
            f'{prefijo}-verificacion_a': 'Hotel', f'{prefijo}-hora': '10:30', f'{prefijo}-respuesta': 'SI',
            f'{prefijo}-intentos': '2', f'{prefijo}-nota': '',
            f'{prefijo}-foto': SimpleUploadedFile('f.png', png(), content_type='image/png'),
        }, follow=True)
        self.assertContains(resp, 'Evidencia agregada al 09')
        evidencia = Evidencia.objects.get()
        self.assertEqual((evidencia.orden, evidencia.intentos, evidencia.creada_por), (1, 2, self.aero))
        self.assertContains(resp, 'Evidencias del 09')

        resp = self.client.get(reverse('oficios:evidencia_editar', args=[evidencia.pk]))
        self.assertContains(resp, 'Evidencia del 09')
        self.client.post(reverse('oficios:evidencia_editar', args=[evidencia.pk]),
                         {'verificacion_a': 'Hotel Hilton', 'hora': '11:00', 'respuesta': 'NO', 'intentos': '',
                          'nota': 'Sin respuesta', 'orden': '1'})
        evidencia.refresh_from_db()
        self.assertEqual((evidencia.verificacion_a, evidencia.respuesta), ('Hotel Hilton', 'NO'))
        self.assertTrue(evidencia.foto)  # conserva la foto si no se sube otra

        self.client.post(reverse('oficios:evidencia_quitar', args=[evidencia.pk]))
        self.assertFalse(Evidencia.objects.exists())

    def test_foto_invalida_y_permisos(self):
        url = reverse('oficios:evidencia_agregar', args=[self.e.persona.pk, self.p09.pk])
        prefijo = f'ev{self.e.persona.pk}_{self.p09.pk}'
        resp = self.client.post(url, {f'{prefijo}-foto': SimpleUploadedFile('x.png', b'no es imagen')}, follow=True)
        self.assertContains(resp, 'Revisa la evidencia')
        self.assertFalse(Evidencia.objects.exists())
        self.client.force_login(self.general)
        self.client.post(url, {f'{prefijo}-verificacion_a': 'X'})
        self.assertFalse(Evidencia.objects.exists())


class FormulariosTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero)

    def test_04_1_clave_y_orden_en_el_paquete(self):
        p041 = PlantillaOficio.objects.get(numero=Decimal('4.1'))
        self.assertEqual(p041.clave, '04.1')
        plantillas = PlantillaOficio.objects.filter(numero__in=[Decimal('5'), Decimal('4.1'), Decimal('4')])
        oficios = servicio.crear_borradores(self.e.persona, plantillas, self.aero)
        self.assertEqual([o.plantilla.clave for o in servicio.ordenar_paquete(oficios)], ['04', '04.1', '05'])

    def test_03_notas_firmas_y_variables(self):
        p03 = PlantillaOficio.objects.get(numero=3)
        [o03] = servicio.crear_borradores(self.e.persona, [p03], self.aero)
        doc = _abrir(render_docx([pieza_de(o03)]))
        cuerpo = '\n'.join(p.text for p in doc.paragraphs)
        self.assertIn('Vuelo de arribo: HU7925', cuerpo)
        self.assertIn('Nombre: WANG PRUEBA', cuerpo)
        self.assertTrue(any(r.font.superscript for p in doc.paragraphs for r in p.runs if r.text == '1'))
        firmas = [t for t in doc.tables if 'Nombre completo y firma de la persona extranjera' in t.rows[0].cells[0].text]
        self.assertEqual(len(firmas), 1)
        self.assertIn('acompañado(a)', firmas[0].rows[0].cells[1].text)
        self.assertEqual(servicio.revisar(o03)[0], [])

    def test_04_en_chino_con_idioma_y_datos(self):
        self.e.persona.idioma = 'zh'
        self.e.persona.save()
        p04 = PlantillaOficio.objects.get(numero=4)
        [o04] = servicio.crear_borradores(self.e.persona, [p04], self.aero)
        self.assertEqual(o04.idioma, 'zh')
        doc = _abrir(render_docx([pieza_de(o04)]))
        datos = doc.tables[0]
        self.assertIn('WANG PRUEBA', datos.rows[1].cells[0].text)
        self.assertIn('INDIQUE EL IDIOMA / 语言: chino', '\n'.join(p.text for p in doc.paragraphs))
