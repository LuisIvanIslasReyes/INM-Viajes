from django.contrib import admin

from .models import (
    DatosOficina,
    Expediente,
    HojaMembretada,
    MotivoRechazo,
    OficioHistorial,
    OficioInstancia,
    PersonaExpediente,
    PlantillaOficio,
)


class SoloSuperUserMixin:
    """Catálogos que cambian lo que se imprime en todos los oficios: solo el SuperUser."""

    def has_add_permission(self, request, *args):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class SoloConsultaMixin:
    """Se trabaja en la pantalla de Oficios, no en el admin."""

    def has_add_permission(self, request, *args):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DatosOficina)
class DatosOficinaAdmin(SoloSuperUserMixin, admin.ModelAdmin):
    list_display = ('aeropuerto', 'entidad', 'terminal', 'ciudad', 'actualizado_en')

    def has_add_permission(self, request, *args):
        return request.user.is_superuser and not DatosOficina.objects.exists()

    def save_model(self, request, obj, form, change):
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(HojaMembretada)
class HojaMembretadaAdmin(SoloSuperUserMixin, admin.ModelAdmin):
    list_display = ('__str__', 'activo', 'subida_en')


@admin.register(MotivoRechazo)
class MotivoRechazoAdmin(SoloSuperUserMixin, admin.ModelAdmin):
    list_display = ('texto', 'orden', 'activo')
    list_editable = ('orden', 'activo')


@admin.register(PlantillaOficio)
class PlantillaOficioAdmin(SoloSuperUserMixin, admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'bloque_firmas', 'activo', 'modificado_en')
    readonly_fields = ('modificado_en', 'modificado_por')


class PersonaInline(admin.TabularInline):
    model = PersonaExpediente
    fields = ('nombre', 'nacionalidad', 'documento', 'idioma')
    readonly_fields = fields
    extra = 0
    can_delete = False


@admin.register(Expediente)
class ExpedienteAdmin(SoloConsultaMixin, admin.ModelAdmin):
    list_display = ('folio', 'fecha', 'resultado', 'firmante', 'creado_por')
    search_fields = ('folio', 'personas__nombre', 'personas__documento')
    inlines = [PersonaInline]


class HistorialInline(admin.TabularInline):
    model = OficioHistorial
    fields = ('fecha_hora', 'accion', 'usuario', 'detalle')
    readonly_fields = fields
    extra = 0
    can_delete = False


@admin.register(OficioInstancia)
class OficioInstanciaAdmin(SoloConsultaMixin, admin.ModelAdmin):
    list_display = ('__str__', 'estado', 'fecha_oficio', 'impreso_en', 'impreso_por')
    list_filter = ('estado', 'plantilla')
    search_fields = ('persona__nombre', 'persona__expediente__folio')
    inlines = [HistorialInline]
