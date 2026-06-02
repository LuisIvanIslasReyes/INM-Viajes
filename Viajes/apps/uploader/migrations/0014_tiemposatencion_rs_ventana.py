from django.db import migrations, models


class Migration(migrations.Migration):
    """Revisiones Secundarias pasa a tener su propia ventana Inicio/Fin.

    Se agregan `rs_hora_inicio` y `rs_hora_fin` (TimeField). La duración de RS
    se deriva como la diferencia entre ambas. El campo anterior
    `tiempo_revisiones_secundarias` (hora término única) se conserva por
    compatibilidad histórica; sólo cambia su verbose_name a "(legacy)".
    """

    dependencies = [
        ('uploader', '0013_tiemposatencion_horas_termino'),
    ]

    operations = [
        migrations.AddField(
            model_name='tiemposatencion',
            name='rs_hora_inicio',
            field=models.TimeField(blank=True, null=True, verbose_name='RS Hora Inicio'),
        ),
        migrations.AddField(
            model_name='tiemposatencion',
            name='rs_hora_fin',
            field=models.TimeField(blank=True, null=True, verbose_name='RS Hora Fin'),
        ),
        migrations.AlterField(
            model_name='tiemposatencion',
            name='tiempo_revisiones_secundarias',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora término Revisiones Secundarias (legacy)'),
        ),
    ]
