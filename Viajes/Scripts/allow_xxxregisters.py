from datetime import datetime
import pandas as pd
from apps.uploader.models import UploadBatch, Registro, CasoEspecial
from apps.uploader.utils.parsers import obtener_nacionalidad
from django.contrib.auth.models import User
import os
from pathlib import Path
from django.utils import timezone

# Ruta dinámica al archivo Excel
BASE_DIR = Path(__file__).resolve().parent.parent.parent if '__file__' in globals() else Path.cwd().parent
excel_path = BASE_DIR / 'context' / 'HU7925_PEK-TIJ_12ENE26.xlsx'

print(f"📁 Leyendo archivo: {excel_path}")
df = pd.read_excel(excel_path)

# Obtener el batch más reciente para este vuelo
batch = UploadBatch.objects.filter(vuelo_numero='HU7925', tipo_vuelo='PEK-TIJ').order_by('-fecha_carga').first()

if not batch:
    print("Creando nuevo batch...")
    usuario = User.objects.first()
    batch = UploadBatch.objects.create(
        vuelo_numero='HU7925',
        tipo_vuelo='PEK-TIJ',
        fecha_vuelo=datetime(2026, 1, 12).date(),
        usuario=usuario
    )

print(f"✅ Usando batch ID: {batch.id}")

# Mapeo de columnas
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

# Procesar solo las filas 47-60 en Excel (índices 45-58 en pandas = 14 registros)
for index in range(45, 59):
    try:
        row = df.iloc[index]
        registro_data = {'batch': batch}
        
        for excel_col, model_field in column_mapping.items():
            if excel_col in df.columns:
                value = row[excel_col]
                
                if pd.isna(value):
                    value = None
                elif isinstance(value, pd.Timestamp):
                    value = timezone.make_aware(value.to_pydatetime())
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
                    if value is not None and not pd.isna(value):
                        if isinstance(value, (int, float)):
                            value = f"{value:.0f}" if value == int(value) else str(value)
                        else:
                            value = str(value).strip()
                    else:
                        value = None
                
                registro_data[model_field] = value
        
        # FIX: Asignar valores por defecto para campos que no pueden ser null
        if registro_data.get('numero_ticket') is None or registro_data.get('numero_ticket') == '':
            registro_data['numero_ticket'] = 'XXXCREW-SIN-TICKET'
        
        if registro_data.get('genero') is None or registro_data.get('genero') == '':
            registro_data['genero'] = 'N/A'
        
        if registro_data.get('codigo_pais_emision') is None or registro_data.get('codigo_pais_emision') == '':
            registro_data['codigo_pais_emision'] = 'XX'
        
        if registro_data.get('pais_emision') is None or registro_data.get('pais_emision') == '':
            registro_data['pais_emision'] = 'Desconocido'
        
        # Parsear nacionalidad solo si el código es válido
        if registro_data.get('codigo_pais_emision') and registro_data['codigo_pais_emision'] != 'XX':
            codigo_iso = registro_data['codigo_pais_emision']
            nacionalidad = obtener_nacionalidad(codigo_iso)
            if nacionalidad:
                registro_data['pais_emision'] = nacionalidad
        
        # Crear el registro
        nuevo_registro = Registro.objects.create(**registro_data)
        registros_creados += 1
        fila_excel = index + 2  # índice 45 + 2 = fila 47 Excel
        print(f"✅ Fila {fila_excel}: {registro_data.get('nombre_pasajero')} (Doc: {registro_data.get('numero_documento')})")
    
    except Exception as e:
        fila_excel = index + 2
        nombre_error = row.get('旅客姓名', 'N/A') if 'row' in locals() else 'N/A'
        doc_error = row.get('证件号', 'N/A') if 'row' in locals() else 'N/A'
        print(f"❌ ERROR en fila {fila_excel}: {nombre_error} (Doc: {doc_error}) - {str(e)}")
        registros_error += 1

print("\n" + "="*60)
print(f"✅ Registros creados: {registros_creados}")
print(f"❌ Errores: {registros_error}")
print("="*60)