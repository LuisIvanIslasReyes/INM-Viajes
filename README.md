# Sistema de Gestión de Viajes - INM

## Configuración de la Base de Datos MySQL

### 1. Crear la Base de Datos en MySQL Workbench

Abre MySQL Workbench y ejecuta los siguientes comandos SQL:

```sql
-- Crear la base de datos
CREATE DATABASE viajes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Aplicar las Migraciones

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

### 4. Ejecutar el Servidor (desarrollo)

```powershell
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000/`

---

## Producción: servicio de Windows (NSSM)

En el servidor, Django corre como el servicio de Windows **INMViajes** ("INM Viajes (Django)"),
registrado con [NSSM](https://nssm.cc/). Escucha en el puerto `8002` con `Viajes.settings.production`.
Arranca solo después de un reinicio o un apagón (inicio automático retrasado y dependencia de `MySQL80`)
y NSSM lo vuelve a levantar si el proceso se cae.

Los scripts están en la carpeta `Viajes` y **se ejecutan como Administrador**. La ruta de `nssm.exe`
está definida al inicio de cada uno (`C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe`).

| Script | Para qué |
|---|---|
| `instalar_servicio.bat` | Crea (o reinstala) el servicio y lo arranca. Solo se usa una vez, o si cambia la ruta del proyecto/entorno. |
| `actualizar_produccion.bat` | Despliegue manual: detiene el servicio, levanta la página de mantenimiento y muestra el menú (migrate / collectstatic / ambos / solo levantar). |
| `desinstalar_servicio.bat` | Detiene y elimina el servicio. |

### Actualizar producción

1. Ejecuta `actualizar_produccion.bat` como Administrador. Los usuarios verán la página de mantenimiento.
2. Copia el código nuevo (y, si cambió `requirements.txt`, instala los paquetes en el `env`).
3. Elige en el menú: **M** migraciones, **S** collectstatic, **A** ambos, **R** solo levantar, **X** salir dejando el mantenimiento.
   Si `migrate` o `collectstatic` fallan, el servicio no se levanta y se regresa al menú.

### Comandos útiles

```powershell
C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe status INMViajes
C:\Users\usuariobc\Documents\nssm-2.24\win64\nssm.exe restart INMViajes
```

Log del servicio: `Viajes\logs\servicio.log` (rota a los 10 MB).

> No corras `python manage.py runserver 0.0.0.0:8002` a mano en el servidor: chocaría con el servicio en el puerto 8002.

---

## Catálogo de empleados (réplica de la Estancia)

El módulo **Empleados** (`apps/empleados`, menú lateral → Empleados) tiene una copia local de los
empleados de la Estancia (ProyectoEstancia → Personal). La Estancia es la fuente de verdad: las altas,
correcciones y bajas se hacen allá en Recursos Humanos. Viajes solo copia, para seguir teniendo el
catálogo aunque la Estancia se apague. Lo único propio de Viajes es la marca de **firmante habitual**
(se muestra primero en el buscador) y el **fundamento asignado a mano** (ver abajo).

- Nunca se borran empleados: los dados de baja (o que dejan de venir) quedan **inactivos**.
- Si la Estancia no responde, se sigue usando la última copia y la pantalla avisa del intento fallido.
- `GET /empleados/buscar/?q=&municipio=` devuelve JSON para autocompletar firmante y testigos.
- **Cargo impreso** (`Empleado.cargo`): el mismo criterio que usa la Estancia en sus oficios desde D-144.
  Sale de la **plaza** (por ejemplo, "JEFE DE DEPARTAMENTO") y se pone en femenino si firma una mujer
  ("JEFA DE DEPARTAMENTO"). Si el empleado no tiene plaza, se usa la jerarquía. La descripción de la
  plaza ("JEFATURA DE DEPARTAMENTO DE …") se guarda aparte, en `plaza_descripcion`.
- **Fundamento impreso** (`Empleado.fundamento`): el artículo del Acuerdo que se cita según la plaza de
  quien firma (por ejemplo, Representante Local → "Artículo 14, apartado B, fracciones I, II y III").
  - El catálogo de los 6 fundamentos está en el admin, en **Fundamentos por plaza**. Solo el
    SuperUser lo edita.
  - Se asigna solo por la plaza. El Subdirector de Control y Verificación se distingue por la
    descripción de la plaza.
  - Cuando la plaza no lo determina, SuperUser o Aeropuerto lo asignan a mano en la pantalla
    Empleados ("Cambiar"). La sincronización no lo toca.
  - La pantalla marca **Sin fundamento** a los firmantes habituales que no tienen uno.

### Configuración (`.env` de la raíz)

```ini
ESTANCIA_EMPLEADOS_URL=http://<ip-estancia>/<ruta>/api/v1/personal/integracion/empleados/
ESTANCIA_API_KEY=<la misma clave que la Estancia tiene en INTEGRACION_API_KEYS como viajes=...>
# Opcionales
ESTANCIA_API_TIMEOUT=15
ESTANCIA_API_VERIFICAR_SSL=True
```

En el `.env` de la Estancia va la contraparte: `INTEGRACION_API_KEYS=viajes=<clave>`. Generar la clave con
`python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### Sincronización automática

