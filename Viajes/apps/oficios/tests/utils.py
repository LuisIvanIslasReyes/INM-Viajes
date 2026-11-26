"""Datos de prueba para los tests de Oficios (todo ficticio)."""
import datetime
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.test import override_settings
from django.utils import timezone

from apps.cuentas.roles import GRUPO_AEROPUERTO, GRUPO_GENERAL
from apps.empleados.models import Empleado
from apps.uploader.models import Registro, UploadBatch

from ..models import Expediente, PersonaExpediente, PlantillaOficio


def empleado(id_estancia, nombres, apellidos, plaza='', sexo='M', titulo='LIC', **extra):
    return Empleado.objects.create(
        id_estancia=id_estancia, nombres=nombres, apellidos=apellidos, plaza=plaza, sexo=sexo,
        titulo_academico=titulo, sincronizado_en=timezone.now(), **extra,
    )


def usuarios():
    aeropuerto = User.objects.create_user('aero', password='x')
    aeropuerto.groups.add(Group.objects.get(name=GRUPO_AEROPUERTO))
    general = User.objects.create_user('gen', password='x')
    general.groups.add(Group.objects.get(name=GRUPO_GENERAL))
    return aeropuerto, general


def registro(usuario, nombre, codigo='CHN', pais='中国', sr=True, r=False, pi=False, genero='M', **extra):
    batch, _ = UploadBatch.objects.get_or_create(
        usuario=usuario, vuelo_numero='HU7925', defaults={'fecha_vuelo': datetime.date(2026, 11, 24)},
    )
    datos = {
        'batch': batch, 'vuelo_numero': 'HU7925',
        'vuelo_fecha': timezone.make_aware(datetime.datetime(2026, 11, 24, 20, 14)),
        'aeropuerto_salida': 'PEK', 'aeropuerto_llegada': 'TIJ', 'nombre_pasajero': nombre,
        'numero_documento': 'EG0000000', 'numero_asiento': '1A', 'estado_checkin': 'OK',
        'numero_ticket': 'T', 'genero': genero, 'codigo_pais_emision': codigo, 'pais_emision': pais,
        'segunda_revision': sr, 'rechazado': r, 'internacion': pi,
        'fecha_nacimiento': datetime.date(1994, 4, 14),
    }
    datos.update(extra)
    return Registro.objects.create(**datos)


class Escenario:
    """Expediente listo para imprimir: firmante con fundamento, 2 testigos y una persona."""

    def __init__(self, usuario=None, idioma='es'):
        self.firmante = empleado(1, 'MELISSA', 'GALLEGOS', plaza='JEFE DE DEPARTAMENTO', sexo='F')
        self.testigo_1 = empleado(2, 'SAMANTHA', 'MORALES', plaza='AGENTE FEDERAL DE MIGRACIÓN', sexo='F', titulo='')
        self.testigo_2 = empleado(3, 'JAVIER', 'DUARTE', plaza='AGENTE FEDERAL DE MIGRACIÓN', titulo='')
        self.expediente = Expediente.objects.create(
            creado_por=usuario, firmante=self.firmante, testigo_1=self.testigo_1, testigo_2=self.testigo_2,
        )
        self.persona = PersonaExpediente.objects.create(
            expediente=self.expediente, nombre='WANG PRUEBA', nacionalidad='china',
            fecha_nacimiento=datetime.date(1994, 4, 14), documento='EG2830939', idioma=idioma,
            vuelo='HU7925', sala_entrevista='1', orden=1,
        )
        self.p02 = PlantillaOficio.objects.get(numero=2)
        self.p11 = PlantillaOficio.objects.get(numero=11)


class MediaTemporalMixin:
    """Los .docx impresos van a un MEDIA_ROOT temporal, no a Viajes/media."""

    def setUp(self):
        super().setUp()
        self._media = tempfile.mkdtemp(prefix='oficios_test_media_')
        self._override = override_settings(MEDIA_ROOT=self._media)
        self._override.enable()

    def tearDown(self):
        self._override.disable()
        shutil.rmtree(self._media, ignore_errors=True)
        super().tearDown()
