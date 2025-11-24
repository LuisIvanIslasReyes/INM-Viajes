# Sistema de Gestión de Viajes - INM

## Configuración de la Base de Datos MySQL

### 1. Crear la Base de Datos en MySQL Workbench

Abre MySQL Workbench y ejecuta los siguientes comandos SQL:

```sql
-- Crear la base de datos
CREATE DATABASE viajes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configurar Django para MySQL

Edita el archivo `Viajes/settings.py` y actualiza la configuración de DATABASES:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'viajes_db', # O cualquier nombre que identifiques la BD
        'USER': 'root',  
        'PASSWORD': 'tu_password',  # Reemplaza con tu password de MySQL
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

### 3. Aplicar las Migraciones

Ejecuta estos comandos en PowerShell desde la carpeta `Viajes`:

```powershell
# Crear entorno virtual, en la carpeta de raíz o donde la ubique.
python -m venv env # <- Cualquier nombre para tu entorno virtual

# Activar el entorno virtual
C:/turuta/env/Scripts/Activate.ps1

# Aplicar migraciones
python manage.py migrate

# Crear un superusuario
python manage.py createsuperuser
```

### 4. Ejecutar el Servidor

```powershell
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000/`

---

## Uso del Sistema

### Para Usuarios Normales:
1. Iniciar sesión en `http://127.0.0.1:8000/admin/` con tus credenciales
2. Ir a `http://127.0.0.1:8000/` para subir archivos Excel
3. Seleccionar un archivo Excel (.xlsx) con la estructura correcta
4. Hacer clic en "Cargar Archivo"

### Para Superusuarios:
1. Iniciar sesión como superusuario
2. Acceder a la lista de registros en `http://127.0.0.1:8000/admin-list/`
3. Ver todos los registros en formato tabla
4. Modificar campos administrativos:
   - ✅ **Confirmado**: Hacer clic en el checkbox
   - ❌ **Inadmitido**: Hacer clic en el checkbox
   - ✏️ **Comentario**: Hacer clic en "Editar" para agregar/modificar comentarios
5. Usar filtros para buscar por lote, confirmado o inadmitido

---

## 📊 Estructura de los Modelos

### UploadBatch
- **archivo**: El archivo Excel cargado
- **usuario**: Usuario que cargó el archivo
- **fecha_carga**: Fecha y hora de carga

### Registro (Pasajero)

**Campos del Excel (20 campos):**
- vuelo_numero (航班号)
- vuelo_fecha (航班日期)
- aeropuerto_salida (起飞机场)
- aeropuerto_llegada (落地机场)
- salida_planificada (计划离港)
- nombre_pasajero (旅客姓名)
- numero_documento (证件号)
- numero_asiento (座位号)
- numero_equipaje (行李号)
- piezas (件数)
- peso (重量)
- estado_checkin (值机状态)
- informacion_contacto (联系信息)
- contacto_reserva (预订人联系方式)
- contacto_pasajero (乘机人联系方式)
- numero_ticket (票号)
- fecha_nacimiento (旅客生日)
- genero (性别)
- codigo_pais_emision (签发国编码)
- pais_emision (签发国)

**Campos Administrativos (3 campos):**
- **confirmado**: Boolean (Para marcar registros confirmados)
- **comentario**: TextField (Comentarios del administrador)
- **inadmitido**: Boolean (Para marcar registros inadmitidos)

---

## 🔧 Características Implementadas

✅ **Carga de Excel con Pandas**: Lee y procesa archivos Excel automáticamente
✅ **Validación de Archivos**: Solo acepta .xlsx/.xls, máximo 10MB
✅ **Interfaz Amigable**: Templates con Bootstrap-style CSS
✅ **Permisos**: Solo superusuarios pueden modificar campos administrativos
✅ **Filtros**: Por lote, confirmado, inadmitido
✅ **Paginación**: 50 registros por página
✅ **Django Admin**: Panel de administración completo
✅ **Mensajes Flash**: Feedback visual de las acciones
✅ **Modal de Edición**: Para editar comentarios sin recargar la página

---

## 📁 Estructura del Proyecto

```
Viajes/
├── manage.py
├── db.sqlite3 (No se usa, se usa MySQL)
├── media/ (Se creará automáticamente para archivos subidos)
├── uploader/
│   ├── __init__.py
│   ├── admin.py          # Configuración del Django Admin
│   ├── apps.py
│   ├── forms.py          # Formulario de carga de Excel
│   ├── models.py         # Modelos UploadBatch y Registro
│   ├── views.py          # Vistas de carga y administración
│   ├── urls.py           # URLs del app
│   ├── migrations/
│   │   └── 0001_initial.py
│   └── templates/
│       └── uploader/
│           ├── base.html       # Template base
│           ├── upload.html     # Formulario de carga
│           └── admin_list.html # Lista de registros
└── Viajes/
    ├── __init__.py
    ├── settings.py       # Configuración (MySQL, apps, media)
    ├── urls.py           # URLs principales
    ├── asgi.py
    └── wsgi.py
```

---

## 🛠️ Dependencias Instaladas

- Django 5.2.8
- pandas (para leer Excel)
- openpyxl (para archivos .xlsx)
- mysqlclient (driver de MySQL para Django)
- PyMySQL (alternativa para MySQL)

---

## 📝 Notas Importantes

1. **Seguridad**: Cambia el `SECRET_KEY` en `settings.py` para producción
2. **Debug**: Desactiva `DEBUG = False` en producción
3. **Archivos Media**: Los archivos Excel se guardan en `media/uploads/`
4. **Encoding**: La base de datos usa `utf8mb4` para soportar caracteres chinos
5. **Zona Horaria**: Configurada para `America/Mexico_City`

---

## 🐛 Solución de Problemas

### Error: "Access denied for user 'root'@'localhost'"
- Verifica que la contraseña en `settings.py` sea correcta
- Asegúrate de que MySQL esté corriendo

### Error: "No module named 'MySQLdb'"
- Ejecuta: `pip install mysqlclient`

### Error al cargar Excel
- Verifica que el archivo tenga las 20 columnas esperadas
- Revisa que el archivo no esté corrupto
- Comprueba que el tamaño sea menor a 10MB

---

## 👤 Contacto y Soporte

Para cualquier problema o pregunta, contacta al administrador del sistema.
