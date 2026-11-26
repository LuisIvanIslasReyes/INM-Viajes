"""
Plantillas 08, 09, 12, 13 y 14 (25/11/2026), del texto de los Word oficiales de la USB:

  08. CONSTANCIA LLAMADA PERSONAL.docx
  09. CONSTANCIA DE VERIFICACIÓN DE INFORMACIÓN  - FOTO - VARIOS.docx
  12. CONSTANCIA NEGATIVA DE FIRMA.docx
  13. NOTIFICACIÓN A LA EMPRESA_SOLICITUD DE ALIMENTOS Y RUTA.docx
  14. ACUERDO DE EJECUCIÓN DE ACTA DE RECHAZO.docx

Con los controles de contenido cambiados por {{variables}} y lo que se llena en cada caso
entre «…» (no deja imprimir hasta llenarlo). Lo que en el papel se escribe a mano queda
con guiones bajos o `[[ RENGLÓN ]]`. Mismas negritas que los originales.

El texto del 14 se copia TAL CUAL, incluidos dos errores del original ("…del Instituto
Nacional de publicado…" y "…se determina la y circunscripción…"), que también aparecen
en el acta firmada AR000316. Se corrigen en la pantalla de plantillas si así se decide.

Copia congelada; las correcciones posteriores se hacen en la pantalla de plantillas.
"""
from django.db import migrations

J = 'class="ql-align-justify"'
C = 'class="ql-align-center"'
NB = ' ' * 6  # separación entre datos en el mismo renglón (no se colapsa)

APERTURA = (
    f'<p {J}>En {{{{ciudad_encabezado}}}}, siendo el día {{{{fecha_larga}}}}, {{{{firmante_el_la}}}} que suscribe '
    '{{firmante_nombre}}, {{firmante_cargo}} {{firmante_adscrito}} al <strong>Instituto Nacional de Migración</strong> '
    'en el {{aeropuerto}}, quien actúa legalmente con los testigos de asistencia que firman para debida constancia, '
    'constituidos en la oficina que ocupa la <strong>Subrepresentación Local</strong>, sito en la zona considerada '
    'como estéril, en el interior del citado aeropuerto, ubicado en {{domicilio}}. --</p>'
    '<p>[[ ]]</p>'
)

FUNDAMENTO_LLAMADAS = (
    f'<p {J}>Con fundamento en los artículos 19 y 20, fracción II, de la Ley de Migración; 27, fracción V, de la '
    'Ley Orgánica de la Administración Pública Federal; 3, apartado B, fracción III, 142, último párrafo, y 162, '
    'último párrafo, del Reglamento Interior de la Secretaría de Gobernación, publicado en el Diario Oficial de la '
    'Federación el 21 de marzo de 2025; y {{firmante_fundamento}} del ACUERDO por el que se delegan atribuciones '
    'para autorizar trámites migratorios y ejercer diversas atribuciones previstas en la Ley de Migración y su '
    'Reglamento a los servidores públicos adscritos a las Delegaciones Federales del Instituto Nacional de '
    'Migración, publicado en el Diario Oficial de la Federación en fecha 13 de noviembre 2012. --</p>'
)

FUNDAMENTO_CONSTANCIAS = (
    f'<p {J}>Con fundamento en lo dispuesto en los artículos 19, 20, fracción II, de la Ley de Migración, 27, '
    'fracción V, de la Ley Orgánica de la Administración Pública Federal, 3, inciso B), fracción III, 142, último '
    'párrafo y 162, último párrafo, del Reglamento Interior de la Secretaría de Gobernación vigente (D.O.F. '
    '21/03/2025) y {{firmante_fundamento}} del ACUERDO por el que se delegan atribuciones para autorizar trámites '
    'migratorios y ejercer diversas atribuciones previstas en la Ley de Migración y su Reglamento a los servidores '
    'públicos adscritos a las Delegaciones Federales del Instituto Nacional de Migración, publicado en el Diario '
    'Oficial de la Federación en fecha 13 de noviembre 2012. --</p>'
)

