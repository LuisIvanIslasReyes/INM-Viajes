from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ExcelUploadForm, CreateUserForm
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import UploadBatch, Registro, CasoEspecial
from django.contrib import messages
from django.db import models
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from datetime import datetime
import pandas as pd
import os


# ============================================
# VISTAS PARA TODOS LOS USUARIOS
# ============================================

@login_required
def upload_excel(request):
    """Vista para subir archivos Excel"""
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        
        # Validar que se hayan seleccionado archivos
        archivos = request.FILES.getlist('archivo')
        if not archivos:
            messages.error(request, '📁 Por favor, selecciona al menos un archivo Excel antes de subir.')
            return redirect('upload_excel')
        
        if len(archivos) > 2:
            messages.error(request, '❌ Solo puedes subir máximo 2 archivos a la vez.')
            return redirect('upload_excel')
        
        # Procesar cada archivo
        total_registros_creados = 0
        total_casos_especiales = 0
        total_registros_error = 0
        archivos_procesados = 0
        
        for archivo in archivos:
            try:
                # Crear batch asociado al usuario que sube
                batch = UploadBatch.objects.create(
                    archivo=archivo,
                    usuario=request.user
                )
                
                df = pd.read_excel(archivo)

                if df.empty:
                    batch.delete()
                    messages.warning(request, f'📋 El archivo "{archivo.name}" está vacío o no contiene datos válidos.')
                    continue
                
                column_mapping = {
                    '航班号': 'vuelo_numero',
                    '航班日期': 'vuelo_fecha',
                    '起飞机场': 'aeropuerto_salida',
                    '落地机场': 'aeropuerto_llegada',
                    '计划离港': 'salida_planificada',
                    '旅客姓名': 'nombre_pasajero',
                    '证件号': 'numero_documento',
                    '座位号': 'numero_asiento',
                    '行李号': 'numero_equipaje',
                    '件数': 'piezas',
                    '重量': 'peso',
                    '值机状态': 'estado_checkin',
                    '联系信息': 'informacion_contacto',
                    '预订人联系方式': 'contacto_reserva',
                    '乘机人联系方式': 'contacto_pasajero',
                    '票号': 'numero_ticket',
                    '旅客生日': 'fecha_nacimiento',
                    '性别': 'genero',
                    '签发国编码': 'codigo_pais_emision',
                    '签发国': 'pais_emision',
                }
                
                registros_creados = 0
                registros_error = 0
                casos_especiales_creados = 0
                
                for index, row in df.iterrows():
                    try:
                        registro_data = {'batch': batch}
                        
                        for excel_col, model_field in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                
                                if pd.isna(value):
                                    value = None
                                elif isinstance(value, pd.Timestamp):
                                    value = value.to_pydatetime()
                                elif model_field == 'fecha_nacimiento' and value is not None:
                                    try:
                                        fecha_str = str(value).strip()
                                        for formato in ['%Y/%m/%d', '%Y-%m-%d', '%Y%m%d']:
                                            try:
                                                value = datetime.strptime(fecha_str, formato).date()
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            value = None
                                    except:
                                        value = None
                                elif model_field in ['numero_equipaje', 'informacion_contacto', 'contacto_reserva', 
                                                    'contacto_pasajero', 'numero_ticket', 'salida_planificada']:
                                    value = str(value) if value is not None else None
                                
                                registro_data[model_field] = value
                        
                        # Verificar duplicados
                        numero_doc = registro_data.get('numero_documento')
                        vuelo_num = registro_data.get('vuelo_numero')
                        vuelo_fecha = registro_data.get('vuelo_fecha')
                        nombre = registro_data.get('nombre_pasajero')
                        
                        # Crear el registro SIEMPRE (no bloqueamos nada)
                        nuevo_registro = Registro.objects.create(**registro_data)
                        registros_creados += 1
                        
                        # DESPUÉS de crear, verificar si es un Caso Especial
                        if numero_doc and vuelo_num and vuelo_fecha:
                            # Buscar registros con mismo documento + mismo vuelo + misma fecha
                            # (sin importar el nombre - pueden ser hermanos o datos duplicados)
                            registros_mismo_vuelo_doc = Registro.objects.filter(
                                numero_documento=numero_doc,
                                vuelo_numero=vuelo_num,
                                vuelo_fecha=vuelo_fecha
                            ).exclude(
                                id=nuevo_registro.id  # Excluir el que acabamos de crear
                            )
                            
                            # Si encontramos coincidencias, es un Caso Especial
                            if registros_mismo_vuelo_doc.exists():
                                # Determinar razón basado en si el nombre es igual o diferente
                                mismo_nombre = registros_mismo_vuelo_doc.filter(nombre_pasajero=nombre).exists()
                                
                                CasoEspecial.objects.create(
                                    registro=nuevo_registro,
                                    razon='mismo_vuelo_fecha' if mismo_nombre else 'documento_duplicado',
                                    estado='pendiente',
                                    documento_original=numero_doc,
                                    registros_conflictivos_ids=list(registros_mismo_vuelo_doc.values_list('id', flat=True))
                                )
                                casos_especiales_creados += 1
                    
                    except Exception as e:
                        registros_error += 1
                        continue
                
                # Acumular totales
                total_registros_creados += registros_creados
                total_casos_especiales += casos_especiales_creados
                total_registros_error += registros_error
                archivos_procesados += 1
                
            except Exception as e:
                messages.error(request, f'❌ Error al procesar "{archivo.name}": {str(e)}')
                if 'batch' in locals():
                    batch.delete()
                continue
        
        # Mensajes finales consolidados
        if archivos_procesados > 0:
            if total_registros_creados > 0:
                messages.success(request, f'✅ ¡{archivos_procesados} archivo(s) procesado(s) exitosamente! Se agregaron {total_registros_creados} registro(s) en total.')
            
            if total_casos_especiales > 0:
                messages.warning(request, f'🔔 IMPORTANTE: Se crearon {total_casos_especiales} Caso(s) Especial(es) que requieren tu revisión. Ve a "Casos Especiales" en el menú.')
            
            if total_registros_error > 0:
                messages.info(request, f'ℹ️ {total_registros_error} registro(s) tuvieron errores y no se pudieron procesar.')
        else:
            messages.error(request, '❌ No se pudo procesar ningún archivo.')
        
        return redirect('admin_list')
    else:
        form = ExcelUploadForm()
    
    # Mostrar TODAS las cargas (no solo del usuario)
    mis_cargas = UploadBatch.objects.all().order_by('-fecha_carga')[:10]
    
    context = {
        'form': form,
        'mis_cargas': mis_cargas,
    }
    
    return render(request, 'uploader/upload.html', context)

