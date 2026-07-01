from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL
from .models import EmpresaDirectorio, EstadoMexico, ResolucionChoices


class RolesPermisosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aeropuerto = User.objects.create_user('aero', password='x')
        cls.aeropuerto.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))
        cls.general = User.objects.create_user('gen', password='x')
        cls.general.groups.add(Group.objects.get(name=GRUPO_GENERAL))
        cls.admin = User.objects.create_superuser('root', password='x')

    def test_general_redirigido_de_flujo_principal(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('admin_list'))
        self.assertRedirects(resp, reverse('directorio:listado'),
                             fetch_redirect_response=False)

    def test_general_bloqueado_en_gestionar_cargas(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('batch_list'))
        self.assertRedirects(resp, reverse('directorio:listado'),
                             fetch_redirect_response=False)

    def test_aeropuerto_accede_flujo_principal(self):
        self.client.force_login(self.aeropuerto)
        self.assertEqual(self.client.get(reverse('admin_list')).status_code, 200)

    def test_todos_los_roles_acceden_directorio(self):
        for u in (self.general, self.aeropuerto, self.admin):
            self.client.force_login(u)
            self.assertEqual(self.client.get(reverse('directorio:listado')).status_code, 200)

    def test_general_no_puede_crear_usuarios(self):
        self.client.force_login(self.general)
        self.assertNotEqual(self.client.get(reverse('create_user')).status_code, 200)


class DedupDirectorioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('aero', password='x')
        cls.user.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))
        cls.estado = EstadoMexico.objects.first()

    def setUp(self):
        self.client.force_login(self.user)

    def _payload(self, **over):
        data = {
            'empresa': 'Alphacom',
            'domicilio': 'Calle 1',
            'estado': self.estado.id,
            'ciudad': 'Tijuana',
            'firma_encargado': 'Javier',
            'telefono': '6641234567',
            'tentativa_resolucion': ResolucionChoices.INTERNACION,
        }
        data.update(over)
        return data

    def test_alta_simple(self):
        self.client.post(reverse('directorio:crear'), self._payload())
        self.assertEqual(EmpresaDirectorio.objects.count(), 1)

    def test_duplicado_exacto_bloqueado(self):
        self.client.post(reverse('directorio:crear'), self._payload())
        self.client.post(reverse('directorio:crear'), self._payload())
        self.assertEqual(EmpresaDirectorio.objects.count(), 1)

    def test_misma_empresa_distinto_encargado_requiere_confirmacion(self):
        self.client.post(reverse('directorio:crear'), self._payload())
        # Sin confirmar: no se crea.
        self.client.post(reverse('directorio:crear'), self._payload(firma_encargado='Victoria'))
        self.assertEqual(EmpresaDirectorio.objects.count(), 1)
        # Confirmando: se crea el segundo registro válido.
        self.client.post(reverse('directorio:crear'),
                         self._payload(firma_encargado='Victoria', confirmar='1'))
        self.assertEqual(EmpresaDirectorio.objects.count(), 2)

    def test_busqueda_coincidencias(self):
        self.client.post(reverse('directorio:crear'), self._payload())
        resp = self.client.get(reverse('directorio:buscar_coincidencias'), {'empresa': 'Alpha'})
        self.assertEqual(len(resp.json()['resultados']), 1)
