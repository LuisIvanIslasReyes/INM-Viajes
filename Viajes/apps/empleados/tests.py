"""
Tests de la réplica de empleados. No salen a la red: `urlopen` se simula con
respuestas con la misma forma que el endpoint de integración de la Estancia.

    python manage.py test apps.empleados --settings=Viajes.settings.test
"""
import io
import json
import urllib.error
from contextlib import contextmanager
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL

from .models import Empleado, SincronizacionEmpleados
from .services import ErrorSincronizacion, aplicar_empleados, descargar_empleados, sincronizar

URL_ESTANCIA = 'http://estancia.test/api/v1/personal/integracion/empleados/'
CONFIG = {'ESTANCIA_EMPLEADOS_URL': URL_ESTANCIA, 'ESTANCIA_API_KEY': 'clave-viajes'}
URLOPEN = 'apps.empleados.services.urllib.request.urlopen'


def fila(id_empleado, numero, nombres, apellidos, **extra):
    datos = {
        'id_empleado': id_empleado, 'employee_number': numero, 'academic_title': '',
        'nombres': nombres, 'apellidos': apellidos,
        'nombre_completo': f'{nombres} {apellidos}', 'sexo': '', 'estado_actual': 'ACTIVO',
        'plaza': '', 'jerarquia': '', 'municipio_id': 1, 'municipio': 'Tijuana',
        'fecha_modificacion': '2026-11-20T10:00:00-08:00',
    }
    datos.update(extra)
    return datos


MELISSA = fila(10, '1001', 'MELISSA', 'GALLEGOS', academic_title='LIC', sexo='F',
               jerarquia='JEFE DE DEPARTAMENTO', plaza='AGENTE FEDERAL DE MIGRACION B')
CARLOS = fila(11, '1002', 'CARLOS', 'TELLO', sexo='M', municipio_id=2, municipio='Mexicali')
LEGACY = fila(12, None, 'SIN', 'NUMERO', municipio_id=None, municipio='')


def respuesta(paginas):
    """Simula `urlopen`: devuelve la página pedida (`page=N`) de `paginas`."""
    llamadas = []

    @contextmanager
    def _urlopen(req, timeout=None, context=None):
        llamadas.append(req)
        pagina = int(req.full_url.split('page=')[1].split('&')[0])
        resultados = paginas[pagina - 1]
        siguiente = 'otra' if pagina < len(paginas) else None
        yield io.BytesIO(json.dumps({'count': 0, 'next': siguiente, 'results': resultados}).encode())

    return _urlopen, llamadas


@override_settings(**CONFIG)
class DescargaTests(TestCase):

    def test_sin_configuracion(self):
        with override_settings(ESTANCIA_EMPLEADOS_URL='', ESTANCIA_API_KEY=''):
            with self.assertRaisesMessage(ErrorSincronizacion, 'Falta configurar'):
                descargar_empleados()

    def test_paginado_y_headers(self):
        fake, llamadas = respuesta([[MELISSA, CARLOS], [LEGACY]])
        with mock.patch(URLOPEN, fake):
            filas = descargar_empleados()
        self.assertEqual([f['id_empleado'] for f in filas], [10, 11, 12])
        self.assertEqual(len(llamadas), 2)
        self.assertEqual(llamadas[0].get_header('X-api-key'), 'clave-viajes')
        self.assertIn('incluir_bajas=1', llamadas[0].full_url)
        self.assertTrue(llamadas[0].full_url.startswith(URL_ESTANCIA))

    def test_api_key_rechazada(self):
        error = urllib.error.HTTPError(URL_ESTANCIA, 401, 'Unauthorized', {}, None)
        with mock.patch(URLOPEN, side_effect=error):
            with self.assertRaisesMessage(ErrorSincronizacion, 'API key'):
                descargar_empleados()

    def test_estancia_apagada(self):
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError('timed out')):
            with self.assertRaisesMessage(ErrorSincronizacion, 'No se pudo conectar'):
                descargar_empleados()

    def test_respuesta_invalida(self):
        @contextmanager
        def html(req, timeout=None, context=None):
            yield io.BytesIO(b'<html>login</html>')
        with mock.patch(URLOPEN, html):
            with self.assertRaisesMessage(ErrorSincronizacion, 'JSON'):
                descargar_empleados()


