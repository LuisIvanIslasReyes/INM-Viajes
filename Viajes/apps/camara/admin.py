from django.contrib import admin
from .models import FotoRechazo


@admin.register(FotoRechazo)
class FotoRechazoAdmin(admin.ModelAdmin):
    list_display = ['id', 'registro', 'nombre_archivo', 'usuario_captura', 'fecha_captura']
    list_filter = ['fecha_captura', 'usuario_captura']
    search_fields = ['registro__nombre_pasajero', 'registro__numero_documento', 'notas']
    readonly_fields = ['fecha_captura']
    
    def nombre_archivo(self, obj):
        return obj.nombre_archivo
    nombre_archivo.short_description = 'Archivo'