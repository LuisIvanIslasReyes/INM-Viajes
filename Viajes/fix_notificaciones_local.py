"""
Script para quitar el prefijo /viajes/ de las notificaciones en desarrollo local
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Viajes.settings.local')
django.setup()

from uploader.models import Notificacion

# Quitar prefijo /viajes/ de las URLs
notificaciones = Notificacion.objects.filter(enlace__startswith='/viajes/')

print(f"Encontradas {notificaciones.count()} notificaciones con prefijo /viajes/")

for notif in notificaciones:
    old_enlace = notif.enlace
    notif.enlace = notif.enlace.replace('/viajes/', '/')
    notif.save()
    print(f"✓ Actualizado: {old_enlace} -> {notif.enlace}")

print(f"\n✅ {notificaciones.count()} notificaciones actualizadas correctamente")
