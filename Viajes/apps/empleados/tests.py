"""
Tests de la réplica de empleados. No salen a la red: `urlopen` se simula con
respuestas con la misma forma que el endpoint de integración de la Estancia.

    python manage.py test apps.empleados --settings=Viajes.settings.test
"""
import io
import json
import urllib.error
import urllib.parse
from contextlib import contextmanager
from unittest import mock

from django.contrib import admin as django_admin
from django.contrib.auth.models import Group, User
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL

from .models import (
    Empleado,
    FundamentoPlaza,
    SincronizacionEmpleados,
    plaza_en_femenino,
    precargar_fundamentos,
)
from .services import ErrorSincronizacion, aplicar_empleados, descargar_empleados, sincronizar

URL_ESTANCIA = 'http://estancia.test/api/v1/personal/integracion/empleados/'
CONFIG = {'ESTANCIA_EMPLEADOS_URL': URL_ESTANCIA, 'ESTANCIA_API_KEY': 'clave-viajes'}
URLOPEN = 'apps.empleados.services.urllib.request.urlopen'


def fila(id_empleado, numero, nombres, apellidos, **extra):
    datos = {
        'id_empleado': id_empleado, 'employee_number': numero, 'academic_title': '',
        'nombres': nombres, 'apellidos': apellidos,
        'nombre_completo': f'{nombres} {apellidos}', 'sexo': '', 'estado_actual': 'ACTIVO',
        'plaza': '', 'plaza_descripcion': '', 'jerarquia': '',
        'municipio_id': 1, 'municipio': 'Tijuana',
        'fecha_modificacion': '2026-11-20T10:00:00-08:00',
        'actualizado': '2026-11-20T10:00:00-08:00',
    }
    datos.update(extra)
    return datos


MELISSA = fila(10, '1001', 'MELISSA', 'GALLEGOS', academic_title='LIC', sexo='F', jerarquia='AFM',
               plaza='JEFE DE DEPARTAMENTO',
               plaza_descripcion='JEFATURA DE DEPARTAMENTO DE CONTROL MIGRATORIO')
CARLOS = fila(11, '1002', 'CARLOS', 'TELLO', sexo='M', municipio_id=2, municipio='Mexicali')
LEGACY = fila(12, None, 'SIN', 'NUMERO', municipio_id=None, municipio='')


PROXIMO = '2026-11-24T09:58:00-08:00'


def _query(req):
    return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(req.full_url).query))


