import datetime
import io
from unittest import mock

from docx import Document
from django.test import TestCase

from ..models import Expediente, OficioHistorial, OficioInstancia
from ..services import expedientes as servicio
from ..services.pdf import docx_a_pdf
from .utils import Escenario, MediaTemporalMixin, registro, usuarios

Accion = OficioHistorial.Accion


class CrearExpedienteTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aero, _ = usuarios()

    def test_desde_registros_precarga_datos(self):
        r1 = registro(self.aero, 'ZHANG WEI', codigo='CHN', pais='中国', r=True, genero='M')
        r2 = registro(self.aero, 'IVAN P', codigo='RUS', pais='RUSSIA', genero='女')
        exp = servicio.crear_expediente(self.aero, [r1, r2])
        self.assertTrue(exp.folio.startswith(f'VJ-{exp.fecha:%Y}-'))
        self.assertEqual(exp.resultado, Expediente.Resultado.RECHAZO)
        zhang, ivan = exp.personas.all()
        # Gentilicio en minúsculas: "de nacionalidad china".
        self.assertEqual((zhang.nombre, zhang.nacionalidad, zhang.idioma, zhang.sexo), ('ZHANG WEI', 'china', 'zh', 'M'))
        self.assertEqual((ivan.nacionalidad, ivan.idioma, ivan.sexo, ivan.orden), ('rusa', 'ru', 'F', 2))
        self.assertEqual(zhang.fecha_nacimiento, datetime.date(1994, 4, 14))
        self.assertEqual((zhang.documento, zhang.vuelo, zhang.registro), ('EG0000000', 'HU7925', r1))

    def test_codigo_desconocido_usa_pais_emision(self):
        r = registro(self.aero, 'X', codigo='ZZZ', pais='Narnia', sr=True)
        persona = servicio.crear_expediente(self.aero, [r]).personas.get()
        self.assertEqual((persona.nacionalidad, persona.idioma), ('Narnia', 'es'))

    def test_resultado_sugerido(self):
        self.assertEqual(servicio.crear_expediente(self.aero, [registro(self.aero, 'A', pi=True)]).resultado,
                         Expediente.Resultado.INTERNACION)
        self.assertEqual(servicio.crear_expediente(self.aero, []).resultado, Expediente.Resultado.PENDIENTE)

    def test_agregar_registros_no_duplica(self):
        r1, r2 = registro(self.aero, 'A'), registro(self.aero, 'B')
        exp = servicio.crear_expediente(self.aero, [r1])
        self.assertEqual(len(servicio.agregar_registros(exp, [r1, r2])), 1)
        self.assertEqual(list(exp.personas.values_list('nombre', 'orden')), [('A', 1), ('B', 2)])


class OficioFlujoTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero)
        [self.o02, self.o11] = servicio.crear_borradores(self.e.persona, [self.e.p02, self.e.p11], self.aero)

    def test_borradores_copian_la_plantilla_y_no_se_repiten(self):
        self.assertEqual(self.o02.contenido_html, self.e.p02.contenido_html)
        self.assertEqual(servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero), [])
        self.assertEqual(self.o02.historial.get().accion, Accion.CREADO)
        # Cambiar la plantilla no toca los borradores ya creados.
        self.e.p02.contenido_html = '<p>nuevo</p>'
        self.e.p02.save()
        self.o02.refresh_from_db()
        self.assertNotEqual(self.o02.contenido_html, '<p>nuevo</p>')

    def test_guardar_limpia_y_registra_solo_si_cambia(self):
        cambios = servicio.guardar_borrador(self.o02, self.aero, '<p>Hola<script>x</script></p>')
        self.assertEqual(cambios, ['texto'])
        self.assertEqual(self.o02.contenido_html, '<p>Hola</p>')
        self.assertEqual(servicio.guardar_borrador(self.o02, self.aero, '<p>Hola</p>'), [])
        self.assertEqual(self.o02.historial.filter(accion=Accion.EDITADO).count(), 1)

    def test_revisar_lo_que_impide_imprimir(self):
        self.assertEqual(servicio.revisar(self.o02)[0], [])
        exp = self.e.expediente
        exp.testigo_2 = None
        exp.save()
        errores, _ = servicio.revisar(self.o02)
        self.assertEqual(errores, ['Faltan los 2 testigos de asistencia.'])
        self.assertEqual(servicio.revisar(self.o11)[0], [])  # la notificación no lleva testigos

        exp.firmante.plaza = 'AGENTE FEDERAL DE MIGRACIÓN'
        exp.firmante.save()
        errores, _ = servicio.revisar(OficioInstancia.objects.get(pk=self.o11.pk))
        self.assertIn('no tiene fundamento', errores[0])

        exp.firmante = None
        exp.save()
        self.assertIn('Falta el firmante del expediente.', servicio.revisar(self.o11)[0])

    def test_revisar_variables_desconocidas_y_vacias(self):
        servicio.guardar_borrador(self.o11, self.aero, '<p>{{inventada}} {{sala_entrevista}} {{motivo_rechazo}}</p>')
        errores, avisos = servicio.revisar(self.o11)
        self.assertEqual(errores, ['El texto usa variables que no existen: {{inventada}}.'])
        self.assertEqual(avisos, ['Sin dato (saldrá en blanco): Motivo de rechazo (oficio 11).'])

    def test_imprimir_congela(self):
        docx = servicio.imprimir(self.o02, self.aero)
        self.o02.refresh_from_db()
        self.assertEqual(self.o02.estado, OficioInstancia.Estado.IMPRESO)
        self.assertEqual(self.o02.snap_contexto['firmante_fundamento'], 'Artículo 23, fracciones I, II, III y IV')
        self.assertTrue(self.o02.docx_impreso.name.endswith('_02_WANG_PRUEBA.docx'))
        self.assertEqual(self.o02.impreso_por, self.aero)
        self.assertEqual(self.o02.historial.first().accion, Accion.IMPRESO)

        # Ya no se edita, y lo que se descarga es lo impreso aunque cambien los datos.
        with self.assertRaises(servicio.ErrorOficio):
            servicio.guardar_borrador(self.o02, self.aero, '<p>otro</p>')
        with self.assertRaises(servicio.ErrorOficio):
            servicio.imprimir(self.o02, self.aero)
        self.e.persona.nombre = 'OTRO NOMBRE'
        self.e.persona.save()
        self.assertEqual(servicio.docx_de(OficioInstancia.objects.get(pk=self.o02.pk)), docx)

    def test_impreso_sin_archivo_se_regenera_con_lo_congelado(self):
        servicio.imprimir(self.o02, self.aero)
        self.o02.refresh_from_db()
        self.o02.docx_impreso.storage.delete(self.o02.docx_impreso.name)
        self.e.persona.nombre = 'OTRO NOMBRE'
        self.e.persona.save()
        texto = '\n'.join(p.text for p in Document(io.BytesIO(servicio.docx_de(self.o02))).paragraphs)
        self.assertIn('WANG PRUEBA', texto)
        self.assertNotIn('OTRO NOMBRE', texto)

    def test_no_imprime_con_errores(self):
        self.e.expediente.firmante = None
        self.e.expediente.save()
        with self.assertRaisesMessage(servicio.ErrorOficio, 'Falta el firmante'):
            servicio.imprimir(OficioInstancia.objects.get(pk=self.o02.pk), self.aero)

    def test_reabrir_pide_motivo(self):
        with self.assertRaises(servicio.ErrorOficio):
            servicio.reabrir(self.o02, self.aero, 'x')  # todavía es borrador
        servicio.imprimir(self.o02, self.aero)
        with self.assertRaisesMessage(servicio.ErrorOficio, 'motivo'):
            servicio.reabrir(self.o02, self.aero, '  ')
        servicio.reabrir(self.o02, self.aero, 'Faltó la sala')
        self.o02.refresh_from_db()
        self.assertTrue(self.o02.editable)
        self.assertIsNone(self.o02.snap_contexto)
        ultimo = self.o02.historial.first()
        self.assertEqual(ultimo.accion, Accion.REABIERTO)
        self.assertIn('Faltó la sala', ultimo.detalle)


class PdfTests(TestCase):

    def test_convierte_y_limpia(self):
        def falso(ruta):
            import os
            import tempfile
            carpeta = tempfile.mkdtemp()
            salida = os.path.join(carpeta, 'x.pdf')
            with open(salida, 'wb') as fh:
                fh.write(b'%PDF-falso')
            falso.carpeta = carpeta
            return salida

        with mock.patch('apps.oficios.services.pdf.convertir_a_pdf', side_effect=falso):
            self.assertEqual(docx_a_pdf(b'docx'), b'%PDF-falso')
        import os
        self.assertFalse(os.path.exists(falso.carpeta))

    def test_sin_libreoffice_devuelve_none(self):
        with mock.patch('apps.oficios.services.pdf.convertir_a_pdf', return_value=None):
            self.assertIsNone(docx_a_pdf(b'docx'))
