from django.urls import path

from . import views

app_name = 'redacciones'

urlpatterns = [
    path('', views.biblioteca, name='biblioteca'),
    path('subir/', views.subir, name='subir'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar, name='eliminar'),
    path('<int:pk>/preview/', views.preview, name='preview'),
    path('<int:pk>/descargar/', views.descargar, name='descargar'),
]
