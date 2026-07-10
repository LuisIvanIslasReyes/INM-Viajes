from django.urls import path
from apps.uploader import views

urlpatterns = [
    path('', views.admin_list, name='admin_list'),
    path('home-admin/', views.home_admin, name='home_admin'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('update/<int:registro_id>/', views.update_registro, name='update_registro'),
    path('batch/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
    path('batch/download/<int:batch_id>/', views.download_batch_file, name='download_batch_file'),
    path('create-user/', views.create_user, name='create_user'),
    path('batches/', views.batch_list, name='batch_list'),
    path('check-duplicates/', views.check_duplicates, name='check_duplicates'),
    path('date-range-report/', views.date_range_report, name='date_range_report'),
    
    # Notificaciones
    path('notificaciones/', views.notificaciones_list, name='notificaciones_list'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    
    # PIN Oficial
    path('pin/<str:fecha>/', views.generar_pin, name='generar_pin'),

    # Reporte Inadmitidos
    path('inadmitidos/', views.inadmitidos_page, name='inadmitidos_page'),
    path('inadmitidos-data/', views.inadmitidos_data, name='inadmitidos_data'),
    path('inadmitidos-pdf/', views.generar_inadmitidos_pdf, name='generar_inadmitidos_pdf'),
    path('inadmitidos-excel/', views.generar_inadmitidos_excel, name='generar_inadmitidos_excel'),
    
    # Menores (captura manual)
    path('menores/crear/', views.crear_menor, name='crear_menor'),

    # Tiempos de atención (captura manual)
    path('tiempos-atencion/capturar/', views.capturar_tiempos_atencion, name='capturar_tiempos_atencion'),
    path('tiempos-atencion/obtener/<str:fecha>/', views.obtener_tiempos_atencion, name='obtener_tiempos_atencion'),

    # Casos Especiales
    path('casos_especiales/', views.casos_especiales_list, name='casos_especiales_list'),
    path('casos_especiales/aceptar/<int:caso_id>/', views.resolver_caso_aceptar, name='resolver_caso_aceptar'),
    path('casos_especiales/editar/<int:caso_id>/<int:registro_id>/', views.resolver_caso_editar, name='resolver_caso_editar'),
    path('casos_especiales/inadmitir/<int:caso_id>/<int:registro_id>/', views.resolver_caso_inadmitir, name='resolver_caso_inadmitir'),
    path('casos_especiales/eliminar/<int:caso_id>/<int:registro_id>/', views.resolver_caso_eliminar, name='resolver_caso_eliminar'),
]