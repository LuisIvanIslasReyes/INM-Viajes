"""
D-144 de la Estancia: la plaza trae `plaza_descripcion` y el cargo impreso sale de
la plaza (ahora es una propiedad), así que la columna `cargo` (que guardaba la
jerarquía) pasa a llamarse `jerarquia`. Además, la bitácora guarda el modo y el
`proximo_desde` para la sincronización incremental.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(model_name='empleado', old_name='cargo', new_name='jerarquia'),
        migrations.AlterField(
            model_name='empleado',
            name='jerarquia',
            field=models.CharField(
                blank=True, default='', max_length=150,
                help_text='Jerarquía principal vigente en la Estancia (la labor, ej. AFM).',
            ),
        ),
        migrations.AlterField(
            model_name='empleado',
            name='plaza',
            field=models.CharField(
                blank=True, default='', max_length=150,
                help_text='Puesto genérico de la plaza en la Estancia (ej. JEFE DE DEPARTAMENTO).',
            ),
        ),
        migrations.AddField(
            model_name='empleado',
            name='plaza_descripcion',
            field=models.CharField(
                blank=True, default='', max_length=250,
                help_text='La plaza concreta (ej. JEFATURA DE DEPARTAMENTO DE RECURSOS HUMANOS).',
            ),
        ),
        migrations.AddField(
            model_name='sincronizacionempleados',
            name='modo',
            field=models.CharField(
                choices=[('COMPLETA', 'Completa'), ('INCREMENTAL', 'Incremental')],
                default='COMPLETA', max_length=12,
            ),
        ),
        migrations.AddField(
            model_name='sincronizacionempleados',
            name='proximo_desde',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='Lo devuelve la Estancia; la siguiente incremental pide los cambios desde aquí.',
            ),
        ),
    ]
