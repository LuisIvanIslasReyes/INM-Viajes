from django.urls import path

from . import views

app_name = 'oficios'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.nuevo, name='nuevo'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/firmas/', views.guardar_firmas, name='guardar_firmas'),
    path('<int:pk>/personas/agregar/', views.agregar_persona, name='agregar_persona'),
    path('<int:pk>/borradores/', views.crear_borradores_familia, name='crear_borradores_familia'),
    path('<int:pk>/paquete/', views.paquete, name='paquete'),
    path('persona/<int:pk>/editar/', views.editar_persona, name='editar_persona'),
    path('persona/<int:pk>/quitar/', views.quitar_persona, name='quitar_persona'),
    path('persona/<int:pk>/borradores/', views.crear_borradores, name='crear_borradores'),
    path('persona/<int:persona_pk>/evidencias/<int:plantilla_pk>/agregar/', views.evidencia_agregar,
         name='evidencia_agregar'),
    path('persona/<int:persona_pk>/evidencias/<int:plantilla_pk>/camara/', views.evidencia_camara,
         name='evidencia_camara'),
    path('evidencia/<int:pk>/', views.evidencia_editar, name='evidencia_editar'),
    path('evidencia/<int:pk>/quitar/', views.evidencia_quitar, name='evidencia_quitar'),
    path('oficio/<int:pk>/', views.oficio, name='oficio'),
    path('oficio/<int:pk>/word/', views.oficio_docx, name='oficio_docx'),
    path('oficio/<int:pk>/pdf/', views.oficio_pdf, name='oficio_pdf'),
    path('oficio/<int:pk>/recargar/', views.oficio_recargar, name='oficio_recargar'),
    path('oficio/<int:pk>/imprimir/', views.oficio_imprimir, name='oficio_imprimir'),
    path('oficio/<int:pk>/reabrir/', views.oficio_reabrir, name='oficio_reabrir'),
    path('oficio/<int:pk>/eliminar/', views.oficio_eliminar, name='oficio_eliminar'),
    path('plantillas/', views.plantillas, name='plantillas'),
    path('plantillas/<int:pk>/', views.plantilla_editar, name='plantilla_editar'),
    path('plantillas/<int:pk>/idioma/<str:idioma>/', views.plantilla_idioma, name='plantilla_idioma'),
]
