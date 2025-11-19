from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
import pandas as pd
from datetime import datetime
from .models import UploadBatch, Registro
from .forms import ExcelUploadForm, CreateUserForm


# ============================================
# VISTAS PARA USUARIOS NORMALES
# ============================================

@login_required
def upload_excel(request):
    """Vista para que usuarios normales suban archivos Excel"""
    # Si es superadmin, redirigir a admin_list
    if request.user.is_superuser:
        return redirect('admin_list')
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            
            try:
                # Crear batch de carga
                batch = UploadBatch.objects.create(
                    archivo=archivo,
                    usuario=request.user
                )
                
                # Leer archivo Excel con pandas
                df = pd.read_excel(archivo)
                
                # Mapeo de columnas del Excel a campos del modelo
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
                
                # Crear registros desde el DataFrame
                registros_creados = 0
                for index, row in df.iterrows():
                    registro_data = {'batch': batch}
                    
                    for excel_col, model_field in column_mapping.items():
                        if excel_col in df.columns:
                            value = row[excel_col]
                            
                            # Manejar valores NaN/None
                            if pd.isna(value):
                                value = None
                            # Convertir timestamps a datetime
                            elif isinstance(value, pd.Timestamp):
                                value = value.to_pydatetime()
                            # Parsear fecha_nacimiento de formato YYYY/MM/DD o YYYY-MM-DD
                            elif model_field == 'fecha_nacimiento' and value is not None:
                                try:
                                    fecha_str = str(value).strip()
                                    # Intentar varios formatos
                                    for formato in ['%Y/%m/%d', '%Y-%m-%d', '%Y%m%d']:
                                        try:
                                            value = datetime.strptime(fecha_str, formato).date()
                                            break
                                        except ValueError:
                                            continue
                                    else:
                                        # Si no coincide con ningún formato, dejar como None
                                        value = None
                                except:
                                    value = None
                            # Convertir a string para campos de texto
                            elif model_field in ['numero_equipaje', 'informacion_contacto', 'contacto_reserva', 
                                                'contacto_pasajero', 'numero_ticket',
                                                'salida_planificada']:
                                value = str(value) if value is not None else None
                            
                            registro_data[model_field] = value
                    
                    Registro.objects.create(**registro_data)
                    registros_creados += 1
                
                messages.success(request, f' Archivo cargado exitosamente. {registros_creados} registros creados.')
                return redirect('upload_excel')
                
            except Exception as e:
                messages.error(request, f' Error al procesar el archivo: {str(e)}')
                if 'batch' in locals():
                    batch.delete()
    else:
        form = ExcelUploadForm()
    
    # Mostrar historial de cargas del usuario
    mis_cargas = UploadBatch.objects.filter(usuario=request.user).order_by('-fecha_carga')[:10]
    
    context = {
        'form': form,
        'mis_cargas': mis_cargas,
    }
    
    return render(request, 'uploader/upload.html', context)


# ============================================
# VISTAS PARA SUPERADMIN
# ============================================

@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='upload_excel')
def admin_list(request):
    """Vista para que superusuarios vean y modifiquen registros"""
    # Obtener todos los registros
    registros = Registro.objects.select_related('batch', 'batch__usuario').all()
    
    # Filtros
    batch_id = request.GET.get('batch')
    if batch_id:
        registros = registros.filter(batch_id=batch_id)
    
    confirmado = request.GET.get('confirmado')
    if confirmado:
        registros = registros.filter(confirmado=(confirmado == 'true'))
    
    inadmitido = request.GET.get('inadmitido')
    if inadmitido:
        registros = registros.filter(inadmitido=(inadmitido == 'true'))
    
    # Paginación
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener todos los batches para el filtro
    batches = UploadBatch.objects.all()
    
    context = {
        'page_obj': page_obj,
        'batches': batches,
    }
    
    return render(request, 'uploader/admin_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_registro(request, registro_id):
    """Vista AJAX para actualizar campos administrativos"""
    if request.method == 'POST':
        try:
            registro = Registro.objects.get(id=registro_id)
            
            # Actualizar campos administrativos
            if 'confirmado' in request.POST:
                registro.confirmado = request.POST.get('confirmado') == 'true'
            
            if 'inadmitido' in request.POST:
                registro.inadmitido = request.POST.get('inadmitido') == 'true'
            
            if 'comentario' in request.POST:
                registro.comentario = request.POST.get('comentario')
            
            registro.save()
            messages.success(request, '✅ Registro actualizado exitosamente.')
            
        except Registro.DoesNotExist:
            messages.error(request, '❌ Registro no encontrado.')
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {str(e)}')
    
    return redirect('admin_list')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_user(request):
    """Vista para que Administrador cree usuarios"""
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = False
            user.is_staff = False
            user.save()
            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('create_user')
    else:
        form = CreateUserForm()

    # Listar usuarios existentes (esto va fuera del else)
    usuarios = User.objects.filter(is_superuser=False).order_by('-date_joined')

    context = {
        'form': form,
        'usuarios': usuarios,
    }
    return render(request, 'uploader/create_user.html', context)