1. Prueba a mano: `sincronizar_empleados.bat` (resultado en `Viajes\logs\sincronizar_empleados.log`).
2. Como Administrador, ejecuta `programar_sincronizacion_empleados.bat`. Crea dos tareas de Windows,
   las dos como SYSTEM:
   - `INMViajes\SincronizarEmpleados`: cada 15 minutos, **incremental**. Solo trae lo que cambió desde
     la última sincronización exitosa.
   - `INMViajes\SincronizarEmpleadosCompleta`: diario a las 03:00, **completa** (`--completa`). Trae todo
     el catálogo y marca como inactivos a los que ya no vengan; por ejemplo, a los que se borraron en la
     Estancia, que la incremental no ve.

La incremental parte del `proximo_desde` que devolvió la Estancia la vez anterior. Si no hay uno (la primera
vez, o si la Estancia todavía no lo manda), se hace una completa. El botón **Sincronizar ahora** de la
pantalla (SuperUser y Aeropuerto) también hace una completa.

### Tests sin MySQL

```powershell
python manage.py test apps.empleados --settings=Viajes.settings.test
```

---

## Oficios (expedientes de familia)

El módulo **Oficios** (`apps/oficios`, menú lateral → Principal → Oficios) arma los oficios 02–14 de cada
extranjero. Solo lo usan SuperUser y Aeropuerto. El detalle del diseño está en `Docs/EMPLEADOS_Y_OFICIOS.md`.

1. **Nuevo expediente:**
   - Se buscan los pasajeros en los vuelos cargados (por defecto, solo los marcados SR o R).
   - Se eligen los de la familia.
   - Sus datos se precargan, con la nacionalidad sacada del código del país emisor, y se pueden corregir.
   - También se puede capturar a una persona a mano.
2. **Firmante y 2 testigos:** se eligen de la pantalla Empleados, una vez por expediente. Si en un oficio
   cambian los testigos, se ajusta en ese oficio. El fundamento del firmante sale de su plaza.
3. **Borradores por persona** (o para toda la familia de una vez, con los formatos sugeridos según el
   resultado): cada oficio copia el texto de su plantilla y se edita en la app.
   - En el texto hay `{{variables}}` y guiones automáticos: `[[ HACE CONSTAR ]]` y un ` --` al final del renglón.
   - Lo que vaya entre `[[ RECUADRO ]]` y `[[ /RECUADRO ]]` sale dentro de un recuadro con borde; entre
     `[[ TABLA ]]` y `[[ /TABLA ]]`, una fila con borde por renglón.
   - `[[ RENGLÓN ]]` y ` __` dejan líneas para escribir a mano.
   - En una `[[ TABLA ]]`, ` || ` separa las columnas de una fila.
   - `[[ FIRMA: leyenda ]]` dibuja una línea de firma (`[[ FIRMA: A || B ]]`, dos lado a lado) y
     `[[ NUEVA HOJA ]]` empieza otra hoja con el encabezado.
   - `[[ EVIDENCIAS ]]` es donde salen las evidencias de la persona (ver abajo).
   - Lo que va entre `«…»` hay que llenarlo en la app: no deja marcar el oficio como impreso mientras quede alguno.
   - El membrete, el encabezado, el título, la fecha y las firmas los pone el sistema.
4. **Word y PDF:** el PDF es el mismo Word convertido con LibreOffice (`SOFFICE_BIN`).
5. **Marcar como impreso:** congela el oficio tal como se imprimió (variables y `.docx`). Para corregirlo hay
   que reabrirlo con un motivo, y queda en el historial.
6. **Paquete para imprimir:** se eligen varios oficios del expediente y salen en un solo Word o PDF, por
   persona y del 02 al 14. Desde ahí también se marcan como impresos.

