"""
Tamaño de letra por plantilla, el de cada Word oficial (w:sz del cuerpo): 02, 07 y 08 a
9.5 pt; 09, 12, 13 y 14 a 9 pt; 11 a 10 pt. Con 10 pt para todos, los formatos largos se
pasaban de hoja (ej. los testigos del 12 en una hoja aparte).
"""
from decimal import Decimal

import django.core.validators
from django.db import migrations, models


TAMANOS = {2: '9.5', 7: '9.5', 8: '9.5', 9: '9', 11: '10', 12: '9', 13: '9', 14: '9'}


def asignar(apps, schema_editor):
    PlantillaOficio = apps.get_model('oficios', 'PlantillaOficio')
    for numero, tamano in TAMANOS.items():
        PlantillaOficio.objects.filter(numero=numero).update(tamano_letra_pt=Decimal(tamano))


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0006_plantillas_08_09_12_13_14'),
    ]

    operations = [
        migrations.AddField(
            model_name='plantillaoficio',
            name='tamano_letra_pt',
            field=models.DecimalField(decimal_places=1, default=Decimal('10'), help_text='El del Word oficial (9 a 10 pt). Más chico si el oficio no cabe en sus hojas.', max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal('8')), django.core.validators.MaxValueValidator(Decimal('12'))], verbose_name='tamaño de letra (pt)'),
        ),
        migrations.RunPython(asignar, migrations.RunPython.noop),
    ]
