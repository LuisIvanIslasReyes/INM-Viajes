"""
Sistema de roles del proyecto.

Roles:
- SuperUser  -> user.is_superuser = True (acceso total).
- Aeropuerto -> grupo 'Aeropuerto' (flujo principal + módulos Directorio/Redacciones).
- General    -> grupo 'General' (solo módulos Directorio y Redacciones; Redacciones en
                modo consulta).

Se implementa con grupos nativos de Django. Estas utilidades centralizan la lógica
para que las vistas y plantillas no consulten los grupos directamente.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

GRUPO_AEROPUERTO = 'Aeropuerto'
GRUPO_GENERAL = 'General'


def es_aeropuerto(user):
    return user.is_authenticated and user.groups.filter(name=GRUPO_AEROPUERTO).exists()


def es_general(user):
    return user.is_authenticated and user.groups.filter(name=GRUPO_GENERAL).exists()


def puede_flujo_principal(user):
    """SuperUser y Usuario Aeropuerto pueden acceder al flujo principal."""
    return user.is_authenticated and (user.is_superuser or es_aeropuerto(user))


def puede_subir_redacciones(user):
    """Solo SuperUser y Aeropuerto pueden subir documentos a Redacciones."""
    return user.is_authenticated and (user.is_superuser or es_aeropuerto(user))


def rol_nombre(user):
    """Etiqueta legible del rol, para mostrar en la interfaz."""
    if not user.is_authenticated:
        return ''
    if user.is_superuser:
        return 'Administrador'
    if es_aeropuerto(user):
        return 'Usuario Aeropuerto'
    if es_general(user):
        return 'Usuario General'
    return 'Usuario'


def flujo_principal_required(view_func):
    """
    Exige autenticación y permiso de flujo principal.
    Un Usuario General (sin permiso) es redirigido al módulo Directorio.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not puede_flujo_principal(request.user):
            return redirect('directorio:listado')
        return view_func(request, *args, **kwargs)
    return _wrapped


def puede_subir_required(view_func):
    """Exige autenticación y permiso para subir documentos (Redacciones)."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not puede_subir_redacciones(request.user):
            messages.error(request, 'No tienes permiso para subir documentos.')
            return redirect('redacciones:biblioteca')
        return view_func(request, *args, **kwargs)
    return _wrapped


def roles_context(request):
    """Context processor: expone banderas de rol a todas las plantillas."""
    user = request.user
    return {
        'puede_flujo_principal': puede_flujo_principal(user),
        'es_general': es_general(user),
        'puede_subir_redacciones': puede_subir_redacciones(user),
        'rol_nombre': rol_nombre(user),
    }
