"""
Vistas administrativas (solo para superusuarios)
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models

from ..forms import CreateUserForm
from ..models import UploadBatch


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='admin_list')
def batch_list(request):
    """Vista para listar todas las cargas de archivos (SOLO ADMIN)"""
    batches = UploadBatch.objects.select_related('usuario').annotate(
        total_registros=models.Count('registros')
    ).order_by('-fecha_carga')

    paginator = Paginator(batches, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'uploader/batch_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='admin_list')
def delete_batch(request, batch_id):
    """Vista para que el administrador elimine una carga de archivo (SOLO ADMIN)"""
    if request.method == 'POST':
        try:
            batch = UploadBatch.objects.get(id=batch_id)
            archivo_nombre = batch.archivo.name

            registros_count = batch.registros.count()
            batch.registros.all().delete()

            if batch.archivo:
                batch.archivo.delete()
            
            batch.delete()

            messages.success(
                request,
                f'✅ Carga "{archivo_nombre}" eliminada correctamente. '
                f'Se eliminaron {registros_count} registro(s).'
            )
        except UploadBatch.DoesNotExist:
            messages.error(request, '❌ La carga no existe.')
        except Exception as e:
            messages.error(request, f'❌ Error al eliminar la carga: {str(e)}')
    
    return redirect('batch_list')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='admin_list')
def create_user(request):
    """Vista para que Administrador cree usuarios (SOLO ADMIN)"""
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = False
            user.is_staff = False
            user.save()
            messages.success(request, f'✅ Usuario {user.username} creado exitosamente.')
            return redirect('create_user')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {error}')
    else:
        form = CreateUserForm()

    usuarios = User.objects.filter(is_superuser=False).order_by('-date_joined')

    context = {
        'form': form,
        'usuarios': usuarios,
    }
    return render(request, 'uploader/create_user.html', context)