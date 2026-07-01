"""
Crea los grupos de rol ('Aeropuerto' y 'General') y agrega a todos los usuarios
no-superuser existentes al grupo 'Aeropuerto', para no romper su acceso actual al
flujo principal.

Idempotente: usa get_or_create, se puede re-ejecutar sin efectos secundarios.
"""
from django.db import migrations

GRUPO_AEROPUERTO = 'Aeropuerto'
GRUPO_GENERAL = 'General'


def crear_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    grupo_aeropuerto, _ = Group.objects.get_or_create(name=GRUPO_AEROPUERTO)
    Group.objects.get_or_create(name=GRUPO_GENERAL)

    # Backfill: usuarios existentes (no superuser) se consideran Aeropuerto.
    for user in User.objects.filter(is_superuser=False):
        user.groups.add(grupo_aeropuerto)


def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=[GRUPO_AEROPUERTO, GRUPO_GENERAL]).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