def respuesta(paginas, proximos=None):
    """Simula `urlopen` con el endpoint de la Estancia.

    Completa: devuelve la página pedida (`page=N`). Incremental (`modificado_desde`):
    la página se deduce de `despues_de_id` y el `next` lleva el cursor, con un host
    distinto a propósito (como cuando nginx reescribe) para comprobar que no se sigue.
    `proximos`: `proximo_desde` de cada página (None = la Estancia vieja no lo manda).
    """
    llamadas = []
    proximos = proximos or [PROXIMO] * len(paginas)

    @contextmanager
    def _urlopen(req, timeout=None, context=None):
        llamadas.append(req)
        q = _query(req)
        if 'modificado_desde' in q:
            ids = [str(p[-1]['id_empleado']) for p in paginas if p]
            pagina = ids.index(q['despues_de_id']) + 2 if 'despues_de_id' in q else 1
        else:
            pagina = int(q['page'])
        resultados = paginas[pagina - 1]
        siguiente = None
        if pagina < len(paginas):
            siguiente = ('http://127.0.0.1:9999/api/?' + urllib.parse.urlencode({
                'modificado_desde': '2026-11-24T09:00:00-08:00',
                'despues_de_id': resultados[-1]['id_empleado'], 'page_size': 1000,
            }) if 'modificado_desde' in q else 'otra')
        datos = {'next': siguiente, 'results': resultados}
        if proximos[pagina - 1] is not None:
            datos['proximo_desde'] = proximos[pagina - 1]
        yield io.BytesIO(json.dumps(datos).encode())

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
            filas, proximo = descargar_empleados()
        self.assertEqual([f['id_empleado'] for f in filas], [10, 11, 12])
        self.assertEqual(proximo.isoformat(), PROXIMO)
        self.assertEqual(len(llamadas), 2)
        self.assertEqual(llamadas[0].get_header('X-api-key'), 'clave-viajes')
        self.assertIn('incluir_bajas=1', llamadas[0].full_url)
        self.assertTrue(llamadas[0].full_url.startswith(URL_ESTANCIA))

    def test_proximo_desde_es_el_menor_de_las_paginas(self):
        fake, _ = respuesta([[MELISSA], [CARLOS]],
                            proximos=['2026-11-24T10:00:00-08:00', '2026-11-24T10:05:00-08:00'])
        with mock.patch(URLOPEN, fake):
            _, proximo = descargar_empleados()
        self.assertEqual(proximo.isoformat(), '2026-11-24T10:00:00-08:00')

    def test_estancia_vieja_sin_proximo_desde(self):
        fake, _ = respuesta([[MELISSA], [CARLOS]], proximos=[PROXIMO, None])
        with mock.patch(URLOPEN, fake):
            _, proximo = descargar_empleados()
        self.assertIsNone(proximo)

    def test_incremental_sigue_el_cursor_sobre_la_url_propia(self):
        desde = parse_datetime('2026-11-24T09:00:00-08:00')
        fake, llamadas = respuesta([[MELISSA, CARLOS], [LEGACY]])
        with mock.patch(URLOPEN, fake):
            filas, _ = descargar_empleados(modificado_desde=desde)
        self.assertEqual([f['id_empleado'] for f in filas], [10, 11, 12])
        primera, segunda = _query(llamadas[0]), _query(llamadas[1])
        self.assertEqual(primera['modificado_desde'], '2026-11-24T09:00:00-08:00')
        self.assertNotIn('incluir_bajas', primera)
        self.assertNotIn('page', primera)
        self.assertEqual(segunda['despues_de_id'], '11')
        # El '+'/'-' de la zona viaja codificado y el host es el nuestro, no el del `next`.
        self.assertIn('modificado_desde=2026-11-24T09%3A00%3A00-08%3A00', llamadas[0].full_url)
        self.assertTrue(llamadas[1].full_url.startswith(URL_ESTANCIA))

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
        self.assertEqual(m.plaza, 'JEFE DE DEPARTAMENTO')
        self.assertEqual(m.plaza_descripcion, 'JEFATURA DE DEPARTAMENTO DE CONTROL MIGRATORIO')
        self.assertEqual(m.jerarquia, 'AFM')
        self.assertEqual(m.cargo, 'JEFA DE DEPARTAMENTO')  # plaza en femenino
        self.assertEqual(m.modificado_en_estancia, parse_datetime('2026-11-20T10:00:00-08:00'))
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
        cambio = dict(MELISSA, plaza='SUBDIRECTOR DE ÁREA')
        self.assertEqual(aplicar_empleados([cambio]), (0, 1, 0))
        m = Empleado.objects.get(id_estancia=10)
        self.assertEqual(m.cargo, 'SUBDIRECTORA DE ÁREA')
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

    def test_incremental_no_desactiva_ausentes(self):
        aplicar_empleados([MELISSA, CARLOS])
        self.assertEqual(aplicar_empleados([dict(MELISSA, plaza='X')], desactivar_ausentes=False), (0, 1, 0))
        self.assertTrue(Empleado.objects.get(id_estancia=11).activo)

    def test_fila_repetida_gana_la_ultima(self):
        aplicar_empleados([MELISSA, dict(MELISSA, plaza='OTRA')])
        self.assertEqual(Empleado.objects.get(id_estancia=10).plaza, 'OTRA')

    def test_reaparece_se_reactiva(self):
        aplicar_empleados([MELISSA, CARLOS])
        aplicar_empleados([MELISSA])
        aplicar_empleados([MELISSA, CARLOS])
        self.assertTrue(Empleado.objects.get(id_estancia=11).activo)

    def test_conserva_fundamento_manual(self):
        aplicar_empleados([MELISSA, CARLOS])
        titular = FundamentoPlaza.objects.get(clave='TITULAR')
        Empleado.objects.filter(id_estancia=11).update(fundamento_manual=titular)
        aplicar_empleados([MELISSA, dict(CARLOS, plaza='AGENTE FEDERAL DE MIGRACIÓN "B"')])  # completa
        aplicar_empleados([dict(CARLOS, plaza='OFICIAL')], desactivar_ausentes=False)  # incremental
        carlos = Empleado.objects.get(id_estancia=11)
        self.assertEqual(carlos.plaza, 'OFICIAL')
        self.assertEqual(carlos.fundamento_manual, titular)
        self.assertEqual(carlos.fundamento_origen, 'manual')


