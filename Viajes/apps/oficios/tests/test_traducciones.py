"""Iteración 3: traducciones por idioma (variantes), recargar texto, fuentes y árabe."""
import io
from decimal import Decimal

from docx import Document
from docx.shared import Cm
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from ..models import OficioInstancia, PlantillaHistorial, PlantillaOficio, PlantillaOficioIdioma
from ..services import expedientes as servicio
from ..services.docx_oficio import pieza_de, render_docx
from ..services.html_docx import EscritorHTML, pendientes
from .utils import Escenario, MediaTemporalMixin, usuarios


def _abrir(docx_bytes):
    return Document(io.BytesIO(docx_bytes))


class SiembraTraduccionesTests(TestCase):

    def test_variantes_sembradas(self):
        sembradas = set(PlantillaOficioIdioma.objects.values_list('plantilla__numero', 'idioma'))
        self.assertEqual(sembradas, {(2, 'zh'), (2, 'ru'), (2, 'fr'), (3, 'zh'), (3, 'ru'), (3, 'fr'),
                                     (4, 'zh'), (4, 'fr'), (Decimal('4.1'), 'zh'), (7, 'zh'), (7, 'ru'),
                                     (8, 'zh'), (8, 'ru'), (9, 'zh'), (9, 'ru')})
        p02 = PlantillaOficio.objects.get(numero=2)
        zh = p02.variante('zh')
        self.assertIn('使用电子翻译器的证明', zh.titulo)
        # El español sigue completo y la traducción va al final del párrafo del HACE CONSTAR.
        self.assertIn('con el medio de traducción empleado. / <span class="ql-size-small">该中国籍外籍人士',
                      zh.contenido_html)  # la traducción va chica (8 pt), como en el Word oficial
        self.assertIn('{{extranjero_nombre}}', p02.variante('ru').contenido_html)
        self.assertEqual(pendientes(p02.variante('fr').contenido_html), ['NATIONALITÉ EN FRANÇAIS'])
        self.assertEqual(pendientes(p02.variante('ru').contenido_html), [])  # «Vasco…» son comillas
        # 07/08/09: mismo texto que el español, solo la leyenda.
        v07 = PlantillaOficio.objects.get(numero=7).variante('zh')
        self.assertEqual((v07.contenido_html, v07.leyenda_firma_persona), ('', 'NOMBRE Y FIRMA / 姓名和签名'))


class BorradoresPorIdiomaTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, _ = usuarios()
        self.e = Escenario(self.aero, idioma='zh')

    def test_se_crea_en_su_idioma_o_en_espanol(self):
        p07 = PlantillaOficio.objects.get(numero=7)
        o02, o07, o11 = servicio.crear_borradores(self.e.persona, [self.e.p02, p07, self.e.p11], self.aero)
        self.assertEqual((o02.idioma, o07.idioma, o11.idioma), ('zh', 'zh', 'es'))
        self.assertIn('该中国籍外籍人士', o02.contenido_html)
        self.assertEqual(o07.contenido_html, p07.contenido_html)  # texto vacío = el del español
        self.assertEqual(o11.contenido_html, self.e.p11.contenido_html)

    def test_documento_bilingue(self):
        [o02] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        doc = _abrir(render_docx([pieza_de(o02)]))
        textos = [p.text for p in doc.paragraphs]
        self.assertIn('CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO (Chino) / 使用电子翻译器的证明。（中文）', textos)
        self.assertTrue(any('该中国籍外籍人士' in t for t in textos))
        persona = doc.tables[0].rows[0].cells[1].text
        self.assertIn('WANG PRUEBA', persona)
        self.assertIn('NOMBRE Y FIRMA / 姓名和签名', persona)
        # Fuentes: chino con la fuente asiática y árabe con la de escritura compleja.
        rfonts = doc.styles['Normal'].element.rPr.rFonts
        self.assertEqual(rfonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia'),
                         'Microsoft YaHei')

    def test_al_imprimir_se_congela_titulo_y_leyenda(self):
        [o02] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        servicio.imprimir(o02, self.aero)
        v = self.e.p02.variante('zh')
        v.titulo = 'OTRO'
        v.leyenda_firma_persona = 'OTRA'
        v.save()
        pieza = pieza_de(OficioInstancia.objects.get(pk=o02.pk))
        self.assertIn('使用电子翻译器的证明', pieza.titulo)
        self.assertEqual(pieza.leyenda_persona, 'NOMBRE Y FIRMA / 姓名和签名')

    def test_ruso_imprime_y_frances_pide_la_nacionalidad(self):
        self.e.persona.idioma = 'ru'
        self.e.persona.save()
        [o_ru] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        self.assertEqual(servicio.revisar(o_ru)[0], [])
        o_ru.delete()
        self.e.persona.idioma = 'fr'
        self.e.persona.save()
        [o_fr] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        errores, _ = servicio.revisar(o_fr)
        self.assertEqual(errores, ['Falta llenar en el texto: «NATIONALITÉ EN FRANÇAIS».'])

    def test_recargar_texto_y_variante_inactiva(self):
        [o02] = servicio.crear_borradores(self.e.persona, [self.e.p02], self.aero)
        self.assertEqual(servicio.recargar_texto(o02, 'es', self.aero), 'es')
        self.assertEqual(o02.contenido_html, self.e.p02.contenido_html)
        self.e.p02.variantes.filter(idioma='zh').update(activo=False)
        self.assertEqual(servicio.recargar_texto(o02, 'zh', self.aero), 'es')  # sin traducción activa
        servicio.imprimir(o02, self.aero)
        with self.assertRaises(servicio.ErrorOficio):
            servicio.recargar_texto(o02, 'es', self.aero)

    def test_comparar_variables(self):
        faltan, desconocidas = servicio.comparar_variables(
            '<p>{{extranjero_nombre}} {{vuelo}}</p>', '<p>{{extranjero_nombre}} / {{inventada}}</p>')
        self.assertEqual((faltan, desconocidas), (['vuelo'], ['inventada']))


