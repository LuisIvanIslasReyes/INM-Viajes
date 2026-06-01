"""
Vistas administrativas (solo para superusuarios)
NO CONFUNDIR CON DJANGO-ADMIN
Estas vistas permiten al superusuario:
- Listar y eliminar cargas de archivos
- Crear usuarios estándar
"""
from datetime import datetime, date, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone

from ..forms import CreateUserForm
from ..models import UploadBatch


def _parse_date(value):
    """Convierte 'YYYY-MM-DD' a date, o None si es inválido/vacío."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@login_required
def batch_list(request):
    """Vista para listar todas las cargas de archivos (TODOS los usuarios)"""
    fecha_exacta = _parse_date(request.GET.get('fecha'))
    fecha_inicio = _parse_date(request.GET.get('fecha_inicio'))
    fecha_fin = _parse_date(request.GET.get('fecha_fin'))
    busqueda = (request.GET.get('q') or '').strip()
    usuario_id = (request.GET.get('usuario') or '').strip()

    # Queryset base con los filtros aplicados (sin annotate, para stats limpios)
    base = UploadBatch.objects.select_related('usuario')

    if fecha_exacta:
        base = base.filter(fecha_carga__date=fecha_exacta)
    else:
        if fecha_inicio:
            base = base.filter(fecha_carga__date__gte=fecha_inicio)
        if fecha_fin:
            base = base.filter(fecha_carga__date__lte=fecha_fin)

    if busqueda:
        base = base.filter(archivo__icontains=busqueda)

    if usuario_id.isdigit():
        base = base.filter(usuario_id=int(usuario_id))

    # Stats (consultas separadas para evitar conflictos con annotate)
    total_cargas = base.count()
    total_registros = base.aggregate(total=models.Count('registros'))['total'] or 0
    stats = {
        'total_cargas': total_cargas,
        'total_registros': total_registros,
    }
    hoy = timezone.localdate()
    stats_hoy = UploadBatch.objects.filter(fecha_carga__date=hoy).count()

    # Queryset paginado con el conteo por fila
    batches = base.annotate(
        total_registros=models.Count('registros')
    ).order_by('-fecha_carga')

    paginator = Paginator(batches, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Querystring para preservar filtros en la paginación
    params = request.GET.copy()
    params.pop('page', None)
    querystring = params.urlencode()

    usuarios = User.objects.filter(uploadbatch__isnull=False).distinct().order_by('username')

    context = {
        'page_obj': page_obj,
        'fecha_exacta': fecha_exacta.isoformat() if fecha_exacta else '',
        'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else '',
        'fecha_fin': fecha_fin.isoformat() if fecha_fin else '',
        'busqueda': busqueda,
        'usuario_id': usuario_id,
        'usuarios': usuarios,
        'stats': stats,
        'stats_hoy': stats_hoy,
        'hoy': hoy.isoformat(),
        'querystring': querystring,
        'filtros_activos': bool(fecha_exacta or fecha_inicio or fecha_fin or busqueda or usuario_id),
    }

    return render(request, 'uploader/batch_list.html', context)


@login_required
def delete_batch(request, batch_id):
    """Vista para eliminar una carga de archivo (TODOS los usuarios)"""
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
                f' Carga "{archivo_nombre}" eliminada correctamente. '
                f'Se eliminaron {registros_count} registro(s).'
            )
        except UploadBatch.DoesNotExist:
            messages.error(request, 'La carga no existe.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la carga: {str(e)}')
    
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
            messages.success(request, f' Usuario {user.username} creado exitosamente.')
            return redirect('create_user')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f' {error}')
    else:
        form = CreateUserForm()

    usuarios = User.objects.filter(is_superuser=False).order_by('-date_joined')

    context = {
        'form': form,
        'usuarios': usuarios,
    }
    return render(request, 'uploader/create_user.html', context)