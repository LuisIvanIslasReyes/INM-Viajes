from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_list, name='admin_list'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('update/<int:registro_id>/', views.update_registro, name='update_registro'),
    path('batch/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
    path('batch/download/<int:batch_id>/', views.download_batch_file, name='download_batch_file'),
    path('create-user/', views.create_user, name='create_user'),
    path('batches/', views.batch_list, name='batch_list'),
    path('check-duplicates/', views.check_duplicates, name='check_duplicates'),
    path('date-range-report/', views.date_range_report, name='date_range_report'),
    
    # Casos Especiales
    path('casos-especiales/', views.casos_especiales_list, name='casos_especiales_list'),
    path('casos-especiales/aceptar/<int:caso_id>/', views.resolver_caso_aceptar, name='resolver_caso_aceptar'),
    path('casos-especiales/editar/<int:caso_id>/<int:registro_id>/', views.resolver_caso_editar, name='resolver_caso_editar'),
    path('casos-especiales/inadmitir/<int:caso_id>/<int:registro_id>/', views.resolver_caso_inadmitir, name='resolver_caso_inadmitir'),
    path('casos-especiales/eliminar/<int:caso_id>/<int:registro_id>/', views.resolver_caso_eliminar, name='resolver_caso_eliminar'),
]