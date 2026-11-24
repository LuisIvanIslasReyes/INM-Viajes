"""
Sincroniza la réplica local de empleados con la Estancia.

Pensado para el Programador de tareas de Windows (ver `sincronizar_empleados.bat`
y `programar_sincronizacion_empleados.bat`):

    python manage.py sincronizar_empleados              # cada 15 min: incremental
    python manage.py sincronizar_empleados --completa   # de noche: catálogo entero

Sin `--completa` es incremental si la última sincronización exitosa dejó un punto
de partida; si no, hace una completa. Sale con código 1 si falla, para que la
tarea quede marcada con error en el historial.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.empleados.models import SincronizacionEmpleados
from apps.empleados.services import ErrorSincronizacion, sincronizar


class Command(BaseCommand):
    help = 'Descarga el catálogo de empleados de la Estancia y actualiza la réplica local.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--completa', action='store_true',
            help='Baja el catálogo entero y desactiva a quien ya no venga (no solo los cambios).',
        )

    def handle(self, *args, **options):
        try:
            r = sincronizar(origen=SincronizacionEmpleados.Origen.PROGRAMADA, completa=options['completa'])
        except ErrorSincronizacion as e:
            raise CommandError(f'Sincronización fallida: {e}') from e
        self.stdout.write(self.style.SUCCESS(
            f'OK · {r.get_modo_display().lower()} · recibidos {r.recibidos} · nuevos {r.creados} · '
            f'actualizados {r.actualizados} · desactivados {r.desactivados}'
        ))