@login_required
def update_registro(request, registro_id):
    """Vista para actualizar campos (TODOS pueden editar TODO)"""
    from urllib.parse import urlparse, parse_qs, urlencode
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
    
    context = {
        'page_obj': page_obj,
        'batches': batches,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/admin_list.html', context)


@login_required
def date_range_report(request):
    """Vista de reporte por rango de fechas con agrupación por día"""
    from collections import OrderedDict
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    registros = Registro.objects.all().select_related('batch', 'batch__usuario').order_by('vuelo_fecha', 'vuelo_numero')
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        registros = registros.filter(vuelo_fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(vuelo_fecha__lte=fecha_fin)
    
    # Agrupar por fecha
    registros_por_fecha = OrderedDict()
    for registro in registros:
        fecha = registro.vuelo_fecha
        if fecha not in registros_por_fecha:
            registros_por_fecha[fecha] = []
        registros_por_fecha[fecha].append(registro)
    
    # Calcular totales por fecha
    estadisticas_por_fecha = []
    for fecha, regs in registros_por_fecha.items():
        estadisticas_por_fecha.append({
            'fecha': fecha,
            'registros': regs,
            'total': len(regs),
            'segunda_revisions': sum(1 for r in regs if r.segunda_revision),
            'rechazados': sum(1 for r in regs if r.rechazado),
        })
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estadisticas_por_fecha': estadisticas_por_fecha,
        'total_registros': registros.count(),
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/date_range_report.html', context)


# ============================================
# VISTAS SOLO PARA SUPERADMIN
# ============================================

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


@login_required
def download_batch_file(request, batch_id):
    """Vista para descargar el archivo Excel de un batch"""
    batch = get_object_or_404(UploadBatch, id=batch_id)
    
    # Verificar que el archivo existe
    if not batch.archivo or not os.path.exists(batch.archivo.path):
        messages.error(request, '❌ El archivo no existe en el servidor.')
        return redirect('batch_list')
    
    try:
        # Abrir el archivo para descarga
        response = FileResponse(
            open(batch.archivo.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(batch.archivo.name)
        )
        return response
    except Exception as e:
        messages.error(request, f'❌ Error al descargar el archivo: {str(e)}')
        return redirect('batch_list')


@login_required
def check_duplicates(request):
    """Vista para identificar registros duplicados"""
    # Encontrar documentos que aparecen más de una vez
    from django.db.models import Count
    
    duplicados = Registro.objects.values('numero_documento', 'nombre_pasajero').annotate(
        total=Count('id')
    ).filter(total__gt=1).order_by('-total')
    
    # Obtener detalles completos de los duplicados
    duplicados_detalle = []
    for dup in duplicados:
        registros = Registro.objects.filter(
            numero_documento=dup['numero_documento']
        ).select_related('batch', 'batch__usuario').order_by('vuelo_fecha', 'batch__fecha_carga')
        
        duplicados_detalle.append({
            'documento': dup['numero_documento'],
            'pasajero': dup['nombre_pasajero'],
            'total': dup['total'],
            'registros': list(registros)
        })
    
    context = {
        'duplicados_detalle': duplicados_detalle,
        'total_duplicados': len(duplicados_detalle),
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/check_duplicates.html', context)


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
        
        # Marcar como rechazado
        registro.rechazado = True
        registro.comentario = request.POST.get('motivo', 'Marcado como rechazado por documento duplicado')
        registro.save()
        
        # Marcar caso como resuelto
        caso.estado = 'rechazado'
        caso.resuelto_por = request.user
        caso.fecha_resolucion = timezone.now()
        caso.notas_admin = f'Registro {registro.nombre_pasajero} marcado como rechazado'
        caso.save()
        
        messages.success(request, f'✅ Caso #{caso.id} resuelto. Registro marcado como rechazado.')
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