"""
Sincroniza la réplica local de empleados con la Estancia.

Pensado para correr desde el Programador de tareas de Windows cada 10-15 minutos
(ver `sincronizar_empleados.bat`). Sale con código 1 si falla, para que la tarea
quede marcada con error en el historial.

    python manage.py sincronizar_empleados
"""
from django.core.management.base import BaseCommand, CommandError

from apps.empleados.models import SincronizacionEmpleados
from apps.empleados.services import ErrorSincronizacion, sincronizar


class Command(BaseCommand):
    help = 'Descarga el catálogo de empleados de la Estancia y actualiza la réplica local.'

    def handle(self, *args, **options):
        try:
            r = sincronizar(origen=SincronizacionEmpleados.Origen.PROGRAMADA)
        except ErrorSincronizacion as e:
            raise CommandError(f'Sincronización fallida: {e}') from e
        self.stdout.write(self.style.SUCCESS(
            f'OK · recibidos {r.recibidos} · nuevos {r.creados} · '
            f'actualizados {r.actualizados} · desactivados {r.desactivados}'
        ))
