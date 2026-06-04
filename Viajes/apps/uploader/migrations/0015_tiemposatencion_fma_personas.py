from django.db import migrations, models


class Migration(migrations.Migration):
    """Conteo manual de personas atendidas en la fila FMA.

    Se agrega `fma_personas` (PositiveIntegerField, opcional). Es un conteo
    independiente de los registros marcados como Segunda Revisión y sólo
    aplica a FMA. Se captura en el modal de Tiempos de Atención y se muestra
    en el reporte de inadmitidos junto al tiempo de la fila FMA.
    """

    dependencies = [
        ('uploader', '0014_tiemposatencion_rs_ventana'),
    ]

    operations = [
        migrations.AddField(
            model_name='tiemposatencion',
            name='fma_personas',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Personas FMA'),
        ),
    ]
