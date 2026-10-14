from django.core.management.base import BaseCommand
from apps.uploader.models import Registro
from apps.uploader.utils.parsers import PAISES_ISO, obtener_nacionalidad


class Command(BaseCommand):
    help = 'Actualiza las nacionalidades de todos los registros existentes basándose en el código ISO'

    def handle(self, *args, **options):
        registros = Registro.objects.all()
        total = registros.count()
        actualizados = 0
        
        self.stdout.write(f'📊 Procesando {total} registros...\n')
        
        for i, registro in enumerate(registros, 1):
            # Sólo códigos conocidos: uno fuera del diccionario (p. ej. 'XX' de
            # captura manual) devolvería el código y pisaría el nombre actual.
            if registro.codigo_pais_emision and registro.codigo_pais_emision.strip().upper() in PAISES_ISO:
                nacionalidad_parseada = obtener_nacionalidad(registro.codigo_pais_emision)
                if nacionalidad_parseada != registro.pais_emision:
                    registro.pais_emision = nacionalidad_parseada
                    registro.save(update_fields=['pais_emision'])
                    actualizados += 1
            
            # Mostrar progreso cada 100 registros
            if i % 100 == 0:
                self.stdout.write(f'Procesados: {i}/{total}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n Proceso completado:')
        )
        self.stdout.write(f'   Total registros: {total}')
        self.stdout.write(f'   Actualizados: {actualizados}')
        self.stdout.write(f'   Sin cambios: {total - actualizados}')
