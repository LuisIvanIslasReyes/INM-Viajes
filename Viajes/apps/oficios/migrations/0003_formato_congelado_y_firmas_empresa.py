"""snap_formato (título, firmas y fecha congelados al imprimir) y el bloque de firmas EMPRESA (oficio 13)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0002_sembrar'),
    ]

    operations = [
        migrations.AddField(
            model_name='oficioinstancia',
            name='snap_formato',
            field=models.JSONField(blank=True, help_text='Título, firmas y fecha de la plantilla al imprimir (por si después cambia la plantilla).', null=True),
        ),
        migrations.AlterField(
            model_name='plantillaoficio',
            name='bloque_firmas',
            field=models.CharField(choices=[('CONSTANCIA', 'Constancia: autoridad, persona extranjera y 2 testigos'), ('NOTIFICACION', 'Notificación: atentamente y "recibí original"'), ('EMPRESA', 'Empresa: representante de la aerolínea y autoridad'), ('NINGUNO', 'Sin firmas')], default='CONSTANCIA', max_length=15),
        ),
    ]
