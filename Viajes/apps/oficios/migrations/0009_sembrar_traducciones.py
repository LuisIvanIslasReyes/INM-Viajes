"""
Traducciones iniciales (25/11/2026), del texto de las copias por idioma de la USB:

  02 · chino   — "chino - Victor - 02…" (idéntico al de Carrillo): título, párrafo del HACE
                 CONSTAR y leyenda de firma.
  02 · ruso    — "ruso- TELLO - 02…": ídem.
  02 · francés — "frances - Melissa - 02…": ídem (como en el original, la traducción va al
                 final del mismo párrafo, sin " / ").
  07, 08 y 09 · chino y ruso — solo la leyenda bajo la firma de la persona; el texto es el
                 mismo que el español (contenido vacío = el de la plantilla).

La traducción va en letra chica (8 pt), como en las copias oficiales. Lo que en las copias era un dato de un caso se cambió por {{variables}} (el nombre) o por un
campo «…» que se llena antes de imprimir (la nacionalidad escrita en francés). Se copió tal
cual el resto, incluido el título ruso que dice "(китайский язык)" ("idioma chino"), que
parece un error de la copia: se corrige en Oficios → Plantillas → 02 → Ruso.

Si una plantilla 02 ya se había editado y no trae el párrafo esperado, la traducción se
agrega como párrafo aparte al final. Idempotente (update_or_create).
"""
from django.db import migrations

ANCLA_02 = 'con el medio de traducción empleado.'

TRADUCCION_02 = {
    'zh': {
        'titulo': "CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO (Chino) / 使用电子翻译器的证明。（中文）",
        'texto': "该中国籍外籍人士不会说或听懂西班牙语。根据《移民法》第三十五条第二款的规定，使用 “巴斯克语翻译器 V4 电子翻译器）”品牌的电子翻译软件将其翻译成中文（该外籍人士表示其能理解和说中文），以便告知其移民程序、在此过程中享有的权利以及所需文件的内容。该外籍人士签署此文件，以确认所使用的翻译方式。",
        'separador': ' / ',
        'leyenda': 'NOMBRE Y FIRMA / 姓名和签名',
    },
    'ru': {
        'titulo': "CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO (Ruso) / СПРАВКА ОБ ИСПОЛЬЗОВАНИИ ЭЛЕКТРОННОГО ПЕРЕВОДЧИКА (китайский язык)",
        'texto': "Поскольку иностранный гражданин {{extranjero_nombre}}, гражданин(ка) России, не говорит и не понимает по-испански, в соответствии с абзацем вторым статьи 35 Закона о миграции было использовано электронное переводческое устройство марки «Vasco Translator V4 (electronic translator)» для перевода на русский язык, который он/она заявляет, что понимает и на котором говорит, с целью доведения до его/ее сведения миграционной процедуры, прав, принадлежащих ему/ей в ходе ее проведения, и содержания приобщаемых документов. Иностранный гражданин подписывает настоящий документ в знак согласия с использованным средством перевода.",
        'separador': ' / ',
        'leyenda': 'NOMBRE Y FIRMA / ФИО И ПОДПИСЬ',
    },
    'fr': {
        'titulo': "CONSTANCIA DE USO DE TRADUCTOR ELECTRÓNICO / ATTESTATION D'UTILISATION D'UN TRADUCTEUR ÉLECTRONIQUE",
        'texto': "Étant donné que la personne étrangère nommée {{extranjero_nombre}}, de nationalité «NATIONALITÉ EN FRANÇAIS», ne parle ni ne comprend l'espagnol, un appareil électronique de traduction, marque \"Vasco Translator V4 (electronic translator)\", a été utilisé, conformément à l'article 35, paragraphe deux, de la Loi sur l'immigration, pour traduire en français, langue qu'elle déclare comprendre et parler, afin de lui faire connaître la procédure migratoire, les droits dont elle bénéficie au cours de celle-ci et le contenu des documents établis. La personne étrangère signe le présent document en signe de conformité avec le moyen de traduction utilisé.",
        'separador': ' ',
        'leyenda': 'NOMBRE Y FIRMA / NOM ET SIGNATURE',
    },
}

# (número de plantilla, idioma, leyenda): mismo texto que el español, solo la leyenda traducida.
SOLO_LEYENDA = [
    (7, 'zh', 'NOMBRE Y FIRMA / 姓名和签名'),
    (7, 'ru', 'NOMBRE Y FIRMA / ФИО И ПОДПИСЬ'),
    (8, 'zh', 'NOMBRE Y FIRMA / 姓名和签名'),
    (8, 'ru', 'NOMBRE Y FIRMA / ФИО И ПОДПИСЬ'),
    (9, 'zh', 'NOMBRE COMPLETO Y FIRMA / 姓名及签名'),
    (9, 'ru', 'NOMBRE Y FIRMA / ФИО И ПОДПИСЬ'),
]


def _texto_02(base, traduccion):
    """El texto en español con la traducción pegada al final del párrafo del HACE CONSTAR."""
    i = base.find(ANCLA_02)
    if i >= 0:
        fin = base.find('</p>', i)
        if fin >= 0:
            return base[:fin] + traduccion['separador'] + _chico(traduccion['texto']) + base[fin:]
    return base + f'<p class="ql-align-justify">{_chico(traduccion["texto"])}</p>'


def _chico(texto):
    """La traducción a 8 pt, como en los Word oficiales (el español va a 9.5 pt)."""
    return f'<span class="ql-size-small">{texto}</span>'


def sembrar(apps, schema_editor):
    PlantillaOficio = apps.get_model('oficios', 'PlantillaOficio')
    PlantillaOficioIdioma = apps.get_model('oficios', 'PlantillaOficioIdioma')

    p02 = PlantillaOficio.objects.filter(numero=2).first()
    if p02:
        for idioma, traduccion in TRADUCCION_02.items():
            PlantillaOficioIdioma.objects.update_or_create(
                plantilla=p02, idioma=idioma,
                defaults={'titulo': traduccion['titulo'], 'contenido_html': _texto_02(p02.contenido_html, traduccion),
                          'leyenda_firma_persona': traduccion['leyenda'], 'activo': True},
            )
    for numero, idioma, leyenda in SOLO_LEYENDA:
        plantilla = PlantillaOficio.objects.filter(numero=numero).first()
        if plantilla:
            PlantillaOficioIdioma.objects.update_or_create(
                plantilla=plantilla, idioma=idioma,
                defaults={'titulo': '', 'contenido_html': '', 'leyenda_firma_persona': leyenda, 'activo': True},
            )


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0008_traducciones'),
    ]

    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
