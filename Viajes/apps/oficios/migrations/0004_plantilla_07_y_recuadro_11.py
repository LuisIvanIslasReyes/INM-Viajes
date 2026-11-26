"""
Iteración 2 (25/11/2026):

- Plantilla 07 (Constancia de llamada consular), del Word oficial
  `07. CONSTANCIA LLAMADA CONSULAR.docx`. No lleva "Ciudad, fecha." bajo el título: la
  fecha va dentro del texto ("En …, siendo el día …"). Mismas negritas que el original
  (solo el INM, la Subrepresentación Local y el nombre del extranjero): así cabe en una hoja.
- Plantilla 11: el motivo de rechazo va en un recuadro con borde, como en el Word
  oficial. Solo se cambia si el texto sigue igual al sembrado en la 0002 (si alguien ya
  lo editó en la pantalla de plantillas, se respeta).

Copia congelada; las correcciones posteriores se hacen en la pantalla de plantillas.
"""
from django.db import migrations

J = 'class="ql-align-justify"'

PLANTILLA_07 = (
    f'<p {J}>En {{{{ciudad_encabezado}}}}, siendo el día {{{{fecha_larga}}}}, '
    '{{firmante_el_la}} que suscribe {{firmante_nombre}}, {{firmante_cargo}} '
    '{{firmante_adscrito}} al <strong>Instituto Nacional de Migración</strong> en el {{aeropuerto}}, '
    'quien actúa legalmente con los testigos de asistencia que firman para debida constancia, constituidos en '
    'la oficina que ocupa la <strong>Subrepresentación Local</strong>, sito en la zona considerada como '
    'estéril, en el interior del citado aeropuerto, ubicado en {{domicilio}}. --</p>'
    '<p>[[ ]]</p>'
    f'<p {J}>Con fundamento en los artículos 19 y 20, fracción II, de la Ley de Migración; 27, fracción V, '
    'de la Ley Orgánica de la Administración Pública Federal; 3, apartado B, fracción III, 142, último '
    'párrafo, y 162, último párrafo, del Reglamento Interior de la Secretaría de Gobernación, publicado en el '
    'Diario Oficial de la Federación el 21 de marzo de 2025; y {{firmante_fundamento}} del '
    'ACUERDO por el que se delegan atribuciones para autorizar trámites migratorios y ejercer diversas '
    'atribuciones previstas en la Ley de Migración y su Reglamento a los servidores públicos adscritos a las '
    'Delegaciones Federales del Instituto Nacional de Migración, publicado en el Diario Oficial de la '
    'Federación en fecha 13 de noviembre 2012. --</p>'
    '<p>[[ HACE CONSTAR ]]</p>'
    f'<p {J}>Que, en cumplimiento de lo dispuesto en el artículo 60, párrafo cuarto, del Reglamento de la Ley '
    'de Migración, y 21, fracción VI, de los Lineamientos para Trámites y Procedimientos Migratorios, durante '
    'el procedimiento de segunda revisión se hizo del conocimiento de <strong>{{extranjero_nombre}}</strong> '
    'de nacionalidad {{extranjero_nacionalidad}}, su derecho de comunicarse con su '
    'Representación Consular durante la diligencia de segunda revisión; lo cual se le informó de forma verbal '
    'y, previamente, de manera escrita al completar su cuestionario; manifestando su conformidad de:</p>'
    '<p class="ql-align-center"><strong>REALIZARLA:</strong> ☐'
    '            '
    '<strong>NO REALIZARLA:</strong> ☐</p>'
    '<p><strong>Número telefónico:</strong> ____________________ '
    '<strong>Nombre de la persona que atendió:</strong> ____________________________</p>'
    '<p><strong>Hora de la comunicación:</strong> ____________________</p>'
    '<p>[[ SE CIERRA Y SE AUTORIZA LO ACTUADO ]]</p>'
)

MOTIVO_11_ANTES = (
    '<p class="ql-align-center"><strong>Motivo de rechazo aplicable</strong></p>'
    '<p class="ql-align-justify">{{motivo_rechazo}}</p>'
)
MOTIVO_11_DESPUES = (
    '<p>[[ RECUADRO ]]</p>'
    '<p class="ql-align-center"><strong>Motivo de rechazo aplicable</strong></p>'
    '<p class="ql-align-justify">{{motivo_rechazo}}</p>'
    '<p>[[ /RECUADRO ]]</p>'
)


def aplicar(apps, schema_editor):
    PlantillaOficio = apps.get_model('oficios', 'PlantillaOficio')
    PlantillaOficio.objects.update_or_create(
        numero=7,
        defaults={'nombre': 'Constancia de llamada consular', 'titulo': 'CONSTANCIA DE LLAMADA CONSULAR',
                  'bloque_firmas': 'CONSTANCIA', 'contenido_html': PLANTILLA_07, 'lleva_fecha': False,
                  'activo': True},
    )
    p11 = PlantillaOficio.objects.filter(numero=11).first()
    if p11 and MOTIVO_11_ANTES in p11.contenido_html and '[[ RECUADRO ]]' not in p11.contenido_html:
        p11.contenido_html = p11.contenido_html.replace(MOTIVO_11_ANTES, MOTIVO_11_DESPUES)
        p11.save(update_fields=['contenido_html'])


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0003_formato_congelado_y_firmas_empresa'),
    ]

    operations = [
        migrations.RunPython(aplicar, migrations.RunPython.noop),
    ]
