from django.urls import path

from . import views

app_name = 'empleados'

urlpatterns = [
    path('', views.listado, name='listado'),
    path('buscar/', views.buscar, name='buscar'),
    path('sincronizar/', views.sincronizar_ahora, name='sincronizar'),
    path('<int:pk>/firmante/', views.alternar_firmante, name='alternar_firmante'),
    path('<int:pk>/fundamento/', views.asignar_fundamento, name='asignar_fundamento'),
]