class CargoTests(TestCase):

    def _empleado(self, **campos):
        return Empleado(nombres='A', apellidos='B', sincronizado_en=timezone.now(), **campos)

    def test_plaza_en_femenino(self):
        self.assertEqual(plaza_en_femenino('JEFE DE DEPARTAMENTO'), 'JEFA DE DEPARTAMENTO')
        self.assertEqual(plaza_en_femenino('SUB REPRESENTANTE LOCAL'), 'SUB REPRESENTANTE LOCAL')
        self.assertEqual(plaza_en_femenino(''), '')

    def test_hombre_conserva_la_plaza(self):
        self.assertEqual(self._empleado(sexo='M', plaza='JEFE DE DEPARTAMENTO').cargo, 'JEFE DE DEPARTAMENTO')

    def test_sin_sexo_decide_el_titulo(self):
        e = self._empleado(titulo_academico='MTRA', plaza='COORDINADOR DEL GRUPO BETA')
        self.assertEqual(e.cargo, 'COORDINADORA DEL GRUPO BETA')
        self.assertEqual(self._empleado(titulo_academico='LIC', plaza='JEFE X').cargo, 'JEFE X')

    def test_sin_plaza_cae_a_la_jerarquia(self):
        self.assertEqual(self._empleado(sexo='F', jerarquia='afm').cargo, 'AFM')
        self.assertEqual(self._empleado().cargo, '')


