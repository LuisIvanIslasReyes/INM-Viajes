from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0010_registro_es_menor_alter_uploadbatch_archivo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TiemposAtencion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(unique=True, verbose_name='Fecha')),
                ('hora_inicio', models.TimeField(verbose_name='Hora Inicio')),
                ('hora_fin', models.TimeField(verbose_name='Hora Fin')),
                ('tiempo_extranjeros', models.PositiveIntegerField(default=0, verbose_name='Tiempo Extranjeros (min)')),
                ('tiempo_mexicanos', models.PositiveIntegerField(default=0, verbose_name='Tiempo Mexicanos (min)')),
                ('tiempo_fma', models.PositiveIntegerField(default=0, verbose_name='Tiempo FMA (min)')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='tiempos_atencion', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tiempos de Atención',
                'verbose_name_plural': 'Tiempos de Atención',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddIndex(
            model_name='tiemposatencion',
            index=models.Index(fields=['fecha'], name='uploader_ti_fecha_d42c61_idx'),
        ),
    ]
