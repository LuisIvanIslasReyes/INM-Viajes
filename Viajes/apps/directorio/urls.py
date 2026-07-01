from django.urls import path

from . import views

app_name = 'directorio'

urlpatterns = [
    path('', views.listado, name='listado'),
    path('nueva/', views.crear, name='crear'),
    path('coincidencias/', views.buscar_coincidencias, name='buscar_coincidencias'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/editar/', views.editar, name='editar'),
]