class FundamentoTests(TestCase):
    """Plaza → fundamento, con plazas reales tal como quedan tras D-144 (`separar_plaza`)."""

    def _empleado(self, plaza='', descripcion='', **campos):
        return Empleado(nombres='A', apellidos='B', plaza=plaza, plaza_descripcion=descripcion,
                        sincronizado_en=timezone.now(), **campos)

    def _clave(self, plaza, descripcion=''):
        aplicable = self._empleado(plaza, descripcion).fundamento_aplicable
        return aplicable.clave if aplicable else None

    def test_siembra_los_6(self):
        self.assertEqual(
            list(FundamentoPlaza.objects.values_list('clave', flat=True)),
            ['TITULAR', 'SUB_REP_FEDERAL', 'REP_LOCAL', 'SUB_REP_LOCAL', 'SUBDIR_CYV', 'JEFE_DEPTO'],
        )
        self.assertTrue(all(FundamentoPlaza.objects.values_list('activo', flat=True)))

    def test_cada_plaza_recibe_su_fundamento(self):
        casos = [
            ('TITULAR DE LA OFICINA DE REPRESENTACION DEL I.N.M. EN BAJA CALIFORNIA', '', 'TITULAR'),
            ('REPRESENTANTE LOCAL', 'REPRESENTACION LOCAL DEL I.N.M. EN TIJUANA', 'REP_LOCAL'),
            ('SUB REPRESENTANTE LOCAL', 'SUB REPRESENTACION LOCAL TECATE', 'SUB_REP_LOCAL'),
            ('SUB REPRESENTANTE LOCAL',
             'SUB REPRESENTANTE LOCAL AEROPUERTO INTERNACIONAL DE TIJUANA "A"', 'SUB_REP_LOCAL'),
            ('SUBDIRECTOR DE ÁREA',
             'SUBDIRECCION DE CONTROL Y VERIFICACION MIGRATORIA EN B.C.', 'SUBDIR_CYV'),
            ('JEFE DE DEPARTAMENTO', 'JEFATURA DE DEPARTAMENTO DE RECURSOS HUMANOS', 'JEFE_DEPTO'),
            ('JEFE DE DEPARTAMENTO', '', 'JEFE_DEPTO'),
        ]
        for plaza, descripcion, clave in casos:
            with self.subTest(plaza=plaza, descripcion=descripcion):
                self.assertEqual(self._clave(plaza, descripcion), clave)

    def test_textos_impresos(self):
        esperados = {
            'TITULAR DE LA OFICINA': 'Artículo 12, apartado B, fracciones I, II y III',
            'REPRESENTANTE LOCAL': 'Artículo 14, apartado B, fracciones I, II y III',
            'SUB REPRESENTANTE LOCAL': 'Artículo 15, apartado B, fracciones I, II y III',
            'JEFE DE DEPARTAMENTO': 'Artículo 23, fracciones I, II, III y IV',
        }
        for plaza, texto in esperados.items():
            with self.subTest(plaza=plaza):
                e = self._empleado(plaza)
                self.assertEqual(e.fundamento, texto)
                self.assertEqual(e.fundamento_origen, 'plaza')
        subdirector = self._empleado('SUBDIRECTOR DE ÁREA', 'SUBDIRECCION DE CONTROL Y VERIFICACION')
        self.assertEqual(subdirector.fundamento, 'Artículo 19, fracciones I, II, IV, V y IX')

    def test_plazas_sin_fundamento(self):
        casos = [
            ('SUBDIRECTOR DE ÁREA', 'SUBDIRECCION DE REGULACION MIGRATORIA'),
            ('SUBDIRECTOR DE ÁREA', 'SUBDIRECCION DE ATENCION AL MIGRANTE'),
            ('AGENTE FEDERAL DE MIGRACIÓN "B"', ''),
            ('COORDINADOR DEL GRUPO BETA', 'COORDINACION DEL GRUPO DE PROTECCION A MIGRANTES BETA TIJUANA'),
            ('ENCARGADO DE LA OFICINA DE REPRESENTACIÓN BC', ''),
            ('TITULARIDAD DE ALGO', ''),  # se compara en palabras completas
            ('', ''),
        ]
        for plaza, descripcion in casos:
            with self.subTest(plaza=plaza, descripcion=descripcion):
                e = self._empleado(plaza, descripcion)
                self.assertIsNone(e.fundamento_aplicable)
                self.assertEqual(e.fundamento, '')
                self.assertEqual(e.fundamento_origen, '')

    def test_sub_representante_federal_solo_a_mano(self):
        self.assertEqual(FundamentoPlaza.objects.get(clave='SUB_REP_FEDERAL').plaza_empieza_con, '')
        self.assertIsNone(self._clave('SUB REPRESENTANTE FEDERAL'))
        federal = FundamentoPlaza.objects.get(clave='SUB_REP_FEDERAL')
        e = self._empleado('', fundamento_manual=federal)
        self.assertEqual(e.fundamento, 'Artículo 13, apartado B, fracciones I, II y III')
        self.assertEqual(e.fundamento_origen, 'manual')

    def test_sin_importar_acentos_ni_espacios(self):
        self.assertEqual(self._clave('  jefe  de   departamento '), 'JEFE_DEPTO')
        self.assertEqual(
            self._clave('SUBDIRECTOR DE AREA', 'Subdirección de Control y Verificación Migratoria'),
            'SUBDIR_CYV',
        )

    def test_el_asignado_a_mano_gana(self):
        titular = FundamentoPlaza.objects.get(clave='TITULAR')
        e = self._empleado('JEFE DE DEPARTAMENTO', fundamento_manual=titular)
        self.assertEqual(e.fundamento, 'Artículo 12, apartado B, fracciones I, II y III')
        self.assertEqual(e.fundamento_origen, 'manual')
        self.assertEqual(e.fundamento_de_su_plaza.clave, 'JEFE_DEPTO')

    def test_inactivo_no_se_asigna_ni_a_mano(self):
        FundamentoPlaza.objects.filter(clave='TITULAR').update(activo=False)
        titular = FundamentoPlaza.objects.get(clave='TITULAR')
        e = self._empleado('JEFE DE DEPARTAMENTO', fundamento_manual=titular)
        self.assertEqual(e.fundamento_aplicable.clave, 'JEFE_DEPTO')
        self.assertEqual(e.fundamento_origen, 'plaza')
        self.assertIsNone(self._clave('TITULAR DE LA OFICINA'))

    def test_texto_corregido_en_el_catalogo(self):
        FundamentoPlaza.objects.filter(clave='JEFE_DEPTO').update(texto='Artículo 23, fracciones I a IV')
        self.assertEqual(self._empleado('JEFE DE DEPARTAMENTO').fundamento, 'Artículo 23, fracciones I a IV')

    def test_precarga_con_una_sola_consulta(self):
        empleados = [self._empleado('JEFE DE DEPARTAMENTO'), self._empleado('REPRESENTANTE LOCAL'),
                     self._empleado('AGENTE FEDERAL DE MIGRACIÓN "B"')]
        with self.assertNumQueries(1):
            precargar_fundamentos(empleados)
            textos = [e.fundamento for e in empleados]
        self.assertEqual(textos[1], 'Artículo 14, apartado B, fracciones I, II y III')
        self.assertEqual(textos[2], '')


