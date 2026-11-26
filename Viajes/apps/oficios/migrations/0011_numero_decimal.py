"""El número de plantilla pasa a decimal para el 04.1 (cuestionario para residentes)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0010_evidencias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plantillaoficio',
            name='numero',
            field=models.DecimalField(decimal_places=1, help_text='Ej. 2, 11 o 4.1.', max_digits=4, unique=True),
        ),
    ]
