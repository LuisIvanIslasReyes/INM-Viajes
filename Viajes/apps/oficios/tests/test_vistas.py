import shutil
from unittest import mock, skipUnless

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ..models import Expediente, OficioInstancia, PersonaExpediente, PlantillaOficio
from ..services import expedientes as servicio
from .utils import Escenario, MediaTemporalMixin, empleado, registro, usuarios

DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


class PermisosTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aero, cls.general = usuarios()
        cls.e = Escenario(cls.aero)
        cls.oficio = OficioInstancia.objects.create(persona=cls.e.persona, plantilla=cls.e.p02)

    def test_general_y_anonimo_no_entran(self):
        urls = [reverse('oficios:lista'), reverse('oficios:nuevo'), reverse('oficios:detalle', args=[self.e.expediente.pk]),
                reverse('oficios:oficio', args=[self.oficio.pk]), reverse('oficios:plantillas')]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)  # anónimo → login
        self.client.force_login(self.general)
        for url in urls:
            with self.subTest(url=url, rol='general'):
                self.assertRedirects(self.client.get(url), reverse('directorio:listado'), fetch_redirect_response=False)

    def test_acciones_solo_post(self):
        self.client.force_login(self.aero)
        for nombre in ['oficio_imprimir', 'oficio_reabrir', 'oficio_eliminar']:
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(f'oficios:{nombre}', args=[self.oficio.pk])).status_code, 405)

    def test_menu_muestra_oficios_solo_al_flujo_principal(self):
        self.client.force_login(self.aero)
        self.assertContains(self.client.get(reverse('oficios:lista')), 'href="/oficios/"')
        self.client.force_login(self.general)
        self.assertNotContains(self.client.get(reverse('directorio:listado')), 'href="/oficios/"')


class ExpedienteVistasTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aero, _ = usuarios()

    def setUp(self):
        self.client.force_login(self.aero)

    def test_buscar_y_crear_desde_el_vuelo(self):
        marcado = registro(self.aero, 'ZHANG WEI PRUEBA', r=True)
        registro(self.aero, 'SIN MARCAS PRUEBA', sr=False)
        resp = self.client.get(reverse('oficios:nuevo'), {'q': 'prueba'})
        self.assertEqual([r.pk for r in resp.context['registros']], [marcado.pk])  # solo SR/R por defecto
        resp = self.client.get(reverse('oficios:nuevo'), {'q': 'prueba', 'buscar': '1'})  # sin la casilla
        self.assertEqual(len(resp.context['registros']), 2)

        resp = self.client.post(reverse('oficios:nuevo'), {'registros': [marcado.pk]})
        exp = Expediente.objects.get()
        self.assertRedirects(resp, reverse('oficios:detalle', args=[exp.pk]), fetch_redirect_response=False)
        self.assertEqual(exp.personas.get().nombre, 'ZHANG WEI PRUEBA')

    def test_sin_elegir_no_crea_salvo_vacio(self):
        self.client.post(reverse('oficios:nuevo'), {})
        self.assertFalse(Expediente.objects.exists())
        self.client.post(reverse('oficios:nuevo'), {'accion': 'vacio'})
        self.assertEqual(Expediente.objects.get().personas.count(), 0)

    def test_agregar_al_existente(self):
        exp = servicio.crear_expediente(self.aero, [])
        r = registro(self.aero, 'NUEVO PRUEBA')
        resp = self.client.post(reverse('oficios:nuevo'), {'expediente': exp.pk, 'registros': [r.pk]})
        self.assertRedirects(resp, reverse('oficios:detalle', args=[exp.pk]), fetch_redirect_response=False)
        self.assertEqual(exp.personas.get().nombre, 'NUEVO PRUEBA')

    def test_firmas(self):
        e = Escenario(self.aero)
        url = reverse('oficios:guardar_firmas', args=[e.expediente.pk])
        otro = empleado(20, 'OTRO', 'FIRMANTE', plaza='REPRESENTANTE LOCAL')
        self.client.post(url, {'firmante': otro.pk, 'testigo_1': e.testigo_1.pk, 'testigo_2': e.testigo_2.pk,
                               'resultado': 'INTERNACION'})
        e.expediente.refresh_from_db()
        self.assertEqual((e.expediente.firmante, e.expediente.resultado), (otro, 'INTERNACION'))

        resp = self.client.post(url, {'firmante': otro.pk, 'testigo_1': otro.pk, 'testigo_2': '', 'resultado': 'RECHAZO'})
        self.assertContains(resp, 'deben ser personas distintas')
        e.expediente.refresh_from_db()
        self.assertEqual(e.expediente.testigo_1, e.testigo_1)

    def test_detalle_muestra_fundamento_y_formatos(self):
        e = Escenario(self.aero)
        resp = self.client.get(reverse('oficios:detalle', args=[e.expediente.pk]))
        self.assertContains(resp, 'Fundamento: Artículo 23, fracciones I, II, III y IV')
        self.assertContains(resp, '02. Constancia de uso de traductor electrónico')
        self.assertNotContains(resp, '{#')  # ningún comentario de plantilla se cuela

    def test_personas_a_mano_editar_y_quitar(self):
        e = Escenario(self.aero)
        resp = self.client.post(reverse('oficios:agregar_persona', args=[e.expediente.pk]), {
            'nueva-nombre': 'CAPTURADA A MANO', 'nueva-idioma': 'fr', 'nueva-fecha_nacimiento': '2001-02-03',
        })
        self.assertEqual(resp.status_code, 302)
        nueva = PersonaExpediente.objects.get(nombre='CAPTURADA A MANO')
        self.assertEqual((nueva.idioma, nueva.orden, nueva.registro), ('fr', 2, None))

        prefijo = f'p{nueva.pk}'
        self.client.post(reverse('oficios:editar_persona', args=[nueva.pk]), {
            f'{prefijo}-nombre': 'CORREGIDA', f'{prefijo}-idioma': 'es', f'{prefijo}-nacionalidad': 'francesa',
        })
        nueva.refresh_from_db()
        self.assertEqual((nueva.nombre, nueva.nacionalidad), ('CORREGIDA', 'francesa'))

        resp = self.client.post(reverse('oficios:editar_persona', args=[nueva.pk]), {f'{prefijo}-nombre': ''})
        self.assertEqual(resp.status_code, 200)  # sin nombre no guarda

        self.client.post(reverse('oficios:quitar_persona', args=[nueva.pk]))
        self.assertFalse(PersonaExpediente.objects.filter(pk=nueva.pk).exists())

    def test_crear_borradores(self):
        e = Escenario(self.aero)
        url = reverse('oficios:crear_borradores', args=[e.persona.pk])
        self.client.post(url, {'plantillas': [e.p02.pk, e.p11.pk]})
        self.assertEqual(sorted(e.persona.oficios.values_list('plantilla__numero', flat=True)), [2, 11])
        e.p02.activo = False
        e.p02.save()
        e.persona.oficios.all().delete()
        self.client.post(url, {'plantillas': [e.p02.pk]})  # inactiva: no se crea
        self.assertFalse(e.persona.oficios.exists())


class OficioVistasTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.client.force_login(self.aero)
        self.e = Escenario(self.aero)
        [self.oficio] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        self.url = reverse('oficios:oficio', args=[self.oficio.pk])

    def test_pantalla_del_editor(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, 'oficios/vendor/quill/quill.js')
        self.assertContains(resp, 'id="contenido-inicial"')
        self.assertContains(resp, '{{firmante_fundamento}}')  # panel de variables
        self.assertContains(resp, 'Marcar como impreso')

    def test_guardar(self):
        resp = self.client.post(self.url, {
            'contenido_html': '<p>Texto <strong>nuevo</strong> {{extranjero_nombre}}</p><script>x</script>',
            'fecha_oficio': '2026-11-20', 'testigo_1': '', 'testigo_2': self.e.firmante.pk,
        })
        self.assertRedirects(resp, self.url, fetch_redirect_response=False)
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.contenido_html, '<p>Texto <strong>nuevo</strong> {{extranjero_nombre}}</p>')
        self.assertEqual(str(self.oficio.fecha_oficio), '2026-11-20')
        self.assertEqual(self.oficio.testigo_2, self.e.firmante)

    def test_imprimir_reabrir_y_descargas(self):
        resp = self.client.post(reverse('oficios:oficio_imprimir', args=[self.oficio.pk]), follow=True)
        self.assertContains(resp, 'congelado tal como se imprimió')
        self.assertContains(resp, 'Reabrir como borrador')
        self.assertContains(resp, 'data-solo-lectura="1"')

        # Congelado: un POST de guardado no cambia nada.
        self.client.post(self.url, {'contenido_html': '<p>otro</p>', 'fecha_oficio': '2026-11-20'})
        self.oficio.refresh_from_db()
        self.assertNotEqual(self.oficio.contenido_html, '<p>otro</p>')

        resp = self.client.get(reverse('oficios:oficio_docx', args=[self.oficio.pk]))
        self.assertEqual(resp['Content-Type'], DOCX)
        self.assertIn('attachment; filename="VJ-', resp['Content-Disposition'])

        with mock.patch('apps.oficios.views.docx_a_pdf', return_value=b'%PDF-1.7'):
            resp = self.client.get(reverse('oficios:oficio_pdf', args=[self.oficio.pk]), {'inline': '1'})
        self.assertEqual((resp['Content-Type'], resp.content), ('application/pdf', b'%PDF-1.7'))
        self.assertTrue(resp['Content-Disposition'].startswith('inline;'))

        self.client.post(reverse('oficios:oficio_reabrir', args=[self.oficio.pk]), {'motivo': 'Corregir sala'})
        self.oficio.refresh_from_db()
        self.assertTrue(self.oficio.editable)

    def test_imprimir_con_errores_avisa(self):
        self.e.expediente.firmante = None
        self.e.expediente.save()
        resp = self.client.post(reverse('oficios:oficio_imprimir', args=[self.oficio.pk]), follow=True)
        self.assertContains(resp, 'Falta el firmante del expediente.')
        self.oficio.refresh_from_db()
        self.assertTrue(self.oficio.editable)

    def test_pdf_sin_libreoffice_regresa_al_oficio(self):
        with mock.patch('apps.oficios.views.docx_a_pdf', return_value=None):
            resp = self.client.get(reverse('oficios:oficio_pdf', args=[self.oficio.pk]), follow=True)
        self.assertContains(resp, 'No se pudo generar el PDF')

    def test_eliminar_solo_borradores(self):
        servicio.imprimir(self.oficio, self.aero)
        self.client.post(reverse('oficios:oficio_eliminar', args=[self.oficio.pk]))
        self.assertTrue(OficioInstancia.objects.filter(pk=self.oficio.pk).exists())
        servicio.reabrir(self.oficio, self.aero, 'x')
        self.client.post(reverse('oficios:oficio_eliminar', args=[self.oficio.pk]))
        self.assertFalse(OficioInstancia.objects.filter(pk=self.oficio.pk).exists())

    def test_no_se_quita_persona_con_impresos(self):
        servicio.imprimir(self.oficio, self.aero)
        resp = self.client.post(reverse('oficios:quitar_persona', args=[self.e.persona.pk]), follow=True)
        self.assertContains(resp, 'ya tiene oficios impresos')
        self.assertTrue(PersonaExpediente.objects.filter(pk=self.e.persona.pk).exists())

    def test_editar_plantilla(self):
        plantilla = PlantillaOficio.objects.get(numero=11)
        url = reverse('oficios:plantilla_editar', args=[plantilla.pk])
        self.assertContains(self.client.get(url), 'Guardar plantilla')
        self.client.post(url, {
            'nombre': plantilla.nombre, 'titulo': 'TÍTULO NUEVO', 'bloque_firmas': 'NOTIFICACION', 'tamano_letra_pt': '10',
            'lleva_fecha': 'on', 'activo': 'on', 'contenido_html': '<p onclick="x">Base {{vuelo}}</p>',
        })
        plantilla.refresh_from_db()
        self.assertEqual((plantilla.titulo, plantilla.contenido_html, plantilla.modificado_por),
                         ('TÍTULO NUEVO', '<p>Base {{vuelo}}</p>', self.aero))


@skipUnless(shutil.which(getattr(settings, 'SOFFICE_BIN', 'soffice')), 'LibreOffice no está instalado')
class PdfRealTests(TestCase):
    """Conversión real con LibreOffice (se salta donde no esté instalado)."""

    def test_pdf_de_un_oficio(self):
        from ..services.docx_oficio import pieza_de, render_docx
        from ..services.pdf import docx_a_pdf
        e = Escenario()
        oficio = OficioInstancia.objects.create(persona=e.persona, plantilla=e.p02, contenido_html=e.p02.contenido_html)
        pdf = docx_a_pdf(render_docx([pieza_de(oficio)]))
        self.assertIsNotNone(pdf)
        self.assertTrue(pdf.startswith(b'%PDF'))
