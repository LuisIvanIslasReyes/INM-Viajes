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
# DICCIONARIO DE CÓDIGOS ISO DE PAÍSES
# ============================================
PAISES_ISO = {
    'AFG': 'Afganistán', 'ALB': 'Albania', 'DEU': 'Alemania', 'AND': 'Andorra', 'AGO': 'Angola',
    'ATG': 'Antigua y Barbuda', 'SAU': 'Arabia Saudita', 'DZA': 'Argelia', 'ARG': 'Argentina', 
    'ARM': 'Armenia', 'AUS': 'Australia', 'AUT': 'Austria', 'AZE': 'Azerbaiyán', 'BHS': 'Bahamas',
    'BGD': 'Bangladés', 'BRB': 'Barbados', 'BHR': 'Baréin', 'BEL': 'Bélgica', 'BLZ': 'Belice',
    'BEN': 'Benín', 'BLR': 'Bielorrusia', 'MMR': 'Birmania', 'BOL': 'Bolivia', 'BIH': 'Bosnia y Herzegovina',
    'BWA': 'Botsuana', 'BRA': 'Brasil', 'BRN': 'Brunéi', 'BGR': 'Bulgaria', 'BFA': 'Burkina Faso',
    'BDI': 'Burundi', 'BTN': 'Bután', 'CPV': 'Cabo Verde', 'KHM': 'Camboya', 'CMR': 'Camerún',
    'CAN': 'Canadá', 'QAT': 'Catar', 'TCD': 'Chad', 'CHL': 'Chile', 'CHN': 'China',
    'CYP': 'Chipre', 'VAT': 'Ciudad del Vaticano', 'COL': 'Colombia', 'COM': 'Comoras', 
    'PRK': 'Corea del Norte', 'KOR': 'Corea del Sur', 'CIV': 'Costa de Marfil', 'CRI': 'Costa Rica',
    'HRV': 'Croacia', 'CUB': 'Cuba', 'DNK': 'Dinamarca', 'DMA': 'Dominica', 'ECU': 'Ecuador',
    'EGY': 'Egipto', 'SLV': 'El Salvador', 'ARE': 'Emiratos Árabes Unidos', 'ERI': 'Eritrea',
    'SVK': 'Eslovaquia', 'SVN': 'Eslovenia', 'ESP': 'España', 'USA': 'Estados Unidos',
    'EST': 'Estonia', 'ETH': 'Etiopía', 'PHL': 'Filipinas', 'FIN': 'Finlandia', 'FJI': 'Fiyi',
    'FRA': 'Francia', 'GAB': 'Gabón', 'GMB': 'Gambia', 'GEO': 'Georgia', 'GHA': 'Ghana',
    'GRD': 'Granada', 'GRC': 'Grecia', 'GTM': 'Guatemala', 'GNB': 'Guinea-Bisáu', 'GIN': 'Guinea',
    'GNQ': 'Guinea Ecuatorial', 'GUY': 'Guyana', 'HTI': 'Haití', 'HND': 'Honduras', 'HUN': 'Hungría',
    'IND': 'India', 'IDN': 'Indonesia', 'IRQ': 'Irak', 'IRN': 'Irán', 'IRL': 'Irlanda',
    'ISL': 'Islandia', 'MHL': 'Islas Marshall', 'SLB': 'Islas Salomón', 'ISR': 'Israel',
    'ITA': 'Italia', 'JAM': 'Jamaica', 'JPN': 'Japón', 'JOR': 'Jordania', 'KAZ': 'Kazajistán',
    'KEN': 'Kenia', 'KGZ': 'Kirguistán', 'KIR': 'Kiribati', 'KWT': 'Kuwait', 'LAO': 'Laos',
    'LSO': 'Lesoto', 'LVA': 'Letonia', 'LBN': 'Líbano', 'LBR': 'Liberia', 'LBY': 'Libia',
    'LIE': 'Liechtenstein', 'LTU': 'Lituania', 'LUX': 'Luxemburgo', 'MKD': 'Macedonia del Norte',
    'MDG': 'Madagascar', 'MYS': 'Malasia', 'MWI': 'Malaui', 'MDV': 'Maldivas', 'MLI': 'Mali',
    'MLT': 'Malta', 'MAR': 'Marruecos', 'MUS': 'Mauricio', 'MRT': 'Mauritania', 'MEX': 'México',
    'FSM': 'Micronesia', 'MDA': 'Moldavia', 'MCO': 'Mónaco', 'MNG': 'Mongolia', 'MNE': 'Montenegro',
    'MOZ': 'Mozambique', 'NAM': 'Namibia', 'NRU': 'Nauru', 'NPL': 'Nepal', 'NIC': 'Nicaragua',
    'NER': 'Níger', 'NGA': 'Nigeria', 'NOR': 'Noruega', 'NZL': 'Nueva Zelanda', 'OMN': 'Omán',
    'NLD': 'Países Bajos', 'PAK': 'Pakistán', 'PLW': 'Palaos', 'PSE': 'Palestina', 'PAN': 'Panamá',
    'PNG': 'Papúa Nueva Guinea', 'PRY': 'Paraguay', 'PER': 'Perú', 'POL': 'Polonia', 'PRT': 'Portugal',
    'GBR': 'Reino Unido', 'CAF': 'República Centroafricana', 'CZE': 'República Checa',
    'COG': 'República del Congo', 'COD': 'República Democrática del Congo', 'DOM': 'República Dominicana',
    'RWA': 'Ruanda', 'ROU': 'Rumania', 'RUS': 'Rusia', 'WSM': 'Samoa', 'KNA': 'San Cristóbal y Nieves',
    'SMR': 'San Marino', 'VCT': 'San Vicente y las Granadinas', 'LCA': 'Santa Lucía',
    'STP': 'Santo Tomé y Príncipe', 'SEN': 'Senegal', 'SRB': 'Serbia', 'SYC': 'Seychelles',
    'SLE': 'Sierra Leona', 'SGP': 'Singapur', 'SYR': 'Siria', 'SOM': 'Somalia', 'LKA': 'Sri Lanka',
    'SWZ': 'Esuatini', 'ZAF': 'Sudáfrica', 'SDN': 'Sudán', 'SSD': 'Sudán del Sur', 'SWE': 'Suecia',
    'CHE': 'Suiza', 'SUR': 'Surinam', 'THA': 'Tailandia', 'TZA': 'Tanzania', 'TJK': 'Tayikistán',
    'TLS': 'Timor Oriental', 'TGO': 'Togo', 'TON': 'Tonga', 'TTO': 'Trinidad y Tobago', 'TUN': 'Túnez',
    'TKM': 'Turkmenistán', 'TUR': 'Turquía', 'TUV': 'Tuvalu', 'UKR': 'Ucrania', 'UGA': 'Uganda',
    'URY': 'Uruguay', 'UZB': 'Uzbekistán', 'VUT': 'Vanuatu', 'VEN': 'Venezuela', 'VNM': 'Vietnam',
    'YEM': 'Yemen', 'DJI': 'Yibuti', 'ZMB': 'Zambia', 'ZWE': 'Zimbabue',
    # Códigos adicionales de 2 letras comunes
    'CN': 'China', 'US': 'Estados Unidos', 'MX': 'México', 'BR': 'Brasil', 'AR': 'Argentina',
    'CA': 'Canadá', 'JP': 'Japón', 'KR': 'Corea del Sur', 'IN': 'India', 'GB': 'Reino Unido',
    'FR': 'Francia', 'DE': 'Alemania', 'IT': 'Italia', 'ES': 'España', 'RU': 'Rusia',
    'AU': 'Australia', 'NZ': 'Nueva Zelanda', 'TH': 'Tailandia', 'VN': 'Vietnam', 'PH': 'Filipinas',
}

