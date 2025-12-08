from django.urls import path
from . import views

app_name = 'camara'

urlpatterns = [
    path('subir/<int:registro_id>/', views.subir_foto_rechazo, name='subir_foto_rechazo'),
    path('ver/<int:registro_id>/', views.ver_fotos_rechazo, name='ver_fotos_rechazo'),
]