@override_settings(**CONFIG)
class SincronizarTests(TestCase):

    def test_exitosa_deja_registro(self):
        fake, _ = respuesta([[MELISSA, CARLOS]])
        with mock.patch(URLOPEN, fake):
            r = sincronizar()
        self.assertTrue(r.exitosa)
        self.assertEqual((r.recibidos, r.creados), (2, 2))
        self.assertIsNotNone(r.terminada_en)
        self.assertEqual(r.modo, SincronizacionEmpleados.Modo.COMPLETA)
        self.assertEqual(r.proximo_desde, parse_datetime(PROXIMO))

    def test_segunda_es_incremental_desde_el_proximo_desde(self):
        fake, _ = respuesta([[MELISSA, CARLOS]])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        fake, llamadas = respuesta([[dict(MELISSA, plaza='SUBDIRECTOR DE ÁREA')]],
                                   proximos=['2026-11-24T10:13:00-08:00'])
        with mock.patch(URLOPEN, fake):
            r = sincronizar()
        self.assertEqual(r.modo, SincronizacionEmpleados.Modo.INCREMENTAL)
        self.assertEqual(parse_datetime(_query(llamadas[0])['modificado_desde']), parse_datetime(PROXIMO))
        self.assertEqual((r.recibidos, r.actualizados, r.desactivados), (1, 1, 0))
        self.assertTrue(Empleado.objects.get(id_estancia=11).activo)  # no vino, sigue activo
        self.assertEqual(r.proximo_desde, parse_datetime('2026-11-24T10:13:00-08:00'))

    def test_incremental_vacia_no_es_error(self):
        fake, _ = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        fake, _ = respuesta([[]])
        with mock.patch(URLOPEN, fake):
            r = sincronizar()
        self.assertTrue(r.exitosa)
        self.assertEqual(r.modo, SincronizacionEmpleados.Modo.INCREMENTAL)

    def test_completa_forzada(self):
        fake, _ = respuesta([[MELISSA, CARLOS]])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        fake, llamadas = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            r = sincronizar(completa=True)
        self.assertEqual(r.modo, SincronizacionEmpleados.Modo.COMPLETA)
        self.assertIn('incluir_bajas', _query(llamadas[0]))
        self.assertEqual(r.desactivados, 1)

    def test_sin_proximo_desde_vuelve_a_completa(self):
        fake, _ = respuesta([[MELISSA]], proximos=[None])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        fake, _ = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            self.assertEqual(sincronizar().modo, SincronizacionEmpleados.Modo.COMPLETA)

    def test_fallida_no_mueve_el_punto_de_partida(self):
        fake, _ = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        with mock.patch(URLOPEN, side_effect=urllib.error.URLError('x')):
            with self.assertRaises(ErrorSincronizacion):
                sincronizar()
        fake, llamadas = respuesta([[]])
        with mock.patch(URLOPEN, fake):
            sincronizar()
        self.assertEqual(parse_datetime(_query(llamadas[0])['modificado_desde']), parse_datetime(PROXIMO))

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
        self.assertIn('completa · recibidos 1', salida.getvalue())

    def test_comando_completa(self):
        fake, _ = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            call_command('sincronizar_empleados', stdout=io.StringIO())
        fake, llamadas = respuesta([[MELISSA]])
        with mock.patch(URLOPEN, fake):
            call_command('sincronizar_empleados', '--completa', stdout=io.StringIO())
        self.assertIn('incluir_bajas', _query(llamadas[0]))

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
        self.assertEqual(r['cargo'], 'JEFA DE DEPARTAMENTO')
        self.assertEqual(r['plaza_descripcion'], 'JEFATURA DE DEPARTAMENTO DE CONTROL MIGRATORIO')
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
        r = SincronizacionEmpleados.objects.first()
        self.assertEqual(r.usuario, self.aeropuerto)
        self.assertEqual(r.modo, SincronizacionEmpleados.Modo.COMPLETA)

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

    # ---- Fundamento ----

    def test_buscar_trae_fundamento(self):
        self.client.force_login(self.general)
        datos = self.client.get(reverse('empleados:buscar')).json()['resultados']
        por_numero = {r['numero_empleado']: r for r in datos}
        self.assertEqual(por_numero['1001']['fundamento'], 'Artículo 23, fracciones I, II, III y IV')
        self.assertEqual(por_numero['1001']['fundamento_origen'], 'plaza')
        self.assertEqual(por_numero['1002']['fundamento'], '')
        self.assertEqual(por_numero['1002']['fundamento_origen'], '')

    def test_listado_muestra_fundamento_sin_selector_para_general(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('empleados:listado'))
        self.assertContains(resp, 'Jefe de Departamento')  # Melissa, por su plaza
        self.assertNotContains(resp, 'A mano:')
        self.assertNotContains(resp, 'Cambiar')

    def test_sin_fundamento_solo_alerta_en_firmantes_habituales(self):
        self.client.force_login(self.general)
        # Carlos no trae plaza: mientras no firme, no es una alerta.
        self.assertNotContains(self.client.get(reverse('empleados:listado')), 'Sin fundamento')
        Empleado.objects.filter(id_estancia=11).update(firmante_habitual=True)
        self.assertContains(self.client.get(reverse('empleados:listado')), 'Sin fundamento', count=1)

    def test_listado_aeropuerto_ve_el_selector(self):
        self.client.force_login(self.aeropuerto)
        resp = self.client.get(reverse('empleados:listado'))
        self.assertContains(resp, 'Según plaza: Jefe de Departamento')
        self.assertContains(resp, 'Según plaza: sin fundamento')
        self.assertContains(resp, 'A mano: Sub Representante Federal')

    def test_asignar_y_quitar_fundamento(self):
        self.client.force_login(self.aeropuerto)
        carlos = Empleado.objects.get(id_estancia=11)
        url = reverse('empleados:asignar_fundamento', args=[carlos.pk])
        titular = FundamentoPlaza.objects.get(clave='TITULAR')

        resp = self.client.post(url, {'fundamento': titular.pk, 'querystring': 'q=tello'})
        self.assertRedirects(resp, reverse('empleados:listado') + '?q=tello',
                             fetch_redirect_response=False)
        self.assertEqual(Empleado.objects.get(pk=carlos.pk).fundamento, titular.texto)

        resp = self.client.post(url, {'fundamento': ''}, follow=True)
        self.assertContains(resp, 'su plaza no tiene fundamento')
        self.assertIsNone(Empleado.objects.get(pk=carlos.pk).fundamento_manual_id)

    def test_quitar_vuelve_al_de_su_plaza(self):
        self.client.force_login(self.aeropuerto)
        melissa = Empleado.objects.get(id_estancia=10)
        melissa.fundamento_manual = FundamentoPlaza.objects.get(clave='TITULAR')
        melissa.save(update_fields=['fundamento_manual'])
        resp = self.client.post(reverse('empleados:asignar_fundamento', args=[melissa.pk]),
                                {'fundamento': ''}, follow=True)
        self.assertContains(resp, 'se usa el fundamento de su plaza (Jefe de Departamento)')
        self.assertEqual(Empleado.objects.get(pk=melissa.pk).fundamento_origen, 'plaza')

    def test_fundamento_invalido_o_inactivo_no_se_asigna(self):
        self.client.force_login(self.aeropuerto)
        pk = Empleado.objects.get(id_estancia=10).pk
        url = reverse('empleados:asignar_fundamento', args=[pk])
        FundamentoPlaza.objects.filter(clave='TITULAR').update(activo=False)
        inactivo = FundamentoPlaza.objects.get(clave='TITULAR').pk
        for valor in ['abc', '99999', str(inactivo)]:
            with self.subTest(valor=valor):
                resp = self.client.post(url, {'fundamento': valor}, follow=True)
                self.assertContains(resp, 'no existe o está inactivo')
        self.assertIsNone(Empleado.objects.get(pk=pk).fundamento_manual_id)

    def test_general_no_puede_asignar_fundamento(self):
        self.client.force_login(self.general)
        pk = Empleado.objects.get(id_estancia=11).pk
        titular = FundamentoPlaza.objects.get(clave='TITULAR')
        self.client.post(reverse('empleados:asignar_fundamento', args=[pk]), {'fundamento': titular.pk})
        self.assertIsNone(Empleado.objects.get(pk=pk).fundamento_manual_id)

    def test_asignar_fundamento_solo_post(self):
        self.client.force_login(self.aeropuerto)
        pk = Empleado.objects.get(id_estancia=11).pk
        url = reverse('empleados:asignar_fundamento', args=[pk])
        self.assertEqual(self.client.get(url).status_code, 405)