class AplicarTests(TestCase):

    def test_crea_con_campos_mapeados(self):
        self.assertEqual(aplicar_empleados([MELISSA, CARLOS, LEGACY]), (3, 0, 0))
        m = Empleado.objects.get(id_estancia=10)
        self.assertEqual(m.numero_empleado, '1001')
        self.assertEqual(m.cargo, 'JEFE DE DEPARTAMENTO')
        self.assertEqual(m.nombre_para_oficio, 'LIC. MELISSA GALLEGOS')
        self.assertTrue(m.activo)
        legacy = Empleado.objects.get(id_estancia=12)
        self.assertEqual(legacy.numero_empleado, '')
        self.assertIsNone(legacy.municipio_id_estancia)

    def test_sin_cambios_no_cuenta_como_actualizado(self):
        aplicar_empleados([MELISSA, CARLOS])
        self.assertEqual(aplicar_empleados([MELISSA, CARLOS]), (0, 0, 0))

    def test_actualiza_y_conserva_firmante_habitual(self):
        aplicar_empleados([MELISSA])
        Empleado.objects.filter(id_estancia=10).update(firmante_habitual=True)
        cambio = dict(MELISSA, jerarquia='SUBDIRECTORA')
        self.assertEqual(aplicar_empleados([cambio]), (0, 1, 0))
        m = Empleado.objects.get(id_estancia=10)
        self.assertEqual(m.cargo, 'SUBDIRECTORA')
        self.assertTrue(m.firmante_habitual)

    def test_baja_queda_inactivo(self):
        aplicar_empleados([MELISSA, CARLOS])
        aplicar_empleados([MELISSA, dict(CARLOS, estado_actual='BAJA')])
        self.assertFalse(Empleado.objects.get(id_estancia=11).activo)

    def test_ausente_se_desactiva_sin_borrar(self):
        aplicar_empleados([MELISSA, CARLOS])
        self.assertEqual(aplicar_empleados([MELISSA]), (0, 0, 1))
        self.assertFalse(Empleado.objects.get(id_estancia=11).activo)
        self.assertEqual(Empleado.objects.count(), 2)

    def test_reaparece_se_reactiva(self):
        aplicar_empleados([MELISSA, CARLOS])
        aplicar_empleados([MELISSA])
        aplicar_empleados([MELISSA, CARLOS])
        self.assertTrue(Empleado.objects.get(id_estancia=11).activo)


@override_settings(**CONFIG)
class SincronizarTests(TestCase):

    def test_exitosa_deja_registro(self):
        fake, _ = respuesta([[MELISSA, CARLOS]])
        with mock.patch(URLOPEN, fake):
            r = sincronizar()
        self.assertTrue(r.exitosa)
        self.assertEqual((r.recibidos, r.creados), (2, 2))
        self.assertIsNotNone(r.terminada_en)

    def test_fallo_no_toca_la_replica(self):
        aplicar_empleados([MELISSA, CARLOS])
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError('apagón')):
            with self.assertRaises(ErrorSincronizacion):
                sincronizar()
        self.assertEqual(Empleado.objects.filter(activo=True).count(), 2)
        r = SincronizacionEmpleados.objects.first()
        self.assertFalse(r.exitosa)
        self.assertIn('apagón', r.error)

    def test_cero_empleados_no_desactiva_a_todos(self):
        aplicar_empleados([MELISSA, CARLOS])
        fake, _ = respuesta([[]])
        with mock.patch(URLOPEN, fake):
            with self.assertRaisesMessage(ErrorSincronizacion, '0 empleados'):
                sincronizar()
        self.assertEqual(Empleado.objects.filter(activo=True).count(), 2)

    def test_comando(self):
        fake, _ = respuesta([[MELISSA]])
        salida = io.StringIO()
        with mock.patch(URLOPEN, fake):
            call_command('sincronizar_empleados', stdout=salida)
        self.assertIn('recibidos 1', salida.getvalue())

    def test_comando_falla_con_error(self):
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError('x')):
            with self.assertRaises(CommandError):
                call_command('sincronizar_empleados', stdout=io.StringIO())


