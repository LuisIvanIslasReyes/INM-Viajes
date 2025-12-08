"""
Script para actualizar los enlaces de notificaciones
Cambia /casos-especiales/ por /casos_especiales/
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Viajes.settings.production')
django.setup()

from uploader.models import Notificacion

# Actualizar enlaces con guion a guion bajo Y agregar prefijo /viajes/
notificaciones = Notificacion.objects.filter(enlace__icontains='/casos-especiales/')

print(f"Encontradas {notificaciones.count()} notificaciones con enlaces antiguos")

for notif in notificaciones:
    old_enlace = notif.enlace
    # Cambiar /casos-especiales/ por /viajes/casos_especiales/
    notif.enlace = notif.enlace.replace('/casos-especiales/', '/viajes/casos_especiales/')
    notif.save()
    print(f"✓ Actualizado: {old_enlace} -> {notif.enlace}")

print(f"\n✅ {notificaciones.count()} notificaciones actualizadas correctamente")