PLANTILLA_08 = (
    APERTURA + FUNDAMENTO_LLAMADAS
    + '<p>[[ HACE CONSTAR ]]</p>'
    f'<p {J}>Que, en observancia de las garantías aplicables durante el procedimiento de segunda revisión y con la '
    'finalidad de procurar que la persona cuente con medios de comunicación durante el desarrollo de la diligencia, '
    'se hizo del conocimiento de <strong>{{extranjero_nombre}}</strong>, de nacionalidad '
    '{{extranjero_nacionalidad}}, la posibilidad de realizar una comunicación telefónica de carácter personal con '
    'un familiar, persona de confianza o contacto de su elección; lo cual le fue informado verbalmente durante la '
    'segunda revisión y, previamente, por escrito al completar su cuestionario, manifestando libremente su '
    'voluntad de:</p>'
    f'<p {C}><strong>REALIZARLA:</strong> ☐{NB}{NB}<strong>NO REALIZARLA:</strong> ☐</p>'
    '<p>Nombre de la persona con quien se comunicó: ____________________ Relación o vínculo: '
    '____________________</p>'
    '<p>Hora de la comunicación: ____________________</p>'
    '<p>[[ SE CIERRA Y SE AUTORIZA LO ACTUADO ]]</p>'
)

PLANTILLA_09 = (
    '<p>[[ TABLA ]]</p>'
    f'<p {C}><strong>Fecha:</strong> {{{{fecha_larga}}}}{NB}<strong>Hora:</strong> ____________</p>'
    '<p><strong>Nombre:</strong> {{extranjero_nombre}}</p>'
    '<p><strong>Nacionalidad:</strong> {{extranjero_nacionalidad}}</p>'
    '<p><strong>Verificación realizada a:</strong> <em>(persona que lo invita o expide la carta invitación, '
    'empresa, hotel, aerolínea, sitio oficial, etc.)</em> __</p>'
    '<p><strong>Hora:</strong> ____________</p>'
    f'<p {J}><strong>Requisito que se busca acreditar: Domicilio y tiempo de estancia, motivo de viaje, medio de '
    'transporte de salida del país, actividades a realizar</strong></p>'
    f'<p><strong>¿Se recibió respuesta?{NB}Sí:</strong> ☐{NB}<strong>No:</strong> ☐{NB}'
    '<strong>Número de intentos:</strong> ________</p>'
    '<p>[[ /TABLA ]]</p>'
    '<p><br></p>'
    f'<p {J}><strong>Observaciones: (Información obtenida posterior de la llamada e inconsistencias con la '
    'información proporcionada por la persona extranjera).</strong></p>'
    '<p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p>'
    '<p><br></p>'
    '<p><strong>Evidencia documental:</strong></p>'
    '<p>[[ RECUADRO ]]</p>'
    '<p><br></p><p><br></p><p><br></p><p><br></p><p><br></p><p><br></p>'
    f'<p {C}><em>(Fotografía del registro de llamadas dentro del teléfono de oficina o de información obtenida '
    'en páginas de internet)</em></p>'
    f'<p {C}><em>(SE ANEXA LA EVIDENCIA DOCUMENTAL EFECTUADA)</em></p>'
    '<p>[[ /RECUADRO ]]</p>'
    '<p><br></p>'
    f'<p {J}><strong>Lo anterior, con la finalidad de dar cuenta que se realizó la llamada telefónica '
    'correspondiente a la verificación de la información otorgada por la persona en segunda revisión, conforme al '
    'artículo 60 del Reglamento de la Ley de Migración y 21 de los Lineamientos para Trámites y Procedimientos '
    'Migratorios.</strong></p>'
)

