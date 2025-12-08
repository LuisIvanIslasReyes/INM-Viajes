"""
Vistas relacionadas con la gestión de registros de pasajeros
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.urls import reverse
from datetime import datetime, timedelta
import logging

from ..models import Registro, UploadBatch, Notificacion


@login_required
def update_registro(request, registro_id):
    """Vista para actualizar campos (TODOS pueden editar TODO)"""
    from urllib.parse import urlencode
    from django.urls import reverse
    
    if request.method == 'POST':
        try:
            registro = Registro.objects.get(id=registro_id)
            
            # ✅ SIN VALIDACIÓN DE PERMISOS - Todos pueden editar todo
            
            # Actualizar campos según la nueva lógica:
            # SR (Segunda Revisión) = segunda_revision
            # R (Rechazo) = rechazado
            # I (Internación) = internacion
            
            if 'segunda_revision' in request.POST:
                # Toggle Segunda Revisión
                registro.segunda_revision = request.POST.get('segunda_revision') == 'true'
                
                if not registro.segunda_revision:
                    # Si se desactiva SR, también desactivar R e I
                    registro.internacion = False
                    registro.rechazado = False
                    
            # R solo se puede activar si SR está activo
            elif 'rechazado' in request.POST:
                nuevo_valor = request.POST.get('rechazado') == 'true'
                
                # Si está intentando ACTIVAR R, validar que SR esté activo
                if nuevo_valor and not registro.segunda_revision:
                    messages.warning(request, '⚠️ Debes marcar "Segunda Revisión (SR)" antes de poder rechazar.')
                    # Redirigir sin guardar
                    params = request.GET.copy()
                    params['highlight'] = str(registro_id)
                    redirect_url = reverse('admin_list') + '?' + urlencode(params)
                    return redirect(redirect_url)
                
                # Si la validación pasa (o está desactivando), actualizar
                registro.rechazado = nuevo_valor
                # Si se marca como Rechazo, desmarcar Internación
                if registro.rechazado:
                    registro.internacion = False
                
        
            # I solo se puede activar si SR está activo
            elif 'internacion' in request.POST:
                nuevo_valor = request.POST.get('internacion') == 'true'
                
                # Si está intentando ACTIVAR I, validar que SR esté activo
                if nuevo_valor and not registro.segunda_revision:
                    messages.warning(request, '⚠️ Debes marcar "Segunda Revisión (SR)" antes de marcar Internación (I).')
                    # Redirigir sin guardar
                    params = request.GET.copy()
                    params['highlight'] = str(registro_id)
                    redirect_url = reverse('admin_list') + '?' + urlencode(params)
                    return redirect(redirect_url)
                
                # Si la validación pasa (o está desactivando), actualizar
                registro.internacion = nuevo_valor
                # Si se marca I, desmarcar Rechazo
                if registro.internacion:
                    registro.rechazado = False
            
            elif 'comentario' in request.POST:
                registro.comentario = request.POST.get('comentario')
            
            registro.save()
            messages.success(request, '✅ Registro actualizado exitosamente.')
            
            # Mantener TODOS los parámetros GET que venían en la URL
            params = request.GET.copy()
            
            # Agregar el parámetro highlight
            params['highlight'] = str(registro_id)
            
            # Construir la URL completa manteniendo búsqueda, filtros, paginación, etc.
            redirect_url = reverse('admin_list') + '?' + urlencode(params)
            return redirect(redirect_url)
            
        except Registro.DoesNotExist:
            messages.error(request, '❌ Registro no encontrado.')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {str(e)}')
    
    return redirect('admin_list')


@login_required
def admin_list(request):
    """Vista para ver y modificar registros (TODOS VEN TODO)"""
    # TODOS ven TODOS los registros
    registros = Registro.objects.select_related('batch', 'batch__usuario').all()
    batches = UploadBatch.objects.all().order_by('-fecha_carga')
    
    # Filtro de búsqueda por documento o pasajero
    search = request.GET.get('search')
    if search:
        registros = registros.filter(
            models.Q(numero_documento__icontains=search) |
            models.Q(nombre_pasajero__icontains=search)
        )
    
    # Filtro por batch
    batch_id = request.GET.get('batch')
    if batch_id:
        registros = registros.filter(batch_id=batch_id)
    
    # Filtro por Segunda Revisión (SR)
    segunda_revision = request.GET.get('segunda_revision')
    if segunda_revision == 'true':
        registros = registros.filter(segunda_revision=True)
    
    # Filtro por Rechazo (R)
    rechazado = request.GET.get('rechazado')
    if rechazado == 'true':
        registros = registros.filter(rechazado=True)
    
    # Filtro por Punto de Internación (PI)
    internacion = request.GET.get('internacion')
    if internacion == 'true':
        registros = registros.filter(internacion=True)
    
    # Paginación
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contar notificaciones no leídas para el usuario actual
    notificaciones_no_leidas = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).count()
    
    context = {
        'page_obj': page_obj,
        'batches': batches,
        'is_superuser': request.user.is_superuser,
        'notificaciones_no_leidas': notificaciones_no_leidas,
    }
    
    return render(request, 'uploader/admin_list.html', context)


@login_required
def generar_pin(request, fecha):
    """Vista para generar el PIN oficial del INM por fecha"""
    logger = logging.getLogger(__name__)
    
    # Convertir string de fecha a objeto date
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f'Fecha inválida recibida: {fecha} - Error: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Fecha inválida'}, status=400)
        messages.error(request, '❌ Fecha inválida.')
        return redirect('date_range_report')
    
    # Obtener todos los registros de ese día (buscar por rango de fecha completo)
    fecha_inicio = datetime.combine(fecha_obj, datetime.min.time())
    fecha_fin = datetime.combine(fecha_obj, datetime.max.time())
    
    registros_del_dia = Registro.objects.filter(
        vuelo_fecha__gte=fecha_inicio,
        vuelo_fecha__lte=fecha_fin
    )
    
    if not registros_del_dia.exists():
        logger.warning(f'No se encontraron registros para la fecha: {fecha_obj}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': f'No se encontraron registros para la fecha {fecha_obj.strftime("%d/%m/%Y")}'}, status=404)
        messages.error(request, f'❌ No se encontraron registros para la fecha {fecha_obj.strftime("%d/%m/%Y")}')
        return redirect('date_range_report')
    
    # Calcular estadísticas
    total_pasajeros = registros_del_dia.count()
    
    # Registros con Segunda Revisión
    registros_sr = registros_del_dia.filter(segunda_revision=True)
    total_sr = registros_sr.count()
    
    # De los SR, cuántos fueron Internación
    registros_internacion = registros_sr.filter(internacion=True)
    total_internaciones = registros_internacion.count()
    
    # De los SR, cuántos fueron Rechazo
    registros_rechazo = registros_sr.filter(rechazado=True)
    total_rechazos = registros_rechazo.count()
    
    # Calcular conexiones (pasajeros que van a MEX y NO fueron rechazados)
    # Detectar MEX por aeropuerto_llegada
    registros_mex = registros_del_dia.filter(
        models.Q(aeropuerto_llegada__icontains='MEX') | 
        models.Q(aeropuerto_llegada__icontains='MEXICO') |
        models.Q(aeropuerto_llegada__icontains='MÉXICO')
    )
    # Conexiones = Total PEK-MEX - Rechazados PEK-MEX
    rechazados_mex = registros_mex.filter(rechazado=True).count()
    total_conexiones = registros_mex.count() - rechazados_mex
    
    # Obtener número de vuelo del primer registro
    primer_registro = registros_del_dia.first()
    vuelo_numero = primer_registro.vuelo_numero if primer_registro else 'HU7925'
    
    # Datos completos de personas rechazadas
    rechazados_detalle = []
    for registro in registros_rechazo:
        # Obtener las URLs de las fotos de rechazo
        fotos_urls = []
        fotos_rechazo = registro.fotos_rechazo.all()
        for foto in fotos_rechazo:
            fotos_urls.append(request.build_absolute_uri(foto.foto.url))
        
        rechazados_detalle.append({
            'nombre': registro.nombre_pasajero,
            'genero': 'HOMBRE' if registro.genero == 'M' else 'MUJER' if registro.genero == 'F' else 'N/A',
            'nacionalidad': registro.pais_emision or 'N/A',
            'pasaporte': registro.numero_documento,
            'fecha_nacimiento': registro.fecha_nacimiento.strftime('%d.%m.%Y') if registro.fecha_nacimiento else 'N/A',
            'fotos': fotos_urls
        })
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            return JsonResponse({
                'fecha': fecha_obj.strftime('%Y-%m-%d'),
                'vuelo_numero': vuelo_numero,
                'total_pasajeros': total_pasajeros,
                'total_sr': total_sr,
                'total_internaciones': total_internaciones,
                'total_rechazos': total_rechazos,
                'total_conexiones': total_conexiones,
                'rechazados_detalle': rechazados_detalle,
            })
        except Exception as e:
            logger.error(f'Error al generar JSON del PIN: {str(e)}')
            return JsonResponse({'error': 'Error al generar el PIN'}, status=500)
    
    # Si no es AJAX, renderizar template completo (para compatibilidad)
    context = {
        'fecha': fecha_obj,
        'vuelo_numero': vuelo_numero,
        'total_pasajeros': total_pasajeros,
        'total_sr': total_sr,
        'total_internaciones': total_internaciones,
        'total_rechazos': total_rechazos,
        'total_conexiones': total_conexiones,
        'rechazados_detalle': rechazados_detalle,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/pin_reporte.html', context)