"""
Vistas relacionadas con los casos especiales (duplicados, conflictos)
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from ..models import CasoEspecial, Registro


@login_required
def casos_especiales_list(request):
    """Vista para listar todos los casos especiales pendientes y resueltos"""
    filtro_estado = request.GET.get('estado', 'pendiente')
    
    if filtro_estado == 'todos':
        casos = CasoEspecial.objects.all()
    else:
        casos = CasoEspecial.objects.filter(estado=filtro_estado)
    
    casos = casos.select_related('registro', 'registro__batch', 'resuelto_por').order_by('-fecha_creacion')
    
    # Paginar
    paginator = Paginator(casos, 20)
    page = request.GET.get('page', 1)
    casos_paginados = paginator.get_page(page)
    
    # Enriquecer cada caso con los registros conflictivos
    for caso in casos_paginados:
        caso.conflictivos = caso.registros_conflictivos
    
    context = {
        'casos': casos_paginados,
        'filtro_estado': filtro_estado,
        'total_pendientes': CasoEspecial.objects.filter(estado='pendiente').count(),
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/casos_especiales_list.html', context)


@login_required
def resolver_caso_aceptar(request, caso_id):
    """Aceptar ambos registros como válidos"""
    if request.method == 'POST':
        caso = get_object_or_404(CasoEspecial, id=caso_id)
        
        # Marcar como resuelto
        caso.estado = 'aceptado'
        caso.resuelto_por = request.user
        caso.fecha_resolucion = timezone.now()
        caso.notas_admin = request.POST.get('notas', 'Ambos registros aceptados como válidos')
        caso.save()
        
        # Confirmar todos los registros
        caso.registro.segunda_revision = True
        caso.registro.save()
        
        for reg_conf in caso.registros_conflictivos:
            reg_conf.segunda_revision = True
            reg_conf.save()
        
        messages.success(request, f'✅ Caso #{caso.id} aceptado. Todos los registros se confirmaron como válidos.')
        return redirect('casos_especiales_list')
    
    return redirect('casos_especiales_list')


@login_required
def resolver_caso_editar(request, caso_id, registro_id):
    """Editar el número de documento de uno de los registros"""
    if request.method == 'POST':
        caso = get_object_or_404(CasoEspecial, id=caso_id)
        registro = get_object_or_404(Registro, id=registro_id)
        
        nuevo_documento = request.POST.get('nuevo_documento', '').strip()
        
        if not nuevo_documento:
            messages.error(request, '❌ Debe proporcionar un número de documento nuevo.')
            return redirect('casos_especiales_list')
        
        # Verificar que el nuevo documento no exista
        duplicado = Registro.objects.filter(
            numero_documento=nuevo_documento,
            vuelo_numero=registro.vuelo_numero,
            vuelo_fecha=registro.vuelo_fecha
        ).exists()
        
        if duplicado:
            messages.error(request, f'❌ El documento {nuevo_documento} ya existe para este vuelo y fecha.')
            return redirect('casos_especiales_list')
        
        # Actualizar documento
        documento_anterior = registro.numero_documento
        registro.numero_documento = nuevo_documento
        registro.save()
        
        # Marcar caso como resuelto
        caso.estado = 'editado'
        caso.documento_nuevo = nuevo_documento
        caso.resuelto_por = request.user
        caso.fecha_resolucion = timezone.now()
        caso.notas_admin = f'Documento cambiado de {documento_anterior} a {nuevo_documento}'
        caso.save()
        
        messages.success(request, f'✅ Caso #{caso.id} resuelto. Documento actualizado a {nuevo_documento}.')
        return redirect('casos_especiales_list')
    
    return redirect('casos_especiales_list')


@login_required
def resolver_caso_inadmitir(request, caso_id, registro_id):
    """Marcar un registro como rechazado"""
    if request.method == 'POST':
        caso = get_object_or_404(CasoEspecial, id=caso_id)
        registro = get_object_or_404(Registro, id=registro_id)
        
        # Marcar como rechazado (automáticamente activa SR y R)
        registro.segunda_revision = True  # Activar SR
        registro.rechazado = True  # Activar R
        registro.internacion = False  # Desactivar I (incompatible con R)
        registro.comentario = request.POST.get('motivo', 'Marcado como rechazado por documento duplicado')
        registro.save()
        
        # Marcar caso como resuelto
        caso.estado = 'inadmitido'
        caso.resuelto_por = request.user
        caso.fecha_resolucion = timezone.now()
        caso.notas_admin = f'Registro {registro.nombre_pasajero} marcado como rechazado (SR + R activados automáticamente)'
        caso.save()
        
        messages.success(request, f'✅ Caso #{caso.id} resuelto. Registro marcado como INADMITIDO (SR + R).')
        return redirect('casos_especiales_list')
    
    return redirect('casos_especiales_list')


@login_required
def resolver_caso_eliminar(request, caso_id, registro_id):
    """Eliminar un registro duplicado"""
    if request.method == 'POST':
        caso = get_object_or_404(CasoEspecial, id=caso_id)
        registro = get_object_or_404(Registro, id=registro_id)
        
        nombre_eliminado = registro.nombre_pasajero
        
        # Eliminar el registro
        registro.delete()
        
        # Marcar caso como resuelto
        caso.estado = 'eliminado'
        caso.resuelto_por = request.user
        caso.fecha_resolucion = timezone.now()
        caso.notas_admin = f'Registro de {nombre_eliminado} eliminado del sistema'
        caso.save()
        
        messages.success(request, f'✅ Caso #{caso.id} resuelto. Registro eliminado.')
        return redirect('casos_especiales_list')
    
    return redirect('casos_especiales_list')