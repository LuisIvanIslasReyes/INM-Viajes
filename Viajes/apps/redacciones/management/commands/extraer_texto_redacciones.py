"""
Backfill del buscador: extrae el texto de los documentos ya subidos.

Al desplegar la funcionalidad de búsqueda por contenido, los documentos
existentes no tienen `texto_contenido`. Correr una vez:

    python manage.py extraer_texto_redacciones

Con --forzar reprocesa también los que ya tienen texto (p.ej. tras mejorar
la extracción).
"""
from django.core.management.base import BaseCommand

from apps.redacciones.models import Redaccion
from apps.redacciones.utils.extraccion import actualizar_texto


class Command(BaseCommand):
    help = 'Extrae y guarda el texto de los documentos para el buscador de palabras.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar', action='store_true',
            help='Reprocesa también los documentos que ya tienen texto extraído.',
        )

    def handle(self, *args, **options):
        qs = Redaccion.objects.all()
        if not options['forzar']:
            qs = qs.filter(texto_contenido='')

        total = con_texto = 0
        for redaccion in qs.iterator():
            total += 1
            if actualizar_texto(redaccion):
                con_texto += 1
                self.stdout.write(f'  ✔ {redaccion.titulo}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  – {redaccion.titulo} (sin texto: PDF escaneado o sin vista previa)'
                ))
        self.stdout.write(self.style.SUCCESS(
            f'{con_texto}/{total} documento(s) con texto extraído.'
        ))
