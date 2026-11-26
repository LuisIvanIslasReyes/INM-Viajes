"""
Siembra los 6 fundamentos por plaza (24/11/2026).

Copia congelada: si después cambian los textos o las reglas, se corrigen en el
admin o en otra migración, NO aquí. Es idempotente (`update_or_create` por clave).

Reglas de asignación automática (ver `apps/empleados/fundamentos.py`):
  - Sub Representante Federal: sin regla; hoy no existe esa plaza en la Estancia,
    así que solo se asigna a mano.
  - Subdirector de Control y Verificación: D-144 deja todas las subdirecciones como
    "SUBDIRECTOR DE ÁREA"; lo distingue la descripción. Las de Regulación y Atención
    al Migrante quedan sin fundamento (decisión del usuario).
"""
from django.db import migrations

# (clave, nombre, texto, plaza_empieza_con, descripcion_contiene, orden)
FUNDAMENTOS = [
    ('TITULAR', 'Titular',
     'Artículo 12, apartado B, fracciones I, II y III', 'TITULAR', '', 10),
    ('SUB_REP_FEDERAL', 'Sub Representante Federal',
     'Artículo 13, apartado B, fracciones I, II y III', '', '', 20),
    ('REP_LOCAL', 'Representante Local',
     'Artículo 14, apartado B, fracciones I, II y III', 'REPRESENTANTE LOCAL', '', 30),
    ('SUB_REP_LOCAL', 'Sub Representante Local',
     'Artículo 15, apartado B, fracciones I, II y III', 'SUB REPRESENTANTE LOCAL', '', 40),
    ('SUBDIR_CYV', 'Subdirector de Control y Verificación Migratoria',
     'Artículo 19, fracciones I, II, IV, V y IX', 'SUBDIRECTOR', 'CONTROL Y VERIFICACION', 50),
    ('JEFE_DEPTO', 'Jefe de Departamento',
     'Artículo 23, fracciones I, II, III y IV', 'JEFE DE DEPARTAMENTO', '', 60),
]


def sembrar(apps, schema_editor):
    FundamentoPlaza = apps.get_model('empleados', 'FundamentoPlaza')
    for clave, nombre, texto, plaza, descripcion, orden in FUNDAMENTOS:
        FundamentoPlaza.objects.update_or_create(
            clave=clave,
            defaults={
                'nombre': nombre,
                'texto': texto,
                'plaza_empieza_con': plaza,
                'descripcion_contiene': descripcion,
                'orden': orden,
                'activo': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0003_fundamento_plaza'),
    ]

    # Al revertir no se borra nada aquí: la 0003 elimina la tabla completa.
    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
