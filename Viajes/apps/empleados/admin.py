from django.contrib import admin

from .models import Empleado, FundamentoPlaza, SincronizacionEmpleados, precargar_fundamentos

# Lo único que se edita del empleado en Viajes; lo demás viene de la Estancia.
CAMPOS_PROPIOS_DE_VIAJES = {'firmante_habitual', 'fundamento_manual'}


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    """Solo consulta: los datos vienen de la Estancia y se sobrescriben al sincronizar."""

    list_display = ('numero_empleado', 'apellidos', 'nombres', 'cargo', 'fundamento_impreso',
                    'municipio', 'activo', 'firmante_habitual', 'sincronizado_en')
    list_filter = ('activo', 'firmante_habitual', 'municipio')
    search_fields = ('nombres', 'apellidos', 'numero_empleado')
    readonly_fields = [f.name for f in Empleado._meta.fields if f.name not in CAMPOS_PROPIOS_DE_VIAJES]

    def get_changelist_instance(self, request):
        # Una sola consulta al catálogo de fundamentos para toda la página.
        changelist = super().get_changelist_instance(request)
        precargar_fundamentos(changelist.result_list)
        return changelist

    @admin.display(description='Fundamento')
    def fundamento_impreso(self, obj):
        aplicable = obj.fundamento_aplicable
        if not aplicable:
            return '— sin fundamento —'
        return f'{aplicable.nombre} (a mano)' if obj.fundamento_origen == 'manual' else aplicable.nombre

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FundamentoPlaza)
class FundamentoPlazaAdmin(admin.ModelAdmin):
    """Catálogo de fundamentos por plaza. Solo el SuperUser lo cambia: afecta a todos los oficios futuros."""

    list_display = ('nombre', 'texto', 'plaza_empieza_con', 'descripcion_contiene', 'activo', 'orden')
    list_filter = ('activo',)
    search_fields = ('nombre', 'texto', 'clave')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SincronizacionEmpleados)
class SincronizacionEmpleadosAdmin(admin.ModelAdmin):
    list_display = ('iniciada_en', 'origen', 'modo', 'exitosa', 'recibidos', 'creados',
                    'actualizados', 'desactivados', 'usuario')
    list_filter = ('exitosa', 'origen', 'modo')
    readonly_fields = [f.name for f in SincronizacionEmpleados._meta.fields]

    def has_add_permission(self, request):
        return False