def obtener_nacionalidad(codigo_pais):
    """
    Convierte un código ISO de país a su nombre completo en español.
    Soporta códigos de 2 y 3 letras (ISO 3166-1 alpha-2 y alpha-3).
    
    Args:
        codigo_pais: Código ISO del país (ej: 'CHN', 'CN', 'MEX', 'MX')
        
    Returns:
        Nombre del país en español o el código original si no se encuentra
    """
    if not codigo_pais or pd.isna(codigo_pais):
        return 'N/A'
    
    codigo = str(codigo_pais).strip().upper()
    return PAISES_ISO.get(codigo, codigo)


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
                from .models import Notificacion
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='no_importante',
                    categoria='carga_exitosa',
                    titulo=f'Carga exitosa: {total_registros_creados} registros',
                    mensaje=f'Se procesaron {archivos_procesados} archivo(s) correctamente con un total de {total_registros_creados} registros agregados.',
                    enlace='/admin_list/'
                )
            
            if total_casos_especiales > 0:
                messages.warning(request, f'🔔 IMPORTANTE: Se crearon {total_casos_especiales} Caso(s) Especial(es) que requieren tu revisión. Ve a "Casos Especiales" en el menú.')
                
                # Crear notificación IMPORTANTE de casos especiales
                from .models import Notificacion
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='importante',
                    categoria='casos_especiales',
                    titulo=f'⚠️ {total_casos_especiales} Casos Especiales detectados',
                    mensaje=f'Se encontraron {total_casos_especiales} caso(s) que requieren tu revisión inmediata: documentos duplicados o mismo vuelo/fecha.',
                    enlace='/casos-especiales/'
                )
            
            if total_registros_error > 0:
                messages.info(request, f'ℹ️ {total_registros_error} registro(s) tuvieron errores y no se pudieron procesar.')
                
                # Crear notificación IMPORTANTE de errores
                from .models import Notificacion
                Notificacion.objects.create(
                    usuario=request.user,
                    tipo='importante',
                    categoria='error_registro',
                    titulo=f'❌ {total_registros_error} registros con errores',
                    mensaje=f'Algunos registros no pudieron procesarse debido a errores de formato o datos inválidos. Revisa los archivos Excel.',
                    enlace='/upload/'
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
    from .models import Notificacion
    
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
def date_range_report(request):
    """Vista de reporte por rango de fechas - Solo muestra registros con SR, R o I"""
    from collections import OrderedDict
    from django.db.models import Q
    
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # FILTRO PRINCIPAL: Solo registros que tienen SR, R o I
    # (Los que no tienen nada están OK y no se muestran aquí)
    registros = Registro.objects.filter(
        Q(segunda_revision=True) | Q(rechazado=True) | Q(internacion=True)
    ).select_related('batch', 'batch__usuario').order_by('-vuelo_fecha', 'vuelo_numero')
    
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
            'internaciones': sum(1 for r in regs if r.internacion),
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
def generar_pin(request, fecha):
    """Vista para generar el PIN oficial del INM por fecha"""
    from datetime import datetime, timedelta
    
    # Convertir string de fecha a objeto date
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
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
        messages.error(request, f'❌ No se encontraron registros para la fecha {fecha_obj.strftime("%d/%m/%Y")}.')
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
        rechazados_detalle.append({
            'nombre': registro.nombre_pasajero,
            'genero': 'HOMBRE' if registro.genero == 'M' else 'MUJER' if registro.genero == 'F' else 'N/A',
            'nacionalidad': registro.pais_emision or 'N/A',
            'pasaporte': registro.numero_documento,
            'fecha_nacimiento': registro.fecha_nacimiento.strftime('%d.%m.%Y') if registro.fecha_nacimiento else 'N/A'
        })
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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


@login_required
def notificaciones_list(request):
    """Vista para listar notificaciones del usuario"""
    from .models import Notificacion
    
    filtro_tipo = request.GET.get('tipo', 'todas')
    
    # Obtener notificaciones del usuario actual
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
    
    # Contar no leídas
    total_no_leidas = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    context = {
        'notificaciones': notificaciones_paginadas,
        'filtro_tipo': filtro_tipo,
        'total_no_leidas': total_no_leidas,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'uploader/notificaciones_list.html', context)


@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marcar una notificación como leída"""
    from .models import Notificacion
    
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