from django.contrib import admin

from .models import Pais, Redaccion


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('nombre', 'codigo')
    ordering = ('nombre',)


@admin.register(Redaccion)
class RedaccionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'resolucion', 'tema', 'pais', 'subido_por', 'fecha_creacion')
    list_filter = ('resolucion', 'pais')
    search_fields = ('titulo', 'tema')
    autocomplete_fields = ('pais',)
    readonly_fields = ('archivo_pdf', 'subido_por', 'fecha_creacion', 'fecha_modificacion')
    date_hierarchy = 'fecha_creacion'
