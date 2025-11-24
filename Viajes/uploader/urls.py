from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_excel, name='upload_excel'),
    path('admin-list/', views.admin_list, name='admin_list'),
    path('update/<int:registro_id>/', views.update_registro, name='update_registro'),
    path('create-user/', views.create_user, name='create_user'),
]
