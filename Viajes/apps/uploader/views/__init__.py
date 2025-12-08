"""
Módulo de vistas para la aplicación uploader.
Organizado en submódulos por funcionalidad.
"""

from .upload import upload_excel, check_duplicates
from .registros import update_registro, admin_list, generar_pin
from .reportes import date_range_report, download_batch_file
from .notificaciones import notificaciones_list, marcar_notificacion_leida
from .casos_especiales import (
    casos_especiales_list,
    resolver_caso_aceptar,
    resolver_caso_editar,
    resolver_caso_inadmitir,
    resolver_caso_eliminar
)
from .admin import batch_list, delete_batch, create_user

__all__ = [
    # Upload
    'upload_excel',
    'check_duplicates',
    
    # Registros
    'update_registro',
    'admin_list',
    'generar_pin',
    
    # Reportes
    'date_range_report',
    'download_batch_file',
    
    # Notificaciones
    'notificaciones_list',
    'marcar_notificacion_leida',
    
    # Casos especiales
    'casos_especiales_list',
    'resolver_caso_aceptar',
    'resolver_caso_editar',
    'resolver_caso_inadmitir',
    'resolver_caso_eliminar',
    
    # Admin
    'batch_list',
    'delete_batch',
    'create_user',
]