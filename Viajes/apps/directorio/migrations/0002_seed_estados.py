"""Siembra los 32 estados de México en el catálogo EstadoMexico.

Idempotente: usa get_or_create.
"""
from django.db import migrations

ESTADOS = [
    ('AGS', 'Aguascalientes'),
    ('BC', 'Baja California'),
    ('BCS', 'Baja California Sur'),
    ('CAMP', 'Campeche'),
    ('COAH', 'Coahuila'),
    ('COL', 'Colima'),
    ('CHIS', 'Chiapas'),
    ('CHIH', 'Chihuahua'),
    ('CDMX', 'Ciudad de México'),
    ('DGO', 'Durango'),
    ('GTO', 'Guanajuato'),
    ('GRO', 'Guerrero'),
    ('HGO', 'Hidalgo'),
    ('JAL', 'Jalisco'),
    ('MEX', 'México'),
    ('MICH', 'Michoacán'),
    ('MOR', 'Morelos'),
    ('NAY', 'Nayarit'),
    ('NL', 'Nuevo León'),
    ('OAX', 'Oaxaca'),
    ('PUE', 'Puebla'),
    ('QRO', 'Querétaro'),
    ('QROO', 'Quintana Roo'),
    ('SLP', 'San Luis Potosí'),
    ('SIN', 'Sinaloa'),
    ('SON', 'Sonora'),
    ('TAB', 'Tabasco'),
    ('TAMPS', 'Tamaulipas'),
    ('TLAX', 'Tlaxcala'),
    ('VER', 'Veracruz'),
    ('YUC', 'Yucatán'),
    ('ZAC', 'Zacatecas'),
]


def sembrar_estados(apps, schema_editor):
    EstadoMexico = apps.get_model('directorio', 'EstadoMexico')
    for clave, nombre in ESTADOS:
        EstadoMexico.objects.get_or_create(clave=clave, defaults={'nombre': nombre})


def borrar_estados(apps, schema_editor):
    EstadoMexico = apps.get_model('directorio', 'EstadoMexico')
    EstadoMexico.objects.filter(clave__in=[c for c, _ in ESTADOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('directorio', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sembrar_estados, borrar_estados),
    ]
