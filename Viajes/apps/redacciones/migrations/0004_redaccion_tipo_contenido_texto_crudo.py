from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('redacciones', '0003_redaccion_texto_contenido'),
    ]

    operations = [
        migrations.AddField(
            model_name='redaccion',
            name='tipo_contenido',
            field=models.CharField(choices=[('ARCHIVO', 'Archivo'), ('TEXTO', 'Texto pegado')], default='ARCHIVO', max_length=10, verbose_name='Tipo de contenido'),
        ),
        migrations.AddField(
            model_name='redaccion',
            name='texto_crudo',
            field=models.TextField(blank=True, default='', help_text='Contenido de la redacción pegado directamente (sin archivo).', verbose_name='Texto pegado'),
        ),
        migrations.AlterField(
            model_name='redaccion',
            name='archivo',
            field=models.FileField(blank=True, upload_to='redacciones/%Y/%m/', verbose_name='Documento'),
        ),
    ]
