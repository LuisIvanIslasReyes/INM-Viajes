"""Fecha de arribo y origen en la persona (oficio 13), y los bloques de firmas AUTORIDAD_PERSONA (09) y ACUERDO (14)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0004_plantilla_07_y_recuadro_11'),
    ]

    operations = [
        migrations.AddField(
            model_name='personaexpediente',
            name='fecha_arribo',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='personaexpediente',
            name='origen',
            field=models.CharField(blank=True, default='', help_text='Ej. PEKÍN, CHINA.', max_length=100),
        ),
        migrations.AlterField(
            model_name='plantillaoficio',
            name='bloque_firmas',
            field=models.CharField(choices=[('CONSTANCIA', 'Constancia: autoridad, persona extranjera y 2 testigos'), ('NOTIFICACION', 'Notificación: atentamente y "recibí original"'), ('EMPRESA', 'Empresa: representante de la aerolínea y autoridad'), ('AUTORIDAD_PERSONA', 'Autoridad y persona extranjera (sin testigos)'), ('ACUERDO', 'Acuerdo: autoridad, persona, representante de la aerolínea y 2 testigos'), ('NINGUNO', 'Sin firmas')], default='CONSTANCIA', max_length=20),
        ),
    ]