PLANTILLA_12 = (
    APERTURA + FUNDAMENTO_CONSTANCIAS
    + '<p>[[ HACE CONSTAR ]]</p>'
    f'<p {J}>Que en presencia de la persona extranjera {{{{extranjero_nombre}}}}, de nacionalidad '
    '{{extranjero_nacionalidad}}, y los testigos de asistencia, se dio lectura y se hizo de su conocimiento el '
    'contenido y alcance del acta de rechazo aéreo emitida a su nombre, en la que se determinó negar su internación '
    'a territorio nacional con motivo de los hechos, circunstancias y fundamentos jurídicos asentados en dicho '
    'instrumento, de conformidad con la Ley de Migración, su Reglamento y demás disposiciones aplicables. Acto '
    'seguido, se solicitó a la persona en segunda revisión firmar el acta de rechazo número '
    '<strong>{{numero_acta}}</strong>, así como las constancias que integran la diligencia; sin embargo, manifestó '
    'su negativa a firmarlas por así convenir a sus intereses, circunstancia que se hace constar para los efectos '
    'legales conducentes. No habiendo otro hecho que hacer constar, se da por concluida la presente diligencia, '
    'firmando al calce las personas que en ella intervienen para debida constancia: --</p>'
    '<p>[[ CONSTE | SE CIERRA Y SE AUTORIZA LO ACTUADO ]]</p>'
)

PLANTILLA_13 = (
    '<p><strong>EMPRESA TRANSPORTISTA</strong></p>'
    '<p><strong>P R E S E N T E.</strong></p>'
    '<p><br></p>'
    f'<p {J}>Por este conducto, se hace de su conocimiento que el Instituto Nacional de Migración, a través de la '
    'autoridad migratoria adscrita al {{aeropuerto}}, determinó el rechazo a territorio nacional de la persona '
    'extranjera cuyos datos se precisan a continuación, misma que arribó a este aeródromo internacional en el vuelo '
    'que opera su representada con los datos siguientes:</p>'
    '<p><br></p>'
    f'<p><strong>Nombre:</strong> {{{{extranjero_nombre}}}}{NB}<strong>Nacionalidad:</strong> '
    '{{extranjero_nacionalidad}}</p>'
    f'<p><strong>Fecha de nacimiento:</strong> {{{{extranjero_fecha_nacimiento}}}}{NB}<strong>Número de pasaporte '
    'o documento de viaje:</strong> {{extranjero_documento}}</p>'
    '<p><br></p>'
    '<p><strong>DATOS DEL ARRIBO</strong></p>'
    f'<p><strong>Fecha de arribo:</strong> {{{{fecha_arribo}}}}.{NB}<strong>Número de vuelo:</strong> '
    f'{{{{vuelo}}}}{NB}<strong>Origen:</strong> {{{{origen}}}}</p>'
    '<p><br></p>'
    f'<p {J}>Con fundamento en los artículos 42, fracción IX, 78 y 79 del Reglamento de la Ley de Migración, en '
    'este acto se notifica a esa empresa transportista la resolución mediante la cual se determinó el rechazo de la '
    'persona extranjera, para los efectos legales y operativos correspondientes. En consecuencia, se solicita '
    'proporcionar la custodia y alimentación necesarias durante el tiempo que transcurra hasta la ejecución '
    'material del rechazo, considerando, cuando corresponda, requerimientos específicos derivados de prescripción '
    'médica, prácticas religiosas o alguna condición de vulnerabilidad.</p>'
    f'<p {J}>Asimismo, se requiere informar oportunamente a esta autoridad migratoria el vuelo, fecha, horario, '
    'ruta y destino mediante los cuales se efectuará la salida de la persona extranjera del territorio nacional, a '
    'efecto de dar seguimiento a la ejecución del rechazo dentro del plazo previsto en la normativa aplicable.</p>'
    '<p><br></p>'
    f'<p {C}><strong>ACUSE DE NOTIFICACIÓN Y PROGRAMACIÓN DE SALIDA</strong></p>'
    f'<p {J}>El día {{{{fecha_larga}}}}, se notifica a la aerolínea {{{{aerolinea}}}}, por conducto de '
    '«NOMBRE DEL REPRESENTANTE», quien se desempeña con el cargo de «CARGO DEL REPRESENTANTE» en el '
    '{{aeropuerto}}, y en este acto se identifica con <strong>Tarjeta de Identificación Aeroportuaria</strong>, '
    'número ____________________ recibiendo el original del presente documento, manifestando que su representada '
    'se da por notificada del contenido del mismo, e informa a esta autoridad que el vuelo en que la persona '
    'extranjera de referencia abandonará el país será el <strong>número «VUELO DE SALIDA»</strong> del '
    '<strong>día «FECHA DE SALIDA»</strong>, a las <strong>«HORA DE SALIDA»</strong> horas, con destino a '
    '<strong>«DESTINO»</strong>.</p>'
    '<p>[[ FIRMA: NOMBRE Y FIRMA DEL REPRESENTANTE DE LA EMPRESA TRANSPORTISTA ]]</p>'
    '<p>[[ NUEVA HOJA ]]</p>'
    f'<p {C}><strong>REQUERIMIENTOS DE ALIMENTACIÓN DURANTE LA EJECUCIÓN DEL RECHAZO</strong></p>'
    '<p><br></p>'
    f'<p {J}>Con fundamento en el artículo 78 del Reglamento de la Ley de Migración, se hace constar el tipo de '
    'alimentación que deberá proporcionarse a la persona extranjera durante el tiempo que transcurra hasta la '
    'ejecución material del rechazo.</p>'
    '<p><br></p>'
    '<p><strong>TIPO DE ALIMENTACIÓN:</strong></p>'
    '<p><strong>☐ ALIMENTACIÓN REGULAR</strong></p>'
    '<p><strong>☐ ALIMENTACIÓN CON REQUERIMIENTOS ESPECÍFICOS</strong></p>'
    '<p><br></p>'
    '<p><strong>EN CASO DE ALIMENTACIÓN ESPECIAL, INDIQUE EL MOTIVO:</strong></p>'
    f'<p {C}><strong>☐ Prescripción médica{NB}☐ Práctica o restricción religiosa{NB}☐ Condición de '
    f'vulnerabilidad{NB}☐ Otro</strong></p>'
    '<p><br></p>'
    '<p><strong>ESPECIFICACIONES U OBSERVACIONES:</strong></p>'
    '<p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p><p>[[ RENGLÓN ]]</p>'
)