class ArabeTests(SimpleTestCase):

    def test_runs_rtl_y_parrafo_bidi(self):
        document = Document()
        EscritorHTML(document, Cm(18)).escribir(
            '<p>Nombre completo y firma de la persona extranjera / الاسم والتوقيع</p>'
            '<p>تم استخدام جهاز ترجمة إلكتروني</p>')
        mixto, arabe = document.paragraphs
        rtl = [r.text for r in mixto.runs if r.font.rtl]
        self.assertEqual(rtl, ['الاسم والتوقيع'])
        self.assertNotIn('<w:bidi/>', mixto._p.xml)  # mayormente español: no se voltea el párrafo
        self.assertIn('<w:bidi/>', arabe._p.xml)
        self.assertEqual(arabe.alignment, 2)  # derecha


class VistasTraduccionTests(MediaTemporalMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.aero, self.general = usuarios()
        self.client.force_login(self.aero)
        self.p11 = PlantillaOficio.objects.get(numero=11)

    def test_crear_traduccion_nueva_empieza_en_espanol_y_guarda_version(self):
        url = reverse('oficios:plantilla_idioma', args=[self.p11.pk, 'en'])
        resp = self.client.get(url)
        self.assertContains(resp, 'Nueva traducción')
        self.assertEqual(resp.context['texto'], self.p11.contenido_html)
        traducido = self.p11.contenido_html + '<p>You are notified… {{extranjero_nombre}} {{inventada}}</p>'
        resp = self.client.post(url, {'titulo': 'NOTIFICACIÓN … / NOTICE', 'leyenda_firma_persona': 'FIRMA / SIGNATURE',
                                      'activo': 'on', 'contenido_html': traducido}, follow=True)
        self.assertContains(resp, 'variables que no existen')
        v = self.p11.variante('en')
        self.assertEqual(v.leyenda_firma_persona, 'FIRMA / SIGNATURE')
        self.assertEqual(PlantillaHistorial.objects.filter(plantilla=self.p11, idioma='en').count(), 1)

    def test_igual_al_espanol_se_guarda_vacio(self):
        url = reverse('oficios:plantilla_idioma', args=[self.p11.pk, 'ar'])
        self.client.post(url, {'titulo': '', 'leyenda_firma_persona': 'FIRMA / التوقيع', 'activo': 'on',
                               'contenido_html': self.p11.contenido_html})
        self.assertEqual(self.p11.variante('ar').contenido_html, '')
        self.assertContains(self.client.get(url), 'mismo texto que el español')

    def test_idioma_invalido_y_permisos(self):
        resp = self.client.get(reverse('oficios:plantilla_idioma', args=[self.p11.pk, 'es']), follow=True)
        self.assertContains(resp, 'Idioma no válido.')
        self.client.force_login(self.general)
        resp = self.client.get(reverse('oficios:plantilla_idioma', args=[self.p11.pk, 'zh']))
        self.assertRedirects(resp, reverse('directorio:listado'), fetch_redirect_response=False)

    def test_lista_y_recargar_desde_el_oficio(self):
        resp = self.client.get(reverse('oficios:plantillas'))
        self.assertContains(resp, '+ Traducción')
        self.assertContains(resp, reverse('oficios:plantilla_idioma', args=[PlantillaOficio.objects.get(numero=2).pk, 'zh']))
        e = Escenario(self.aero, idioma='zh')
        [o02] = servicio.crear_borradores(e.persona, [e.p02], self.aero)
        resp = self.client.get(reverse('oficios:oficio', args=[o02.pk]))
        self.assertContains(resp, 'Idioma del texto: <strong>Chino</strong>')
        self.client.post(reverse('oficios:oficio_recargar', args=[o02.pk]), {'idioma': 'es'})
        o02.refresh_from_db()
        self.assertEqual(o02.idioma, 'es')

    def test_guardar_plantilla_deja_version(self):
        url = reverse('oficios:plantilla_editar', args=[self.p11.pk])
        self.client.post(url, {'nombre': self.p11.nombre, 'titulo': self.p11.titulo, 'bloque_firmas': 'NOTIFICACION',
                               'tamano_letra_pt': '10', 'lleva_fecha': 'on', 'activo': 'on',
                               'contenido_html': '<p>Nuevo</p>'})
        self.assertEqual(PlantillaHistorial.objects.filter(plantilla=self.p11, idioma='es').count(), 1)


class TextoChicoTests(SimpleTestCase):

    def test_ql_size_small_sale_a_8_pt(self):
        document = Document()
        EscritorHTML(document, Cm(18)).escribir('<p>Español / <span class="ql-size-small">перевод</span></p>')
        normal, chico = document.paragraphs[0].runs
        self.assertIsNone(normal.font.size)
        self.assertEqual((chico.text, chico.font.size.pt), ('перевод', 8.0))
