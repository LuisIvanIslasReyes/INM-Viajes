"""Evidencias de la persona por formato (09 y 05) y el tipo de evidencia de cada plantilla."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('camara', '0001_initial'),
        ('oficios', '0009_sembrar_traducciones'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='plantillaoficio',
            name='evidencias',
            field=models.CharField(blank=True, choices=[('', 'Sin evidencias'), ('VERIFICACION', 'Verificación (a quién, hora, respuesta, intentos) y foto'), ('FOTO', 'Foto y observaciones')], default='', help_text='Si el formato lleva evidencias de la persona; se imprimen donde el texto dice [[ EVIDENCIAS ]].', max_length=12),
        ),
        migrations.CreateModel(
            name='Evidencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=0)),
                ('verificacion_a', models.CharField(blank=True, default='', help_text='Persona que invita, empresa, hotel, aerolínea, sitio oficial…', max_length=250, verbose_name='verificación realizada a')),
                ('hora', models.CharField(blank=True, default='', help_text='HH:MM', max_length=10)),
                ('respuesta', models.CharField(blank=True, choices=[('', 'Sin dato'), ('SI', 'Sí'), ('NO', 'No')], default='', max_length=2, verbose_name='¿se recibió respuesta?')),
                ('intentos', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='número de intentos')),
                ('nota', models.TextField(blank=True, default='', verbose_name='observaciones')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='oficios/evidencias/%Y/%m/')),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('creada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('foto_rechazo', models.ForeignKey(blank=True, help_text='Foto de la app Cámara de la que se tomó.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='camara.fotorechazo')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidencias', to='oficios.personaexpediente')),
                ('plantilla', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='oficios.plantillaoficio')),
            ],
            options={
                'verbose_name': 'Evidencia',
                'verbose_name_plural': 'Evidencias',
                'ordering': ['orden', 'pk'],
            },
        ),
    ]
