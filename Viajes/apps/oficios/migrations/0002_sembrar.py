"""
Siembra inicial de Oficios (25/11/2026): datos de la oficina, motivos de rechazo del
oficio 11 y las plantillas 02 y 11.

Copia congelada: el texto sale de los Word oficiales de la USB (`02. CONSTANCIA DE USO
TRADUCTOR ELECTRÓNICO.docx` y `11. NOTIFICACIÓN RECHAZO AÉREO.docx`), con sus controles
de contenido cambiados por {{variables}}. Si después se corrige el texto, se hace en la
pantalla de plantillas, NO aquí. Es idempotente (update_or_create).

Convenciones del texto (ver services/html_docx.py): `[[ TÍTULO ]]` es un separador
con guiones, y un párrafo que termina en ` --` se rellena con guiones hasta el margen.
"""
from django.db import migrations

J = 'class="ql-align-justify"'

PLANTILLA_02 = (
    f'<p {J}>En <strong>{{{{ciudad}}}}</strong>, siendo el día <strong>{{{{fecha_larga}}}}</strong> quien '
    'suscribe <strong>{{firmante_nombre}}</strong> en su carácter de <strong>{{firmante_cargo}}</strong> '
    '{{firmante_adscrito}} al Instituto Nacional de Migración en <strong>{{aeropuerto}}</strong>, quien actúa '
    'con los testigos de asistencia que firman para debida constancia, constituidos en el área habilitada '
    'para el procedimiento migratorio, ubicada en <strong>{{domicilio}}</strong>.</p>'
    f'<p {J}>Con fundamento en lo dispuesto en los artículos 19, 20, fracción II, de la Ley de Migración, '
    '27, fracción V, de la Ley Orgánica de la Administración Pública Federal, 3, inciso B), fracción III, '
    '142, último párrafo y 162, último párrafo, del Reglamento Interior de la Secretaría de Gobernación '
    'vigente (D.O.F. 21/03/2025) y <strong>{{firmante_fundamento}}</strong> del ACUERDO por el que se '
    'delegan atribuciones para autorizar trámites migratorios y ejercer diversas atribuciones previstas en '
    'la Ley de Migración y su Reglamento a los servidores públicos adscritos a las Delegaciones Federales '
    'del Instituto Nacional de Migración, publicado en el Diario Oficial de la Federación en fecha 13 de '
    'noviembre 2012. --</p>'
    '<p>[[ HACE CONSTAR ]]</p>'
    f'<p {J}>Toda vez que la persona extranjera de nombre <strong>{{{{extranjero_nombre}}}}</strong>, de '
    'nacionalidad <strong>{{extranjero_nacionalidad}}</strong>, no habla ni entiende el idioma español, se '
    'utilizó un equipo electrónico traductor, marca “Vasco Translator V4 (electronic translator)”, en '
    'términos del artículo 35, párrafo segundo, de la Ley de Migración, para traducir al idioma '
    '<strong>{{extranjero_idioma}}</strong>, que manifiesta comprender y hablar, a efecto de hacer de su '
    'conocimiento el procedimiento migratorio, los derechos que le asisten durante el mismo y el contenido '
    'de las constancias que se integren. La persona extranjera firma la presente en señal de conformidad '
    'con el medio de traducción empleado.</p>'
)

PLANTILLA_11 = (
    '<p class="ql-align-right"><strong>No. de sala de entrevista: </strong>{{sala_entrevista}}</p>'
    '<p><strong>Nombre: </strong>{{extranjero_nombre}}</p>'
    '<p><strong>Nacionalidad: </strong>{{extranjero_nacionalidad}}</p>'
    '<p><strong>Fecha de nacimiento: </strong>{{extranjero_fecha_nacimiento}}</p>'
    '<p><br></p>'
    f'<p {J}>Hago de su conocimiento que esta autoridad migratoria en el {{{{aeropuerto}}}} ha determinado '
    'su inadmisibilidad al territorio nacional y, en consecuencia, su rechazo aéreo, con fundamento en los '
    'artículos 88 de la Ley de Migración, 57, 60, párrafo tercero, y 65 de su Reglamento, por el motivo que '
    'a continuación se señala:</p>'
    '<p><br></p>'
    '<p class="ql-align-center"><strong>Motivo de rechazo aplicable</strong></p>'
    f'<p {J}>{{{{motivo_rechazo}}}}</p>'
    '<p><br></p>'
    f'<p {J}>Por lo anterior, con fundamento en los artículos 86 de la Ley de Migración; 42, fracción IX, '
    '78 y 79 de su Reglamento, la empresa de transporte aéreo que propició su arribo al país se encargará de '
    'su custodia, alimentación y del establecimiento del itinerario de vuelo mediante el cual será '
    'transportada al país de procedencia, de origen o a aquel en el que sea admisible, lo cual deberá '
    'ocurrir dentro de las siguientes veinticuatro horas.</p>'
)

PLANTILLAS = [
    # numero, nombre, titulo, bloque_firmas, contenido
    (2, 'Constancia de uso de traductor electrónico', 'CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO',
     'CONSTANCIA', PLANTILLA_02),
    (11, 'Notificación de rechazo aéreo', 'NOTIFICACIÓN DE RESOLUCIÓN DE RECHAZO AÉREO',
     'NOTIFICACION', PLANTILLA_11),
]

MOTIVOS_RECHAZO = [
    'Falta de pasaporte o documento de identidad y viaje válido (art. 37, fr. I, inc. a), Ley de Migración; '
    'art. 60, fr. I, Reglamento).',
    'Falta de visa válida y vigente (art. 37, fr. I, inc. b), Ley de Migración; art. 60, fr. I, Reglamento).',
    'Antecedentes en México o en el extranjero que comprometen la seguridad nacional o pública '
    '(art. 43, fr. I, Ley de Migración).',
    'Incumplimiento de requisitos para la condición de estancia solicitada (art. 43, fr. II, Ley de '
    'Migración; art. 60, Reglamento).',
    'Documentos o elementos aportados no auténticos (art. 43, fr. III, Ley de Migración).',
    'Prohibición expresa de autoridad competente (art. 43, fr. IV, Ley de Migración).',
]


def sembrar(apps, schema_editor):
    DatosOficina = apps.get_model('oficios', 'DatosOficina')
    MotivoRechazo = apps.get_model('oficios', 'MotivoRechazo')
    PlantillaOficio = apps.get_model('oficios', 'PlantillaOficio')

    if not DatosOficina.objects.exists():
        DatosOficina.objects.create()  # los valores por defecto del modelo: Tijuana
    for orden, texto in enumerate(MOTIVOS_RECHAZO, start=1):
        MotivoRechazo.objects.update_or_create(texto=texto, defaults={'orden': orden, 'activo': True})
    for numero, nombre, titulo, bloque, contenido in PLANTILLAS:
        PlantillaOficio.objects.update_or_create(
            numero=numero,
            defaults={'nombre': nombre, 'titulo': titulo, 'bloque_firmas': bloque,
                      'contenido_html': contenido, 'lleva_fecha': True, 'activo': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0001_initial'),
    ]

    # Al revertir no se borra nada aquí: la 0001 elimina las tablas.
    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