PLANTILLA_14 = (
    APERTURA
    + f'<p {J}>Con fundamento en lo dispuesto los artículos 1º, 11, 14, 16, 90, párrafo primero, de la Constitución '
    'Política de los Estados Unidos Mexicanos: 17, 17 Bis, 26 y 27 V de la Ley Orgánica de la Administración Pública '
    'Federal; 3, fracciones l, XII, y XV, 16, fracción II, 19, 20, fracciones II y III, 34, 35, 36, 37, 40, 43, 87 y '
    '88 de la Ley de Migración; 3, fracciones II, IX, XXI y XXV 55, 57, 58, 59, 60, 65, 78, 79, 81, de su '
    'Reglamento; 3, apartado B, fracción III, 128, 142, último párrafo 162, fracciones l, IV y último párrafo y '
    'Quinto Transitorio del Reglamento de la Secretaria de Gobernación, y {{firmante_fundamento}}, del Acuerdo por '
    'el que se delegan atribuciones para autorizar trámites migratorios y ejercer atribuciones previstas en la Ley '
    'de Migración y su Reglamento a los servidores públicos adscritos a las Delegaciones del Instituto Nacional de '
    'publicado en el Diario Oficial de Federación del día 13 de noviembre de 2012; el ACUERDO por el que se '
    'determina la y circunscripción territorial de las Delegaciones y Subdelegaciones Federales y Locales del '
    'Instituto Nacional de Migración vigente y en cumplimiento a lo ordenado en el acta No. '
    '<strong>{{numero_acta}}</strong>, esta autoridad migratoria determinó el rechazo aéreo de la persona extranjera '
    '<strong>{{extranjero_nombre}}</strong>, de nacionalidad {{extranjero_nacionalidad}}, quien arribó a territorio '
    'nacional en el vuelo {{vuelo}}, de la línea aérea {{aerolinea}}; conforme a las circunstancias, hechos y '
    'fundamentos asentados en el acta de rechazo de referencia, corresponde proceder a la ejecución material de '
    'dicha determinación. --</p>'
    f'<p {J}>Toda vez que no existe una opción de vuelo desde el aeropuerto de arribo que permita materializar el '
    'rechazo dentro de las veinticuatro horas siguientes, la empresa transportista responsable de su ejecución '
    'proporcionó una alternativa que permite efectuar oportunamente la salida de la persona extranjera del '
    'territorio nacional, a efecto de evitar prolongar innecesariamente su permanencia y atender al plazo previsto '
    'en el artículo 79 del Reglamento de la Ley de Migración.</p>'
    f'<p {J}>La alternativa proporcionada tendrá como única finalidad dar continuidad a la ejecución material del '
    'rechazo, sin que ello implique autorización de internación ni modificación alguna de la determinación '
    'previamente adoptada, privilegiando su ejecución oportuna y evitando una permanencia mayor a la estrictamente '
    'necesaria. --</p>'
    '<p>[[ ACUERDA ]]</p>'
    f'<p {J}><strong>ÚNICO. –</strong> Ejecútese el acta de rechazo No. <strong>{{{{numero_acta}}}}</strong>, '
    'emitida a la persona extranjera {{extranjero_nombre}}, de nacionalidad {{extranjero_nacionalidad}}, mediante '
    'la ruta {{aeropuerto}} – «CONEXIÓN Y DESTINO», en los vuelos «VUELOS DE SALIDA» proporcionados por la línea '
    'aérea {{aerolinea}}, permaneciendo la persona extranjera de mérito bajo custodia de personal adscrito a esta '
    '<strong>SUB REPRESENTACIÓN LOCAL</strong>, hasta en tanto la determinación de rechazo cause ejecución. --</p>'
    '<p>[[ CÚMPLASE ]]</p>'
    f'<p {J}>Así lo acuerda y firma, {{{{firmante_el_la}}}} {{{{firmante_nombre}}}}, {{{{firmante_cargo}}}} '
    '{{firmante_adscrito}} al <strong>Instituto Nacional de Migración</strong> en el {{aeropuerto}}, quien actúa '
    'legalmente con los testigos de asistencia, constituidos en la oficina que ocupa la <strong>Sub Representación '
    'Local</strong>, así como autoridades de la línea aérea {{aerolinea}} que firman al margen para constancia del '
    'presente acto. --</p>'
)

