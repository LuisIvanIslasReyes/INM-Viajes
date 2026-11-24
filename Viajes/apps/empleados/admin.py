from django.contrib import admin

from .models import Empleado, SincronizacionEmpleados


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    """Solo consulta: los datos vienen de la Estancia y se sobrescriben al sincronizar."""

    list_display = ('numero_empleado', 'apellidos', 'nombres', 'cargo', 'municipio',
                    'activo', 'firmante_habitual', 'sincronizado_en')
    list_filter = ('activo', 'firmante_habitual', 'municipio')
    search_fields = ('nombres', 'apellidos', 'numero_empleado')
    readonly_fields = [f.name for f in Empleado._meta.fields if f.name != 'firmante_habitual']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SincronizacionEmpleados)
class SincronizacionEmpleadosAdmin(admin.ModelAdmin):
    list_display = ('iniciada_en', 'origen', 'modo', 'exitosa', 'recibidos', 'creados',
                    'actualizados', 'desactivados', 'usuario')
    list_filter = ('exitosa', 'origen', 'modo')
    readonly_fields = [f.name for f in SincronizacionEmpleados._meta.fields]

    def has_add_permission(self, request):
        return False
