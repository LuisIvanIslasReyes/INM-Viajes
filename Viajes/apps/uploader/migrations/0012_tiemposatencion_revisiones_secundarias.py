from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0011_tiemposatencion'),
    ]

    operations = [
        migrations.AddField(
            model_name='tiemposatencion',
            name='tiempo_revisiones_secundarias',
            field=models.PositiveIntegerField(default=0, verbose_name='Tiempo Revisiones Secundarias (min)'),
        ),
    ]