Están las plantillas **02, 03, 04, 04.1, 05, 07, 08, 09, 11, 12, 13 y 14**, cada una con el tamaño de letra de
su Word oficial. Las respuestas del 04 y el 04.1 se escriben a mano.

**Evidencias (09 y 05):** en el detalle, dentro de cada persona, se capturan de 1 a N evidencias. En el 09
cada una lleva a quién se verificó, la hora, si hubo respuesta, los intentos, observaciones y foto; en el 05,
observaciones y foto.
- La foto se sube desde la computadora o el celular (abre la cámara), o se toma de la app Cámara.
- Cada evidencia sale en su propio recuadro; sin foto, el recuadro sale en blanco para llenarlo a mano.
- Al marcar el oficio como impreso, sus evidencias quedan congeladas hasta reabrirlo.
- Las fotos se guardan en `media/oficios/evidencias/`.

**Traducciones:** en Oficios → Plantillas, cada formato puede tener una traducción por idioma.
- Se captura una vez y la usan todos los oficios futuros de personas con ese idioma; si no hay, sale en español.
- Lleva título bilingüe, texto bilingüe (la traducción va en letra chica) y leyenda de firma.
- Ya vienen el 02 y el 03 en chino, ruso y francés; el 04 en chino y francés; el 04.1 en chino; y la leyenda
  del 07, 08 y 09 en chino y ruso.
- El chino usa Microsoft YaHei y el árabe Arial, que vienen con Windows. El texto base se corrige en **Oficios → Plantillas**.

En el admin, solo el SuperUser puede editar:
- los datos de la oficina;
- la hoja membretada: si no hay ninguna, se usa la de 2026 incluida en `apps/oficios/assets/`;
- los motivos de rechazo.

### Despliegue en el servidor (.12, sin internet)

1. Instalar las dependencias nuevas desde `vendor/python-docx-wheels.zip` (python-docx, lxml y
   typing_extensions para Windows y Python 3.11):

   ```powershell
   # desde la raíz del proyecto, después de descomprimir el zip (queda la carpeta wheels\)
   env\Scripts\pip install --no-index --find-links wheels python-docx==1.1.2 lxml==6.1.3
   ```

2. Instalar en Windows las fuentes **Noto Sans** (Regular, Bold, Italic y BoldItalic) para que LibreOffice
   genere el PDF con la misma letra. Los `.ttf` están en `ProyectoEstancia/backend/apps/Oficios/assets/fonts`.
3. `actualizar_produccion.bat` → **M** (migrate, `oficios` 0001 a 0012): crea las tablas `oficios_*` y
   siembra la oficina, los motivos de rechazo, las plantillas y sus traducciones.

### Tests

```powershell
python manage.py test apps.oficios --settings=Viajes.settings.test
```

Si LibreOffice no está instalado, la prueba de conversión real a PDF se salta.

---

## Uso del Sistema

### Para Usuarios Normales:
1. Iniciar sesión en `http://127.0.0.1:8000/` con tus credenciales de prueba.
    Usuario: PruebaRandom
    Contraseña: Azdsfkh-ko/1.cvghydfvvnmgq
2. Ir a `http://127.0.0.1:8000/upload` para subir archivos Excel
3. Seleccionar un archivo Excel (.xlsx) con la estructura correcta
4. Hacer clic en "Cargar Archivo"
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
✅ **Drag & Drop Upload**: Interfaz moderna para arrastrar archivos
✅ **Detección de Duplicados Inteligente**: 3 niveles de validación
✅ **🔔 Módulo de Casos Especiales**: Gestión de documentos duplicados con revisión manual (Ver [CASOS_ESPECIALES.md](CASOS_ESPECIALES.md))
✅ **Búsqueda por Rango de Fechas**: Vista especializada con agrupación por día
✅ **Descarga de Archivos**: Botón de descarga segura para archivos Excel
✅ **Verificación de Duplicados**: Herramienta de análisis de documentos duplicados
✅ **Interfaz Amigable**: Templates con DaisyUI + Tailwind CSS
✅ **Permisos**: Sistema flexible de permisos para usuarios
✅ **Filtros Avanzados**: Por lote, confirmado, inadmitido, fecha, búsqueda de texto
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
6. **🔔 Casos Especiales**: Revisa diariamente los casos pendientes de documentos duplicados (Ver [Guía Rápida](CASOS_ESPECIALES_GUIA_RAPIDA.md))
7. **Validación de Duplicados**: El sistema permite la misma persona en diferentes vuelos/fechas (multi-travel)
8. **Fechas Mínimas**: Las búsquedas por fecha tienen restricción desde 10/11/2025

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
