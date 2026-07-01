import tempfile
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL
from .models import Pais, Redaccion, ResolucionChoices

MEDIA = tempfile.mkdtemp()


def _pdf(nombre='doc.pdf'):
    return SimpleUploadedFile(nombre, b'%PDF-1.4 test', content_type='application/pdf')


@override_settings(MEDIA_ROOT=MEDIA)
class RedaccionesPermisosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aeropuerto = User.objects.create_user('aero', password='x')
        cls.aeropuerto.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))
        cls.general = User.objects.create_user('gen', password='x')
        cls.general.groups.add(Group.objects.get(name=GRUPO_GENERAL))
        cls.pais = Pais.objects.first()

    def _payload(self, **over):
        data = {
            'titulo': 'Acta modelo',
            'resolucion': ResolucionChoices.RECHAZO,
            'tema': 'Documentación falsa',
            'pais': self.pais.id,
            'archivo': _pdf(),
        }
        data.update(over)
        return data

    def test_general_no_puede_abrir_subir(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('redacciones:subir'))
        self.assertRedirects(resp, reverse('redacciones:biblioteca'),
                             fetch_redirect_response=False)

    def test_general_no_puede_subir_post(self):
        self.client.force_login(self.general)
        self.client.post(reverse('redacciones:subir'), self._payload())
        self.assertEqual(Redaccion.objects.count(), 0)

    def test_aeropuerto_sube_pdf_con_preview(self):
        self.client.force_login(self.aeropuerto)
        self.client.post(reverse('redacciones:subir'), self._payload())
        self.assertEqual(Redaccion.objects.count(), 1)
        doc = Redaccion.objects.first()
        self.assertTrue(doc.es_pdf)
        self.assertIsNotNone(doc.preview_url)

    def test_general_consulta_y_descarga(self):
        self.client.force_login(self.aeropuerto)
        self.client.post(reverse('redacciones:subir'), self._payload())
        doc = Redaccion.objects.first()
        self.client.force_login(self.general)
        self.assertEqual(self.client.get(reverse('redacciones:biblioteca')).status_code, 200)
        self.assertEqual(self.client.get(reverse('redacciones:detalle', args=[doc.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('redacciones:descargar', args=[doc.pk])).status_code, 200)

    def test_preview_embebible_sameorigin(self):
        self.client.force_login(self.aeropuerto)
        self.client.post(reverse('redacciones:subir'), self._payload())
        doc = Redaccion.objects.first()
        self.client.force_login(self.general)
        resp = self.client.get(reverse('redacciones:preview', args=[doc.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_extension_invalida_rechazada(self):
        self.client.force_login(self.aeropuerto)
        bad = SimpleUploadedFile('x.txt', b'hola', content_type='text/plain')
        self.client.post(reverse('redacciones:subir'), self._payload(archivo=bad))
        self.assertEqual(Redaccion.objects.count(), 0)

    def test_word_sin_libreoffice_degrada_a_descarga(self):
        self.client.force_login(self.aeropuerto)
        docx = SimpleUploadedFile(
            'acta.docx', b'PKfake',
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        with mock.patch('apps.redacciones.views.generar_preview', return_value=False):
            self.client.post(reverse('redacciones:subir'), self._payload(archivo=docx))
        doc = Redaccion.objects.first()
        self.assertFalse(doc.es_pdf)
        self.assertFalse(bool(doc.archivo_pdf))
        self.assertIsNone(doc.preview_url)


@override_settings(MEDIA_ROOT=MEDIA)
class RedaccionesFiltrosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser('root2', password='x')
        paises = list(Pais.objects.all()[:2])
        cls.p1, cls.p2 = paises[0], paises[1]
        cls._make('Acta A', ResolucionChoices.RECHAZO, 'DOCUMENTACION FALSA', cls.p1)
        cls._make('Acta B', ResolucionChoices.INTERNACION, 'ENTREVISTA', cls.p2)
        cls._make('Acta C', ResolucionChoices.RECHAZO, 'ENTREVISTA', cls.p2)

    @staticmethod
    def _make(titulo, resolucion, tema, pais):
        return Redaccion.objects.create(
            titulo=titulo, resolucion=resolucion, tema=tema, pais=pais,
            archivo=_pdf(titulo + '.pdf'),
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_filtro_resolucion(self):
        resp = self.client.get(reverse('redacciones:biblioteca'), {'resolucion': 'RECHAZO'})
        self.assertEqual(resp.context['total'], 2)

    def test_filtro_combinado_resolucion_pais(self):
        resp = self.client.get(reverse('redacciones:biblioteca'),
                               {'resolucion': 'RECHAZO', 'pais': self.p2.id})
        self.assertEqual(resp.context['total'], 1)  # Acta C

    def test_filtro_tema(self):
        resp = self.client.get(reverse('redacciones:biblioteca'), {'tema': 'entrevista'})
        self.assertEqual(resp.context['total'], 2)