PLANTILLAS = [
    # numero, nombre, titulo, bloque_firmas, lleva_fecha, contenido
    (8, 'Constancia de llamada personal', 'CONSTANCIA DE LLAMADA PERSONAL', 'CONSTANCIA', False, PLANTILLA_08),
    (9, 'Constancia de verificación de información', 'CONSTANCIA DE VERIFICACIÓN DE INFORMACIÓN',
     'AUTORIDAD_PERSONA', True, PLANTILLA_09),
    (12, 'Constancia de negativa de firma', 'CONSTANCIA DE NEGATIVA DE FIRMA DE LA PERSONA', 'CONSTANCIA', True,
     PLANTILLA_12),
    (13, 'Notificación a la empresa: alimentos y ruta',
     'NOTIFICACIÓN A LA EMPRESA TRANSPORTISTA DE DETERMINACIÓN DE RECHAZO, SOLICITUD DE ALIMENTACIÓN Y '
     'PROGRAMACIÓN DE SALIDA', 'EMPRESA', True, PLANTILLA_13),
    (14, 'Acuerdo de ejecución de acta de rechazo', 'ACUERDO DE EJECUCIÓN DE ACTA DE RECHAZO', 'ACUERDO', True,
     PLANTILLA_14),
]


def sembrar(apps, schema_editor):
    PlantillaOficio = apps.get_model('oficios', 'PlantillaOficio')
    for numero, nombre, titulo, bloque, lleva_fecha, contenido in PLANTILLAS:
        PlantillaOficio.objects.update_or_create(
            numero=numero,
            defaults={'nombre': nombre, 'titulo': titulo, 'bloque_firmas': bloque, 'lleva_fecha': lleva_fecha,
                      'contenido_html': contenido, 'activo': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0005_persona_arribo_y_firmas'),
    ]

    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
