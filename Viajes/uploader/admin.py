from django.contrib import admin
from .models import UploadBatch, Registro


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_carga', 'archivo', 'count_registros')
    list_filter = ('fecha_carga', 'usuario')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha_carga',)
    
    def count_registros(self, obj):
        return obj.registros.count()
    count_registros.short_description = 'Total Registros'


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nombre_pasajero', 'vuelo_numero', 'numero_documento', 
        'confirmado', 'inadmitido', 'batch'
    )
    list_filter = (
        'confirmado', 'inadmitido', 'vuelo_numero', 
        'aeropuerto_salida', 'aeropuerto_llegada', 'genero'
    )
    search_fields = (
        'nombre_pasajero', 'numero_documento', 'vuelo_numero', 
        'numero_ticket', 'numero_asiento'
    )
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'batch')
    
    fieldsets = (
        ('Información de Vuelo', {
            'fields': (
                'batch', 'vuelo_numero', 'vuelo_fecha', 
                'aeropuerto_salida', 'aeropuerto_llegada', 'salida_planificada'
            )
        }),
        ('Información del Pasajero', {
            'fields': (
                'nombre_pasajero', 'numero_documento', 'fecha_nacimiento', 
                'genero', 'codigo_pais_emision', 'pais_emision'
            )
        }),
        ('Detalles del Viaje', {
            'fields': (
                'numero_asiento', 'numero_ticket', 'estado_checkin',
                'numero_equipaje', 'piezas', 'peso'
            )
        }),
        ('Información de Contacto', {
            'fields': (
                'informacion_contacto', 'contacto_reserva', 'contacto_pasajero'
            )
        }),
        ('Campos Administrativos', {
            'fields': ('confirmado', 'inadmitido', 'comentario'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('batch', 'batch__usuario')
