"""
Fundamento legal por plaza del firmante: catálogo `FundamentoPlaza` (propio de
Viajes) y `Empleado.fundamento_manual` para asignarlo a mano. Las 6 filas
iniciales las siembra la 0004.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0002_plaza_descripcion_sincronizacion_incremental'),
    ]

    operations = [
        migrations.CreateModel(
            name='FundamentoPlaza',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.SlugField(max_length=30, unique=True)),
                ('nombre', models.CharField(help_text='Ej. Representante Local.', max_length=100)),
                ('texto', models.CharField(help_text='Tal como se imprime en el oficio, ej. "Artículo 14, apartado B, fracciones I, II y III".', max_length=300)),
                ('plaza_empieza_con', models.CharField(blank=True, default='', help_text='Se asigna solo a las plazas que empiezan con este texto (palabras completas, sin importar acentos). Vacío: nunca se asigna solo, únicamente a mano.', max_length=150)),
                ('descripcion_contiene', models.CharField(blank=True, default='', help_text='Opcional: además, la descripción de la plaza debe contener este texto.', max_length=150)),
                ('activo', models.BooleanField(default=True, help_text='Inactivo: no se asigna ni se imprime.')),
                ('orden', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Fundamento por plaza',
                'verbose_name_plural': 'Fundamentos por plaza',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.AddField(
            model_name='empleado',
            name='fundamento_manual',
            field=models.ForeignKey(blank=True, help_text='Asignado a mano cuando la plaza no lo determina. Gana sobre el de la plaza. No lo toca la sincronización.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='empleados_asignados', to='empleados.fundamentoplaza'),
        ),
    ]
