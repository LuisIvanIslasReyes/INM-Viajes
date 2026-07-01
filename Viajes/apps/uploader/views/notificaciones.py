"""
Vistas relacionadas con el sistema de notificaciones
"""
from apps.cuentas.roles import flujo_principal_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import JsonResponse

from ..models import Notificacion


@flujo_principal_required
def notificaciones_list(request):
    """Vista para listar notificaciones del usuario"""
    filtro_tipo = request.GET.get('tipo', 'todas')

    # Capturar y eliminar notificaciones de carga exitosa para mostrarlas brevemente
    exitosas_qs = Notificacion.objects.filter(usuario=request.user, categoria='carga_exitosa')
    notificaciones_exitosas = list(exitosas_qs.order_by('-fecha_creacion'))
    exitosas_qs.delete()

    # Obtener notificaciones persistentes (excluye carga_exitosa ya eliminadas)
    notificaciones = Notificacion.objects.filter(usuario=request.user)

    # Filtrar por tipo
    if filtro_tipo == 'importante':
        notificaciones = notificaciones.filter(tipo='importante')
    elif filtro_tipo == 'no_importante':
        notificaciones = notificaciones.filter(tipo='no_importante')

    notificaciones = notificaciones.order_by('-fecha_creacion')

    # Paginar
    paginator = Paginator(notificaciones, 20)
    page = request.GET.get('page', 1)
    notificaciones_paginadas = paginator.get_page(page)

    # Contar no leídas (ya sin las exitosas eliminadas)
    total_no_leidas = Notificacion.objects.filter(usuario=request.user, leida=False).count()

    context = {
        'notificaciones': notificaciones_paginadas,
        'notificaciones_exitosas': notificaciones_exitosas,
        'filtro_tipo': filtro_tipo,
        'total_no_leidas': total_no_leidas,
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'uploader/notificaciones_list.html', context)


@flujo_principal_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marcar una notificación como leída"""
    if request.method == 'POST':
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
            notificacion.marcar_como_leida()
            
            # Devolver respuesta JSON con el nuevo contador
            total_no_leidas = Notificacion.objects.filter(usuario=request.user, leida=False).count()
            return JsonResponse({
                'success': True,
                'total_no_leidas': total_no_leidas
            })
        except Notificacion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notificación no encontrada'}, status=404)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)