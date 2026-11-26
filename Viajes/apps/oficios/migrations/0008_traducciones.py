"""Traducciones por idioma (PlantillaOficioIdioma) e historial de versiones de plantillas y traducciones."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0007_tamano_letra'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantillaHistorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idioma', models.CharField(choices=[('es', 'Español'), ('zh', 'Chino'), ('ru', 'Ruso'), ('fr', 'Francés'), ('en', 'Inglés'), ('ar', 'Árabe')], default='es', max_length=2)),
                ('titulo', models.CharField(blank=True, default='', max_length=300)),
                ('contenido_html', models.TextField(blank=True, default='')),
                ('leyenda_firma_persona', models.CharField(blank=True, default='', max_length=150)),
                ('fecha_hora', models.DateTimeField(auto_now_add=True)),
                ('plantilla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='oficios.plantillaoficio')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Versión de plantilla',
                'verbose_name_plural': 'Versiones de plantillas',
                'ordering': ['-fecha_hora', '-pk'],
            },
        ),
        migrations.CreateModel(
            name='PlantillaOficioIdioma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idioma', models.CharField(choices=[('zh', 'Chino'), ('ru', 'Ruso'), ('fr', 'Francés'), ('en', 'Inglés'), ('ar', 'Árabe')], max_length=2)),
                ('titulo', models.CharField(blank=True, default='', help_text='Título bilingüe, ej. "CONSTANCIA … (Chino) / 使用电子翻译器的证明". Vacío: el de la plantilla.', max_length=300)),
                ('contenido_html', models.TextField(blank=True, default='', help_text='Texto bilingüe con las mismas {{variables}}. Vacío: el mismo texto en español de la plantilla.')),
                ('leyenda_firma_persona', models.CharField(blank=True, default='', help_text='Bajo la firma de la persona extranjera, ej. "NOMBRE Y FIRMA / 姓名和签名".', max_length=150)),
                ('activo', models.BooleanField(default=True)),
                ('modificado_en', models.DateTimeField(auto_now=True)),
                ('modificado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('plantilla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variantes', to='oficios.plantillaoficio')),
            ],
            options={
                'verbose_name': 'Traducción de plantilla',
                'verbose_name_plural': 'Traducciones de plantillas',
                'ordering': ['plantilla__numero', 'idioma'],
                'constraints': [models.UniqueConstraint(fields=('plantilla', 'idioma'), name='una_traduccion_por_idioma')],
            },
        ),
    ]