@override_settings(**CONFIG)
class VistasTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        aplicar_empleados([MELISSA, CARLOS, LEGACY, fila(13, '1003', 'PEDRO', 'BAJA', estado_actual='BAJA')])
        cls.general = User.objects.create_user('gen', password='x')
        cls.general.groups.add(Group.objects.get(name=GRUPO_GENERAL))
        cls.aeropuerto = User.objects.create_user('aero', password='x')
        cls.aeropuerto.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))

    def test_requiere_login(self):
        self.assertEqual(self.client.get(reverse('empleados:listado')).status_code, 302)
        self.assertEqual(self.client.get(reverse('empleados:buscar')).status_code, 302)

    def test_listado_todos_los_roles_sin_inactivos(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('empleados:listado'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total'], 3)
        self.assertContains(resp, 'LIC. MELISSA GALLEGOS')
        self.assertNotContains(resp, 'PEDRO BAJA')
        self.assertNotContains(resp, 'Sincronizar ahora')  # General no gestiona

    def test_listado_incluye_inactivos(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('empleados:listado'), {'inactivos': '1'})
        self.assertEqual(resp.context['total'], 4)

    def test_filtro_municipio(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('empleados:listado'), {'municipio': '2'})
        self.assertEqual([e.id_estancia for e in resp.context['page_obj']], [11])

    def test_buscar_json(self):
        self.client.force_login(self.general)
        datos = self.client.get(reverse('empleados:buscar'), {'q': 'melissa gall'}).json()
        self.assertEqual(len(datos['resultados']), 1)
        r = datos['resultados'][0]
        self.assertEqual(r['nombre_para_oficio'], 'LIC. MELISSA GALLEGOS')
        self.assertEqual(r['cargo'], 'JEFE DE DEPARTAMENTO')
        self.assertEqual(r['sexo'], 'F')

    def test_buscar_no_devuelve_inactivos(self):
        self.client.force_login(self.general)
        datos = self.client.get(reverse('empleados:buscar'), {'q': 'pedro'}).json()
        self.assertEqual(datos['resultados'], [])

    def test_firmantes_habituales_primero(self):
        Empleado.objects.filter(id_estancia=11).update(firmante_habitual=True)
        self.client.force_login(self.general)
        datos = self.client.get(reverse('empleados:buscar')).json()
        self.assertEqual(datos['resultados'][0]['numero_empleado'], '1002')

    def test_general_no_puede_sincronizar(self):
        self.client.force_login(self.general)
        with mock.patch('apps.empleados.views.sincronizar') as sync:
            resp = self.client.post(reverse('empleados:sincronizar'))
        self.assertRedirects(resp, reverse('empleados:listado'), fetch_redirect_response=False)
        sync.assert_not_called()

    def test_sincronizar_solo_post(self):
        self.client.force_login(self.aeropuerto)
        self.assertEqual(self.client.get(reverse('empleados:sincronizar')).status_code, 405)

    def test_aeropuerto_sincroniza(self):
        self.client.force_login(self.aeropuerto)
        fake, _ = respuesta([[MELISSA, CARLOS, LEGACY]])
        with mock.patch(URLOPEN, fake):
            resp = self.client.post(reverse('empleados:sincronizar'), follow=True)
        self.assertContains(resp, 'Catálogo actualizado')
        self.assertEqual(SincronizacionEmpleados.objects.first().usuario, self.aeropuerto)

    def test_sincronizacion_fallida_avisa_y_conserva_copia(self):
        self.client.force_login(self.aeropuerto)
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError('apagón')):
            resp = self.client.post(reverse('empleados:sincronizar'), follow=True)
        self.assertContains(resp, 'No se pudo sincronizar')
        self.assertEqual(Empleado.objects.filter(activo=True).count(), 3)

    def test_alternar_firmante(self):
        self.client.force_login(self.aeropuerto)
        pk = Empleado.objects.get(id_estancia=10).pk
        url = reverse('empleados:alternar_firmante', args=[pk])
        resp = self.client.post(url, {'querystring': 'q=gallegos'})
        self.assertRedirects(resp, reverse('empleados:listado') + '?q=gallegos',
                             fetch_redirect_response=False)
        self.assertTrue(Empleado.objects.get(pk=pk).firmante_habitual)
        self.client.post(url)
        self.assertFalse(Empleado.objects.get(pk=pk).firmante_habitual)

    def test_general_no_puede_alternar_firmante(self):
        self.client.force_login(self.general)
        pk = Empleado.objects.get(id_estancia=10).pk
        self.client.post(reverse('empleados:alternar_firmante', args=[pk]))
        self.assertFalse(Empleado.objects.get(pk=pk).firmante_habitual)
