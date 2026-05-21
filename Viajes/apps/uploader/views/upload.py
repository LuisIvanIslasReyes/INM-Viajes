"""
Vistas relacionadas con la subida de archivos Excel
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.db import models
from datetime import datetime
import pandas as pd

from ..forms import ExcelUploadForm
from ..models import UploadBatch, Registro, CasoEspecial, Notificacion
from ..utils.parsers import obtener_nacionalidad


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
        total_sin_documento = 0
        archivos_procesados = 0
        
        for archivo in archivos:
            try:
                df = pd.read_excel(archivo)

                if df.empty:
                    messages.warning(request, f'📋 El archivo "{archivo.name}" está vacío o no contiene datos válidos.')
                    continue
                
                # Extraer información del vuelo del primer registro
                primer_registro = df.iloc[0]
                vuelo_numero = str(primer_registro.get('航班号', '')).strip() if '航班号' in df.columns else None
                
                # Detectar fecha del vuelo
                fecha_vuelo = None
                if '航班日期' in df.columns:
                    fecha_valor = primer_registro.get('航班日期')
                    if pd.notna(fecha_valor):
                        if isinstance(fecha_valor, pd.Timestamp):
                            fecha_vuelo = fecha_valor.date()
                        else:
                            try:
                                fecha_vuelo = pd.to_datetime(fecha_valor).date()
                            except:
                                pass
                
                # Detectar tipo de vuelo basado en el aeropuerto de llegada
                tipo_vuelo = None
                if '落地机场' in df.columns:
                    aeropuerto_llegada = str(primer_registro.get('落地机场', '')).upper()
                    if 'TIJ' in aeropuerto_llegada or 'TIJUANA' in aeropuerto_llegada:
                        tipo_vuelo = 'PEK-TIJ'
                    elif 'MEX' in aeropuerto_llegada or 'MEXICO' in aeropuerto_llegada or 'MÉXICO' in aeropuerto_llegada:
                        tipo_vuelo = 'PEK-MEX'
                
                # Crear batch asociado al usuario que sube
                batch = UploadBatch.objects.create(
                    archivo=archivo,
                    usuario=request.user,
                    vuelo_numero=vuelo_numero,
                    tipo_vuelo=tipo_vuelo,
                    fecha_vuelo=fecha_vuelo
                )
                
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
                sin_documento_creados = 0

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
                                elif model_field in ['numero_documento', 'numero_equipaje', 'informacion_contacto', 'contacto_reserva',
                                                    'contacto_pasajero', 'numero_ticket', 'salida_planificada', 'numero_asiento']:
                                    # Convertir a string para manejar tanto números como texto con prefijos
                                    if value is not None and not pd.isna(value):
                                        # Si es número, convertir a string y limpiar notación científica
                                        if isinstance(value, (int, float)):
                                            # Convertir sin notación científica
                                            value = f"{value:.0f}" if value == int(value) else str(value)
                                        else:
                                            value = str(value).strip()
                                    else:
                                        value = None

                                registro_data[model_field] = value

                        # CharFields NOT NULL en DB no aceptan None — convertir a ''
                        _char_not_null = [
                            'vuelo_numero', 'aeropuerto_salida', 'aeropuerto_llegada',
                            'nombre_pasajero', 'numero_asiento', 'estado_checkin',
                            'numero_ticket', 'genero', 'codigo_pais_emision', 'pais_emision',
                        ]
                        for _f in _char_not_null:
                            if registro_data.get(_f) is None:
                                registro_data[_f] = ''

                        # Parsear nacionalidad desde el código ISO
                        if 'codigo_pais_emision' in registro_data and registro_data['codigo_pais_emision']:
                            codigo_iso = registro_data['codigo_pais_emision']
                            registro_data['pais_emision'] = obtener_nacionalidad(codigo_iso)

                        # Verificar duplicados
                        numero_doc = registro_data.get('numero_documento')
                        vuelo_num = registro_data.get('vuelo_numero')
                        vuelo_fecha = registro_data.get('vuelo_fecha')
                        nombre = registro_data.get('nombre_pasajero')

                        # Crear el registro SIEMPRE (no bloqueamos nada)
                        nuevo_registro = Registro.objects.create(**registro_data)
                        registros_creados += 1

                        # CASO ESPECIAL URGENTE: pasajero sin número de documento
                        if not numero_doc:
                            CasoEspecial.objects.create(
                                registro=nuevo_registro,
                                razon='sin_documento',
                                estado='pendiente',
                                documento_original='',
                                registros_conflictivos_ids=[]
                            )
                            sin_documento_creados += 1

                        # DESPUÉS de crear, verificar si es un Caso Especial por duplicado
                        elif vuelo_num and vuelo_fecha:
                            # Buscar registros con mismo documento + mismo vuelo + misma fecha
                            registros_mismo_vuelo_doc = Registro.objects.filter(
                                numero_documento=numero_doc,
                                vuelo_numero=vuelo_num,
                                vuelo_fecha=vuelo_fecha
                            ).exclude(
                                id=nuevo_registro.id  # Excluir el que acabamos de crear
                            )

                            # Si encontramos coincidencias, SIEMPRE crear caso especial
                            if registros_mismo_vuelo_doc.exists():
                                # Determinar razón basada en si el nombre es diferente o igual
                                nombre_diferente = registros_mismo_vuelo_doc.exclude(nombre_pasajero=nombre).exists()

                                # SIEMPRE crear caso especial, pero con diferentes razones:
                                # - NOMBRE DIFERENTE = documento_duplicado (fraude/error grave)
                                # - NOMBRE IGUAL = mismo_vuelo_fecha (carga duplicada)
                                razon = 'documento_duplicado' if nombre_diferente else 'mismo_vuelo_fecha'

                                CasoEspecial.objects.create(
                                    registro=nuevo_registro,
                                    razon=razon,
                                    estado='pendiente',
                                    documento_original=numero_doc,
                                    registros_conflictivos_ids=list(registros_mismo_vuelo_doc.values_list('id', flat=True))
                                )
                                casos_especiales_creados += 1

                    except Exception as e:
                        # Mostrar información detallada del error
                        fila_excel = index + 2  # +2 porque Excel empieza en 1 y tiene encabezado
                        nombre_error = row.get('旅客姓名', 'N/A')
                        doc_error = row.get('证件号', 'N/A')
                        print(f"❌ ERROR en fila {fila_excel}: {nombre_error} (Doc: {doc_error}) - {str(e)}")
                        registros_error += 1
                        continue
                
                # Acumular totales
                total_registros_creados += registros_creados
                total_casos_especiales += casos_especiales_creados
                total_registros_error += registros_error
                total_sin_documento += sin_documento_creados
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
                
                # Crear notificación de carga exitosa
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='no_importante',
                    categoria='carga_exitosa',
                    titulo=f'Carga exitosa: {total_registros_creados} registros',
                    mensaje=f'Se procesaron {archivos_procesados} archivo(s) correctamente con un total de {total_registros_creados} registros agregados.',
                    enlace=reverse('admin_list')
                )
            
            if total_sin_documento > 0:
                messages.error(request, f'🚨 URGENTE: {total_sin_documento} pasajero(s) ingresaron SIN número de documento. Requieren atención inmediata en "Casos Especiales".')

                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='importante',
                    categoria='casos_especiales',
                    titulo=f'🚨 URGENTE: {total_sin_documento} pasajero(s) sin documento',
                    mensaje=f'{total_sin_documento} pasajero(s) fueron registrados sin número de documento. Se requiere revisión y corrección inmediata antes del vuelo.',
                    enlace=reverse('casos_especiales_list')
                )

            if total_casos_especiales > 0:
                messages.warning(request, f'🔔 IMPORTANTE: Se crearon {total_casos_especiales} Caso(s) Especial(es) que requieren tu revisión. Ve a "Casos Especiales" en el menú.')

                # Crear notificación IMPORTANTE de casos especiales
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='importante',
                    categoria='casos_especiales',
                    titulo=f'⚠️ {total_casos_especiales} Casos Especiales detectados',
                    mensaje=f'Se encontraron {total_casos_especiales} caso(s) que requieren tu revisión inmediata: documentos duplicados o mismo vuelo/fecha.',
                    enlace=reverse('casos_especiales_list')
                )
            
            if total_registros_error > 0:
                messages.info(request, f'ℹ️ {total_registros_error} registro(s) tuvieron errores y no se pudieron procesar.')
                
                # Crear notificación IMPORTANTE de errores
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='importante',
                    categoria='error_registro',
                    titulo=f'❌ {total_registros_error} registros con errores',
                    mensaje=f'Algunos registros no pudieron procesarse debido a errores de formato o datos inválidos. Revisa los archivos Excel.',
                    enlace=reverse('upload_excel')
                )
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
def check_duplicates(request):
    """Vista para identificar registros duplicados"""
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