class AdminTests(TestCase):

    def test_changelist_muestra_el_fundamento(self):
        aplicar_empleados([MELISSA, CARLOS])
        self.client.force_login(User.objects.create_superuser('su', password='x'))
        resp = self.client.get(reverse('admin:empleados_empleado_changelist'))
        self.assertContains(resp, 'Jefe de Departamento')
        self.assertContains(resp, 'sin fundamento')

    def test_solo_el_superuser_cambia_el_catalogo(self):
        modelo_admin = django_admin.site._registry[FundamentoPlaza]
        request = RequestFactory().get('/')
        request.user = User.objects.create_user('staff', password='x', is_staff=True)
        self.assertFalse(modelo_admin.has_change_permission(request))
        self.assertFalse(modelo_admin.has_add_permission(request))
        request.user = User.objects.create_superuser('su', password='x')
        self.assertTrue(modelo_admin.has_change_permission(request))

    def test_en_empleado_solo_se_editan_los_campos_de_viajes(self):
        modelo_admin = django_admin.site._registry[Empleado]
        self.assertNotIn('fundamento_manual', modelo_admin.readonly_fields)
        self.assertNotIn('firmante_habitual', modelo_admin.readonly_fields)
        self.assertIn('plaza', modelo_admin.readonly_fields)
