"""Siembra el catálogo Pais desde context/paises.json (reutiliza la fuente de
verdad ya existente en el proyecto).

Idempotente: usa get_or_create por código ISO.
"""
import json

from django.conf import settings
from django.db import migrations


def sembrar_paises(apps, schema_editor):
    Pais = apps.get_model('redacciones', 'Pais')
    ruta = settings.BASE_DIR.parent / 'context' / 'paises.json'
    with open(ruta, encoding='utf-8') as fh:
        data = json.load(fh)
    for p in data:
        codigo = (p.get('codigo') or '').strip()
        nombre = (p.get('nombre') or '').strip()
        if codigo and nombre:
            Pais.objects.get_or_create(codigo=codigo, defaults={'nombre': nombre})


def borrar_paises(apps, schema_editor):
    Pais = apps.get_model('redacciones', 'Pais')
    Pais.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('redacciones', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sembrar_paises, borrar_paises),
    ]
