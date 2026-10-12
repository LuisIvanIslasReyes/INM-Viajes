from datetime import datetime, timezone as dt_timezone
from io import BytesIO

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL
from .models import Registro, UploadBatch
from .views.reporte_mensual import _compute_reporte_mensual


def _registro(batch, fecha, llegada, pais, sr=False, r=False, pi=False):
    return Registro.objects.create(
        batch=batch, vuelo_numero='HU7925', vuelo_fecha=fecha,
        aeropuerto_salida='PEK', aeropuerto_llegada=llegada,
        nombre_pasajero='PASAJERO', numero_asiento='1A', estado_checkin='OK',
        numero_ticket='T', genero='M', codigo_pais_emision='XX', pais_emision=pais,
        segunda_revision=sr, rechazado=r, internacion=pi,
    )


class ReporteMensualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aeropuerto = User.objects.create_user('aero', password='x')
        cls.aeropuerto.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))
        cls.general = User.objects.create_user('gen', password='x')
        cls.general.groups.add(Group.objects.get(name=GRUPO_GENERAL))

        tij = UploadBatch.objects.create(usuario=cls.aeropuerto, vuelo_numero='HU7925', tipo_vuelo='PEK-TIJ')
        mex = UploadBatch.objects.create(usuario=cls.aeropuerto, vuelo_numero='HU7925', tipo_vuelo='PEK-MEX')
        regreso = UploadBatch.objects.create(usuario=cls.aeropuerto, vuelo_numero='HU7926')

        mayo = datetime(2026, 5, 20, tzinfo=dt_timezone.utc)
        # Último instante de mayo en UTC: debe contar en mayo, no en junio.
        fin_mayo = datetime(2026, 5, 31, 23, 59, tzinfo=dt_timezone.utc)
        junio = datetime(2026, 6, 3, tzinfo=dt_timezone.utc)

        # Mayo: 2 inadmitidos (China, Bangladés), 1 internación (México), 1 SR sin resolver, 1 sin SR
        _registro(tij, mayo, 'TIJ', 'China', sr=True, r=True)
        _registro(mex, mayo, 'MEX', 'Bangladés', sr=True, r=True)
        _registro(mex, mayo, 'MEX', 'México', sr=True, pi=True)
        _registro(tij, fin_mayo, 'TIJ', 'China', sr=True)
        _registro(mex, mayo, 'MEX', 'China')
        # Junio: Bangladés vuelve a aparecer (debe ser la misma fila), 1 internación China
        _registro(tij, junio, 'TIJ', 'Bangladés', sr=True, r=True)
        _registro(mex, junio, 'MEX', 'China', sr=True, pi=True)
        # Vuelo de regreso MEX→PEK: no es arribo, no debe contar
        Registro.objects.create(
            batch=regreso, vuelo_numero='HU7926', vuelo_fecha=junio,
            aeropuerto_salida='MEX', aeropuerto_llegada='PEK',
            nombre_pasajero='REGRESO', numero_asiento='1A', estado_checkin='OK',
            numero_ticket='T', genero='M', codigo_pais_emision='CN', pais_emision='China',
            segunda_revision=True, rechazado=True,
        )

    def test_conteos_por_mes(self):
        d = _compute_reporte_mensual(2026, [5, 6])
        self.assertEqual(d['meses_labels'], ['May', 'Jun'])
        self.assertEqual(d['inad'], [2, 1])
        self.assertEqual(d['intern'], [1, 1])
        self.assertEqual(d['sr'], [4, 2])
        self.assertEqual(d['local'], [2, 1])
        self.assertEqual(d['transito'], [3, 1])
        self.assertEqual(d['total'], [5, 2])
        self.assertEqual(d['vuelo'], 'HU7925')
        self.assertEqual(d['origen'], 'China')

    def test_nacionalidad_repetida_en_varios_meses_es_una_sola_fila(self):
        d = _compute_reporte_mensual(2026, [5, 6])
        self.assertEqual(d['inad_por_pais'], [('Bangladés', [1, 1]), ('China', [1, 0])])
        self.assertEqual(d['intern_por_pais'], [('China', [0, 1]), ('México', [1, 0])])

    def test_parametros_invalidos(self):
        self.client.force_login(self.aeropuerto)
        url = reverse('generar_reporte_mensual_excel')
        for params in ({}, {'anio': '2026'}, {'anio': 'x', 'meses': '5'}, {'anio': '2026', 'meses': '0,13'}):
            self.assertEqual(self.client.get(url, params).status_code, 400, params)

    def test_usuario_general_no_accede(self):
        self.client.force_login(self.general)
        resp = self.client.get(reverse('generar_reporte_mensual_excel'), {'anio': '2026', 'meses': '5'})
        self.assertEqual(resp.status_code, 302)

    def test_descarga_xlsx(self):
        from openpyxl import load_workbook

        self.client.force_login(self.aeropuerto)
        resp = self.client.get(reverse('generar_reporte_mensual_excel'), {'anio': '2026', 'meses': '5,6'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Reporte_Completo_HU7925_2026_may-jun.xlsx', resp['Content-Disposition'])

        ws = load_workbook(BytesIO(resp.content))['Resumen mensual']
        filas = {ws.cell(row=r, column=1).value: [ws.cell(row=r, column=c).value for c in range(2, 5)]
                 for r in range(1, ws.max_row + 1)}
        self.assertEqual(filas['Total Inadmitidos'], [2, 1, 3])
        self.assertEqual(filas['Total pasajeros:'], [5, 2, 7])
        self.assertEqual(len(ws._charts), 2)

    def test_pagina_expone_meses_disponibles(self):
        self.client.force_login(self.aeropuerto)
        resp = self.client.get(reverse('inadmitidos_page'))
        self.assertEqual(resp.context['meses_disponibles'], {2026: [5, 6]})
        self.assertContains(resp, 'id="btn-reporte-completo"')
