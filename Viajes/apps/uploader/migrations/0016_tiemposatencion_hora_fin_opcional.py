from django.db import migrations, models


class Migration(migrations.Migration):
    """Hora Fin deja de ser obligatoria en la captura de Tiempos de Atención.

    El operador puede guardar la captura inicial sin conocer aún la hora de
    cierre y completarla después.
    """

    dependencies = [
        ('uploader', '0015_tiemposatencion_fma_personas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tiemposatencion',
            name='hora_fin',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora Fin'),
        ),
    ]
