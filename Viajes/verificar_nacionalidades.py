"""
Script para verificar el parseo de nacionalidades
"""
import os
import sys

# Obtener el directorio actual del script y agregarlo al path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configurar Django - usa la variable de entorno si existe, si no usa el default
# En producción puedes exportar: export DJANGO_SETTINGS_MODULE=Viajes.settings_production
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Viajes.settings')

import django
django.setup()

from uploader.models import Registro
from django.db.models import Count

# Ver todas las nacionalidades únicas
print("=" * 70)
print("NACIONALIDADES EN LA BASE DE DATOS")
print("=" * 70)

nacionalidades = Registro.objects.values('codigo_pais_emision', 'pais_emision').annotate(
    total=Count('id')
).order_by('-total')

for n in nacionalidades:
    codigo = n['codigo_pais_emision'] or 'N/A'
    pais = n['pais_emision'] or 'N/A'
    total = n['total']
    print(f"{codigo:5} -> {pais:30} ({total:3} registros)")

print("\n" + "=" * 70)
print(f"Total de nacionalidades diferentes: {nacionalidades.count()}")
print("=" * 70)
