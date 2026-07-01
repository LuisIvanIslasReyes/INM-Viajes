from django.contrib import admin

from .models import EmpresaDirectorio, EstadoMexico


@admin.register(EstadoMexico)
class EstadoMexicoAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre')
    search_fields = ('nombre', 'clave')
    ordering = ('nombre',)


@admin.register(EmpresaDirectorio)
class EmpresaDirectorioAdmin(admin.ModelAdmin):
    list_display = (
        'empresa', 'firma_encargado', 'telefono', 'ciudad', 'estado',
        'tentativa_resolucion', 'fecha_creacion',
    )
    list_filter = ('tentativa_resolucion', 'estado')
    search_fields = ('empresa', 'firma_encargado', 'telefono')
    autocomplete_fields = ('estado',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'creado_por')
    date_hierarchy = 'fecha_creacion'
