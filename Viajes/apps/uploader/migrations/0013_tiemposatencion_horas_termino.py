from django.db import migrations, models


class Migration(migrations.Migration):
    """Los rubros pasan de minutos (entero) a la HORA DE TÉRMINO (TimeField).

    Para NO perder el histórico, los minutos previos se conservan: cada columna
    entera `tiempo_<rubro>` se RENOMBRA a `tiempo_<rubro>_min_legacy` (los datos
    viajan con el renombre) y se crea una columna nueva `tiempo_<rubro>` de tipo
    hora, inicialmente vacía. El flujo nuevo escribe sólo las columnas de hora;
    las legacy quedan como respaldo de sólo lectura.
    """

    dependencies = [
        ('uploader', '0012_tiemposatencion_revisiones_secundarias'),
    ]

    operations = [
        # 1) Conservar los minutos previos renombrando las columnas.
        migrations.RenameField(
            model_name='tiemposatencion', old_name='tiempo_fma', new_name='tiempo_fma_min_legacy',
        ),
        migrations.RenameField(
            model_name='tiemposatencion', old_name='tiempo_mexicanos', new_name='tiempo_mexicanos_min_legacy',
        ),
        migrations.RenameField(
            model_name='tiemposatencion', old_name='tiempo_extranjeros', new_name='tiempo_extranjeros_min_legacy',
        ),
        migrations.RenameField(
            model_name='tiemposatencion', old_name='tiempo_revisiones_secundarias', new_name='tiempo_revisiones_secundarias_min_legacy',
        ),
        # 2) Crear las nuevas columnas de hora de término (vacías).
        migrations.AddField(
            model_name='tiemposatencion',
            name='tiempo_extranjeros',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora término Extranjeros'),
        ),
        migrations.AddField(
            model_name='tiemposatencion',
            name='tiempo_mexicanos',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora término Mexicanos'),
        ),
        migrations.AddField(
            model_name='tiemposatencion',
            name='tiempo_fma',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora término FMA'),
        ),
        migrations.AddField(
            model_name='tiemposatencion',
            name='tiempo_revisiones_secundarias',
            field=models.TimeField(blank=True, null=True, verbose_name='Hora término Revisiones Secundarias'),
        ),
    ]
