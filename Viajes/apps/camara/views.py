from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.uploader.models import Registro
from .models import FotoRechazo
from .forms import FotoRechazoForm


@login_required
@require_POST
def subir_foto_rechazo(request, registro_id):
    """Vista para subir foto de un rechazo (AJAX)"""
    registro = get_object_or_404(Registro, id=registro_id)
    
    # Verificar que el registro esté marcado como rechazado
    if not registro.rechazado:
        return JsonResponse({
            'success': False,
            'error': 'El registro debe estar marcado como rechazado para subir una foto.'
        }, status=400)
    
    form = FotoRechazoForm(request.POST, request.FILES)
    
    if form.is_valid():
        foto = form.save(commit=False)
        foto.registro = registro
        foto.usuario_captura = request.user
        foto.save()
        
        # Actualizar el comentario del registro si se proporcionó
        comentario = request.POST.get('comentario', '').strip()
        if comentario:
            registro.comentario = comentario
            registro.save(update_fields=['comentario'])
        
        return JsonResponse({
            'success': True,
            'message': f'Foto subida correctamente para {registro.nombre_pasajero}',
            'foto_id': foto.id,
            'foto_url': foto.foto.url
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Archivo inválido. Solo se permiten imágenes JPG, JPEG, PNG o WEBP.',
            'errors': form.errors
        }, status=400)


@login_required
def ver_fotos_rechazo(request, registro_id):
    """Vista para ver todas las fotos de un rechazo"""
    registro = get_object_or_404(Registro, id=registro_id)
    fotos = registro.fotos_rechazo.all()
    
    return JsonResponse({
        'success': True,
        'registro': {
            'id': registro.id,
            'nombre': registro.nombre_pasajero,
            'documento': registro.numero_documento
        },
        'fotos': [
            {
                'id': foto.id,
                'url': foto.foto.url,
                'fecha': foto.fecha_captura.strftime('%d/%m/%Y %H:%M'),
                'usuario': foto.usuario_captura.username if foto.usuario_captura else 'Desconocido',
                'notas': foto.notas or ''
            }
            for foto in fotos
        ]
    })