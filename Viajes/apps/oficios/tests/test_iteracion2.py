"""Iteración 2: recuadro, cargo sin nivel, gentilicios, plantilla 07, firmas de empresa y paquete."""
import datetime
import io
from unittest import mock

from docx import Document
from docx.shared import Cm
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from ..gentilicios import gentilicio
from ..models import Expediente, MotivoRechazo, OficioInstancia, PersonaExpediente, PlantillaOficio
from ..services import expedientes as servicio
from ..services.contexto import cargo_impreso, contexto_para
from ..services.docx_oficio import Pieza, pieza_de, render_docx
from ..services.html_docx import EscritorHTML
from .utils import Escenario, MediaTemporalMixin, registro, usuarios

DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def _abrir(docx_bytes):
    return Document(io.BytesIO(docx_bytes))


class RecuadroTests(SimpleTestCase):

    def _escribir(self, html):
        document = Document()
        EscritorHTML(document, Cm(18.41)).escribir(html)
        return document

    def test_parrafos_dentro_del_recuadro(self):
        doc = self._escribir(
            '<p>Antes</p><p>[[ RECUADRO ]]</p><p class="ql-align-center"><strong>Título</strong></p>'
            '<p>Texto del recuadro --</p><p>[[ /RECUADRO ]]</p><p>Después</p>'
        )
        self.assertEqual([p.text for p in doc.paragraphs], ['Antes', 'Después'])
        [tabla] = doc.tables
        self.assertEqual(tabla.style.name, 'Table Grid')
        celda = tabla.rows[0].cells[0]
        # Sin el renglón vacío con el que nace la celda; el relleno también funciona adentro.
        self.assertEqual([p.text for p in celda.paragraphs], ['Título', 'Texto del recuadro\t\u200b'])

    def test_sin_cerrar_llega_al_final_y_cierre_suelto_no_se_imprime(self):
        doc = self._escribir('<p>[[ /RECUADRO ]]</p><p>A</p><p>[[ recuadro ]]</p><p>B</p>')
        self.assertEqual([p.text for p in doc.paragraphs], ['A'])
        self.assertEqual(doc.tables[0].rows[0].cells[0].text, 'B')


class CargoYGentilicioTests(TestCase):

    def test_cargo_sin_nivel(self):
        casos = {
            'AGENTE FEDERAL DE MIGRACIÓN "B"': 'AGENTE FEDERAL DE MIGRACIÓN',
            'AGENTE FEDERAL DE MIGRACIÓN A': 'AGENTE FEDERAL DE MIGRACIÓN',
            'TÉCNICO OPERATIVO C': 'TÉCNICO OPERATIVO',
            'JEFA DE DEPARTAMENTO': 'JEFA DE DEPARTAMENTO',
            'SUBDIRECTORA DE ÁREA': 'SUBDIRECTORA DE ÁREA',
            '': '',
        }
        for cargo, esperado in casos.items():
            with self.subTest(cargo=cargo):
                self.assertEqual(cargo_impreso(cargo), esperado)

    def test_testigo_se_imprime_sin_nivel(self):
        e = Escenario()
        e.testigo_1.plaza = 'AGENTE FEDERAL DE MIGRACIÓN "B"'
        e.testigo_1.save()
        oficio = OficioInstancia.objects.create(persona=e.persona, plantilla=e.p02)
        self.assertEqual(contexto_para(oficio)['testigo1_cargo'], 'AGENTE FEDERAL DE MIGRACIÓN')

    def test_gentilicio(self):
        self.assertEqual((gentilicio('CHN'), gentilicio('cn'), gentilicio('RUS'), gentilicio('HKG')),
                         ('china', 'china', 'rusa', 'china'))
        self.assertEqual(gentilicio('ZZZ'), '')

    def test_precarga_sin_gentilicio_usa_el_pais(self):
        aero, _ = usuarios()
        r = registro(aero, 'NORUEGO PRUEBA', codigo='NOR', pais='NORWAY')
        self.assertEqual(servicio.datos_desde_registro(r)['nacionalidad'], 'Noruega')


