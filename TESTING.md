# 🧪 Guía de Pruebas del Sistema

## Verificar que todo funciona correctamente

### 1. Verificar la Instalación

```powershell
# Activar entorno virtual
C:/Users/alberto/Documents/GitHub/INM-Viajes/env/Scripts/Activate.ps1

# Ir a la carpeta del proyecto
cd C:\Users\alberto\Documents\GitHub\INM-Viajes\Viajes

# Verificar que Django está instalado
python -c "import django; print(f'Django {django.get_version()}')"

# Verificar pandas
python -c "import pandas; print(f'Pandas {pandas.__version__}')"

# Verificar MySQL
python -c "import MySQLdb; print('MySQL conectado exitosamente')"
```

### 2. Verificar las Migraciones

```powershell
# Ver el estado de las migraciones
python manage.py showmigrations

# Deberías ver:
# uploader
#  [X] 0001_initial
```

### 3. Verificar la Conexión a MySQL

```powershell
python manage.py dbshell
# Si se conecta, escribe: exit
```

### 4. Probar la Carga del Excel de Ejemplo

1. Inicia el servidor:
   ```powershell
   python manage.py runserver
   ```

2. Accede a http://127.0.0.1:8000/admin/
   - Login con tu superusuario

3. Ve a http://127.0.0.1:8000/
   - Sube el archivo `context/PrimerEjemplo.xlsx`
   - Deberías ver: "Archivo cargado exitosamente. 4 registros creados."

4. Ve a http://127.0.0.1:8000/admin-list/
   - Deberías ver 4 registros de pasajeros

### 5. Probar Funcionalidades de Superusuario

En http://127.0.0.1:8000/admin-list/:

1. **Marcar como Confirmado**:
   - Click en el checkbox ⬜ (debería cambiar a ✅)
   - Recarga la página, el estado debe persistir

2. **Marcar como Inadmitido**:
   - Click en el checkbox ⬜ (debería cambiar a ❌)
   - Recarga la página, el estado debe persistir

3. **Agregar Comentario**:
   - Click en "✏️ Editar"
   - Escribe un comentario
   - Click en "Guardar"
   - El comentario debe aparecer en la tabla

4. **Filtros**:
   - Usa el filtro "Confirmado: Sí"
   - Solo deben aparecer los registros marcados como confirmados
   - Prueba con "Inadmitido" y "Lote de Carga"

5. **Paginación**:
   - Si tienes más de 50 registros, verás botones de paginación
   - Prueba navegar entre páginas

### 6. Verificar Django Admin

En http://127.0.0.1:8000/admin/:

1. Click en "Lotes de Carga"
   - Deberías ver tu lote cargado
   - Verifica que muestra el usuario y fecha correctos

2. Click en "Registros de Pasajeros"
   - Deberías ver todos los registros
   - Prueba buscar por nombre o número de documento
   - Prueba filtrar por confirmado/inadmitido

3. Click en un registro
   - Verifica que todos los campos se muestran correctamente
   - Modifica el comentario
   - Guarda y verifica el cambio

### 7. Pruebas de Seguridad

1. **Usuario Normal vs Superusuario**:
   - Crea un usuario normal (no superusuario) en el admin
   - Cierra sesión y entra con ese usuario
   - Ve a /admin-list/
   - NO deberías ver las columnas de Confirmado, Inadmitido, Comentario, ni Acciones
   - Deberías poder ver la lista pero no modificar

2. **Validación de Archivos**:
   - Intenta subir un archivo .txt (debe rechazarse)
   - Intenta subir un archivo muy grande >10MB (debe rechazarse)

### 8. Verificar Datos en MySQL

```sql
-- Conecta a MySQL Workbench y ejecuta:
USE viajes_db;

-- Ver todas las tablas
SHOW TABLES;

-- Deberías ver:
-- auth_user, uploader_uploadbatch, uploader_registro, etc.

-- Ver los lotes de carga
SELECT * FROM uploader_uploadbatch;

-- Ver los registros
SELECT id, nombre_pasajero, vuelo_numero, confirmado, inadmitido 
FROM uploader_registro;

-- Contar registros
SELECT COUNT(*) as total FROM uploader_registro;
```

---

## 🎯 Lista de Verificación Completa

- [ ] Django instalado correctamente
- [ ] Pandas instalado correctamente
- [ ] MySQL conectado correctamente
- [ ] Migraciones aplicadas
- [ ] Superusuario creado
- [ ] Servidor inicia sin errores
- [ ] Puedo hacer login
- [ ] Puedo subir el Excel de ejemplo
- [ ] Los 4 registros se crean correctamente
- [ ] Puedo ver la lista de registros
- [ ] Puedo marcar como confirmado
- [ ] Puedo marcar como inadmitido
- [ ] Puedo agregar comentarios
- [ ] Los filtros funcionan
- [ ] El Django Admin funciona
- [ ] Las validaciones de archivo funcionan
- [ ] Los permisos de superusuario funcionan

---

## 🐛 Problemas Comunes y Soluciones

### El servidor no inicia
```
Error: "Address already in use"
Solución: Otro proceso está usando el puerto 8000
Usa: python manage.py runserver 8080
```

### No puedo subir archivos
```
Error: "PermissionError"
Solución: Verifica permisos de la carpeta media/
```

### Los registros no se crean
```
Error: "KeyError" al procesar Excel
Solución: Verifica que el Excel tenga exactamente las 20 columnas esperadas
```

### No veo los campos administrativos
```
Problema: Solo veo la lista básica
Solución: Verifica que tu usuario sea superusuario (is_superuser=True)
```

---

## ✅ Si Todo Funciona...

¡Felicidades! El sistema está completamente funcional y listo para usar.

Ahora puedes:
- Subir archivos Excel reales
- Gestionar registros de pasajeros
- Usar el sistema en tu flujo de trabajo

Para producción, recuerda:
- Cambiar `SECRET_KEY` en settings.py
- Configurar `DEBUG = False`
- Configurar un servidor web (nginx, Apache)
- Usar un servidor de aplicación (gunicorn, uwsgi)
- Configurar backups de la base de datos
