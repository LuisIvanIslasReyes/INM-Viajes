from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_excel, name='upload_excel'),
    path('update/<int:registro_id>/', views.update_registro, name='update_registro'),
    path('batch/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'), 
    path('create-user/', views.create_user, name='create_user'),
    path('admin-list/', views.admin_list, name='admin_list'),
    path('batches/', views.batch_list, name='batch_list'), 
]