class Plantilla07Tests(TestCase):

    def test_sembrada_sin_fecha_bajo_el_titulo(self):
        p07 = PlantillaOficio.objects.get(numero=7)
        self.assertFalse(p07.lleva_fecha)
        e = Escenario()
        oficio = OficioInstancia.objects.create(persona=e.persona, plantilla=p07, contenido_html=p07.contenido_html,
                                                fecha_oficio=datetime.date(2026, 11, 25))
        textos = [p.text for p in _abrir(render_docx([pieza_de(oficio)])).paragraphs]
        self.assertEqual(textos[5], 'CONSTANCIA DE LLAMADA CONSULAR')
        self.assertTrue(textos[6].startswith('En Tijuana, Baja California, siendo el día 25 de noviembre de 2026, '
                                             'la que suscribe LIC. MELISSA GALLEGOS, JEFA DE DEPARTAMENTO adscrita'))
        self.assertIn('\t SE CIERRA Y SE AUTORIZA LO ACTUADO \t\u200b', textos)
        self.assertIn('\t\u200b', textos)  # la línea completa de guiones
        self.assertTrue(any('REALIZARLA: ☐' in t for t in textos))

    def test_11_lleva_recuadro(self):
        self.assertIn('[[ RECUADRO ]]', PlantillaOficio.objects.get(numero=11).contenido_html)


class FirmasEmpresaYFormatoCongeladoTests(MediaTemporalMixin, TestCase):

    def test_bloque_empresa(self):
        pieza = Pieza(titulo='T', cuerpo_html='<p>x</p>', bloque_firmas='EMPRESA', lleva_fecha=False,
                      contexto={'firmante_nombre': 'LIC. A', 'firmante_cargo': 'JEFA DE DEPARTAMENTO'})
        [tabla] = _abrir(render_docx([pieza])).tables
        izquierda, derecha = tabla.rows[0].cells
        self.assertIn('NOMBRE Y FIRMA DEL REPRESENTANTE DE LA EMPRESA TRANSPORTISTA', izquierda.text)
        self.assertIn('LA AUTORIDAD MIGRATORIA', derecha.text)
        self.assertIn('LIC. A', derecha.text)

    def test_impreso_conserva_titulo_y_firmas_aunque_cambie_la_plantilla(self):
        aero, _ = usuarios()
        e = Escenario(aero)
        [oficio] = servicio.crear_borradores(e.persona, [e.p02], aero)
        servicio.imprimir(oficio, aero)
        e.p02.titulo = 'OTRO TÍTULO'
        e.p02.bloque_firmas = 'NINGUNO'
        e.p02.save()
        oficio = OficioInstancia.objects.get(pk=oficio.pk)
        pieza = pieza_de(oficio)
        self.assertEqual((pieza.titulo, pieza.bloque_firmas),
                         ('CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO', 'CONSTANCIA'))
        servicio.reabrir(oficio, aero, 'corregir')
        oficio.refresh_from_db()
        self.assertIsNone(oficio.snap_formato)
        self.assertEqual(pieza_de(oficio).titulo, 'OTRO TÍTULO')


class FamiliaYPaqueteServicioTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero)
        self.hija = PersonaExpediente.objects.create(expediente=self.e.expediente, nombre='HIJA PRUEBA', orden=2)
        self.p07 = PlantillaOficio.objects.get(numero=7)

    def test_borradores_para_toda_la_familia_sin_duplicar(self):
        servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        creados = servicio.crear_borradores_familia(self.e.expediente, [self.e.p02, self.p07], self.aero)
        self.assertEqual(creados, 3)  # persona: 07; hija: 02 y 07
        self.assertEqual(OficioInstancia.objects.count(), 4)

    def test_orden_y_paquete(self):
        servicio.crear_borradores_familia(self.e.expediente, [self.e.p11, self.p07, self.e.p02], self.aero)
        oficios = list(OficioInstancia.objects.order_by('-pk'))
        ordenados = servicio.ordenar_paquete(oficios)
        self.assertEqual([(o.persona.nombre, o.plantilla.numero) for o in ordenados], [
            ('WANG PRUEBA', 2), ('WANG PRUEBA', 7), ('WANG PRUEBA', 11),
            ('HIJA PRUEBA', 2), ('HIJA PRUEBA', 7), ('HIJA PRUEBA', 11),
        ])
        documento = _abrir(servicio.render_paquete(oficios))
        self.assertEqual(len(documento.sections), 6)
        titulos = [p.text for p in documento.paragraphs if p.text in (
            'CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO', 'CONSTANCIA DE LLAMADA CONSULAR',
            'NOTIFICACIÓN DE RESOLUCIÓN DE RECHAZO AÉREO')]
        self.assertEqual(len(titulos), 6)
        self.assertEqual(servicio.nombre_paquete(self.e.expediente, oficios, 'pdf'), f'{self.e.expediente.folio}_paquete.pdf')
        solo_hija = [o for o in oficios if o.persona_id == self.hija.pk]
        self.assertEqual(servicio.nombre_paquete(self.e.expediente, solo_hija, 'docx'),
                         f'{self.e.expediente.folio}_HIJA_PRUEBA_paquete.docx')

    def test_imprimir_varios_reporta_errores(self):
        self.e.persona.motivo_rechazo = MotivoRechazo.objects.first()
        self.e.persona.save()
        servicio.crear_borradores_familia(self.e.expediente, [self.e.p02, self.e.p11], self.aero)
        self.e.expediente.testigo_2 = None  # el 02 pide testigos; el 11 no
        self.e.expediente.save()
        oficios = list(OficioInstancia.objects.all())
        impresos, errores = servicio.imprimir_varios(oficios, self.aero)
        self.assertEqual(sorted(o.plantilla.numero for o in impresos), [11, 11])
        self.assertEqual(len(errores), 2)
        self.assertIn('testigos', errores[0][1])
        # Los ya impresos se saltan.
        self.assertEqual(servicio.imprimir_varios(impresos, self.aero), ([], []))


class PaqueteVistasTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, self.general = usuarios()
        self.client.force_login(self.aero)
        self.e = Escenario(self.aero)
        self.e.expediente.resultado = Expediente.Resultado.RECHAZO
        self.e.expediente.save()
        self.url = reverse('oficios:paquete', args=[self.e.expediente.pk])

    def test_detalle_preselecciona_por_resultado_y_crea_para_la_familia(self):
        resp = self.client.get(reverse('oficios:detalle', args=[self.e.expediente.pk]))
        marcados = {p.numero for p, sugerido in resp.context['plantillas_familia'] if sugerido}
        self.assertEqual(marcados, {2, 3, 4, 5, 7, 8, 9, 11, 13, 14})  # lo que lleva un rechazo
        self.assertNotContains(resp, 'Paquete para imprimir')  # todavía no hay oficios
        self.client.post(reverse('oficios:crear_borradores_familia', args=[self.e.expediente.pk]),
                         {'plantillas': [self.e.p02.pk, self.e.p11.pk]})
        self.assertEqual(self.e.persona.oficios.count(), 2)
        self.assertContains(self.client.get(reverse('oficios:detalle', args=[self.e.expediente.pk])), 'Paquete para imprimir')

    def test_paquete_word_pdf_e_imprimir(self):
        o02, o11 = servicio.crear_borradores(self.e.persona, [self.e.p02, self.e.p11], self.aero)
        # Un oficio de OTRO expediente no debe colarse aunque venga en el POST.
        otro_exp = Expediente.objects.create()
        otra = PersonaExpediente.objects.create(expediente=otro_exp, nombre='AJENA')
        ajeno = OficioInstancia.objects.create(persona=otra, plantilla=self.e.p02)

        resp = self.client.get(self.url)
        self.assertContains(resp, '02. Constancia de uso de traductor electrónico')
        self.assertNotContains(resp, 'AJENA')

        resp = self.client.post(self.url, {'oficios': [o02.pk, o11.pk, ajeno.pk], 'accion': 'word'})
        self.assertEqual(resp['Content-Type'], DOCX)
        self.assertIn('_WANG_PRUEBA_paquete.docx', resp['Content-Disposition'])
        self.assertEqual(len(_abrir(resp.content).sections), 2)

        with mock.patch('apps.oficios.views.docx_a_pdf', return_value=b'%PDF-paquete'):
            resp = self.client.post(self.url, {'oficios': [o02.pk], 'accion': 'pdf'})
        self.assertEqual(resp.content, b'%PDF-paquete')

        with mock.patch('apps.oficios.views.docx_a_pdf', return_value=None):
            resp = self.client.post(self.url, {'oficios': [o02.pk], 'accion': 'pdf'}, follow=True)
        self.assertContains(resp, 'No se pudo generar el PDF')

        # El 11 sin motivo solo es un aviso (sale en blanco): se imprime igual.
        resp = self.client.post(self.url, {'oficios': [o02.pk, o11.pk, ajeno.pk], 'accion': 'imprimir'}, follow=True)
        self.assertContains(resp, '2 oficio(s) marcados como impresos.')
        self.assertEqual(set(OficioInstancia.objects.filter(estado='IMPRESO').values_list('pk', flat=True)),
                         {o02.pk, o11.pk})
        resp = self.client.post(self.url, {'oficios': [o02.pk], 'accion': 'imprimir'}, follow=True)
        self.assertContains(resp, 'ya estaban impresos')

    def test_sin_eleccion_y_permisos(self):
        resp = self.client.post(self.url, {'accion': 'word'}, follow=True)
        self.assertContains(resp, 'Elige al menos un oficio.')
        self.client.force_login(self.general)
        self.assertRedirects(self.client.get(self.url), reverse('directorio:listado'), fetch_redirect_response=False)
