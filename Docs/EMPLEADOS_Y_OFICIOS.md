# Empleados y Oficios en INM-Viajes — handoff para iterar

> Documento vivo para retomar el feature en la siguiente sesión.
> Última actualización: 23/11/2026.

## Objetivo del feature

En INM-Viajes, buscar empleados y asignarlos a los **oficios** de un expediente de familia: un **firmante** para todo el expediente y **N testigos**. Al final, imprimir un **paquete** con los oficios seleccionados de una sola vez.

Hay dos piezas:

1. **Catálogo de empleados**, siempre actualizado y disponible aunque la Estancia se caiga. → **Hecho (fase 1).**
2. **Motor de oficios** propio de Viajes, construido con la base técnica de la Estancia pero **sin compartirse por API**. → **Pendiente (fase 2).**

---

## Decisiones tomadas

| Tema | Decisión | Por qué |
|---|---|---|
| Fuente de verdad de empleados | `Personal` de la **Estancia** (ProyectoEstancia), no INM_Horarios | La Estancia ya tiene el catálogo y RRHH lo mantiene ahí. Horarios se migrará a la Estancia. |
| Cómo llegan a Viajes | **Réplica local** de solo lectura, sincronizada por *pull* desde Viajes | Si la Estancia se apaga, Viajes sigue con su catálogo. La Estancia no necesita saber que Viajes existe. |
| Llave de cruce | `id_empleado` de la Estancia (`id_estancia` en Viajes) | `employee_number` es opcional allá: 14 empleados no lo tienen. |
| Bajas | Nunca se borran; quedan `activo=False` | Hay oficios ya generados que los mencionan. |
| Datos que viajan | Número, título, nombres, apellidos, sexo, plaza, jerarquía, municipio y estado | Lo que imprime un oficio. Sin CURP, RFC, teléfono, foto ni fecha de nacimiento. |
| Seguridad | API key por app en el header `X-API-Key`, de servidor a servidor | El navegador nunca habla con la Estancia, así que no hace falta CORS. |
| Oficios | **No** se comparten por API; Viajes tiene su propio motor y copia el *patrón* de la Estancia | Son de otro tema (rechazo aéreo vs. presentados) y son documentos legales: cada app debe ser dueña de los suyos. |
| Vacaciones / incapacidad | No importan | El oficio es físico y se firma en el momento. |
| Filtros | Todos los empleados, con filtro opcional por municipio | Pedido explícito. |
| Firmante | Uno por expediente de familia | Firma todos los oficios del expediente. |
| Testigos | Se heredan del expediente, **pero se pueden cambiar por oficio** | "No vaya a ser". |
| Paquete | Selector múltiple de N oficios → un solo archivo, en **Word y PDF** | Imprimir todo de una vez. Se parece a los oficios básicos y al PAM de la Estancia. |
| Idiomas | Plantilla oficial en español, más variantes traducidas (texto en español y su traducción lado a lado) | Chino como principal; ruso y francés; tener en cuenta inglés y árabe. Portugués, no. |
| Formato 01 | **Fuera de alcance** | Sale de la intranet de CDMX. |
| Formatos 06 y 10 | **Fuera de la primera versión** | Casi no se usan. Más adelante pueden entrar como texto libre sin lógica. |

---

## Fase 1 — Catálogo de empleados ✅

### Estancia (ProyectoEstancia, rama `Back-dev`, commit `2594c7b`)

- **Endpoint** `GET /api/v1/personal/integracion/empleados/` en `backend/apps/Personal/integracion.py`.
  - Auth: `ApiKeyIntegracionAuthentication` revisa `X-API-Key` contra `settings.INTEGRACION_API_KEYS`. Sin llaves configuradas, el endpoint queda cerrado. Un JWT de usuario no sirve.
  - Filtros: `municipio=<id>`, `q=<texto>` (por palabras), `incluir_bajas=1`. Paginado de 500 por página, con tope de 2000.
  - `jerarquia` = jerarquía **principal vigente** del empleado.
- **Setting** `INTEGRACION_API_KEYS = env.dict(...)`, con formato `viajes=<clave>,otra=<clave>`.
- **Tests:** `apps.Personal.tests.test_integracion_empleados` (15).

### Viajes (INM-Viajes, `main`, commit `4f8d0e7`)

- **App** `Viajes/apps/empleados/`:
  - `models.Empleado`: réplica con `id_estancia` único, más `activo` y `firmante_habitual`, que son lo único propio de Viajes. Propiedades `nombre_completo`, `titulo_abreviado` y `nombre_para_oficio` (ej. `LIC. MELISSA GALLEGOS`).
  - `models.SincronizacionEmpleados`: bitácora de cada intento (origen, usuario, contadores, error).
  - `services.py`: `descargar_empleados()` usa `urllib`, sin dependencias nuevas, y pagina por su cuenta. `aplicar_empleados()` hace el upsert en bloque y desactiva a los ausentes. `sincronizar()` deja registro siempre.
    - Si la descarga falla, la réplica no se toca.
    - Si la Estancia devuelve 0 empleados y aquí hay activos, se aborta.
  - Comando `python manage.py sincronizar_empleados`: sale con código 1 si falla.
  - Vistas en `/empleados/`:
    - `listado`: todos los roles; búsqueda, municipio e inactivos.
    - `buscar/`: JSON para autocompletar, con firmantes habituales primero. Tope de 20.
    - `sincronizar/`: POST, solo SuperUser y Aeropuerto.
    - `<pk>/firmante/`: POST para alternar la marca de firmante habitual.
  - Admin de solo consulta. Link "Empleados" en el menú lateral (`uploader/base_ds.html`).
- **Settings** en `settings/base.py`: `ESTANCIA_EMPLEADOS_URL`, `ESTANCIA_API_KEY`, `ESTANCIA_API_TIMEOUT`, `ESTANCIA_API_VERIFICAR_SSL`.
- **`settings/test.py`**: SQLite en memoria para correr tests sin MySQL ni `.env`.
- **`.bat`:**
  - `sincronizar_empleados.bat` corre la sincronización y escribe en `logs\sincronizar_empleados.log`.
  - `programar_sincronizacion_empleados.bat` crea la tarea de Windows `INMViajes\SincronizarEmpleados` cada 15 minutos como SYSTEM.
- **README:** tiene la sección "Catálogo de empleados".
- **Tests:** `apps.empleados` (29). Los 75 de Viajes pasan.

### Prueba de punta a punta (local, 20/11)

La Estancia local en el puerto 8000 y Viajes con SQLite, conectados por HTTP real:

- Llegaron **341** empleados en 0.3 s: **280 activos** y **61 de baja**.
- La segunda corrida no cambió nada.
- Sin llave → 401. Llave equivocada → 401.

### ⏳ Falta para cerrar la fase 1 (despliegue)

- [ ] Generar la llave: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- [ ] **Estancia (producción):** agregar `INTEGRACION_API_KEYS=viajes=<llave>` al `.env`, revisar que `DJANGO_ALLOWED_HOSTS` acepte el host con el que llama Viajes, y desplegar `Back-dev`.
- [ ] **Viajes (.12):** agregar `ESTANCIA_EMPLEADOS_URL` (URL completa, con IP 10.100.152.x y el prefijo de nginx) y `ESTANCIA_API_KEY` en el `.env` de la raíz.
- [ ] **Viajes (.12):** correr `actualizar_produccion.bat` y elegir **M** (migrate) para crear las tablas `empleados_*`.
- [ ] **Viajes (.12):** probar `sincronizar_empleados.bat` y revisar el log.
- [ ] **Viajes (.12):** correr `programar_sincronizacion_empleados.bat` como Administrador.
- [ ] Revisar la pantalla **Empleados** en el navegador. No se revisó visualmente: solo se probó con tests.
- [ ] Marcar a los firmantes habituales (Carrillo, Melissa, Merenteria, Tello, Víctor…).

### Observaciones a revisar

- **61 bajas** en la BD local, cuando se esperaban de 1 a 5. Confirmar en producción; puede ser que la copia local esté vieja.
- **El cargo impreso no coincide con los datos.** El oficio dice "JEFE(A) DE DEPARTAMENTO", pero en la Estancia la `jerarquia` sale "AFM" en muchos empleados y la `plaza` es "AGENTE FEDERAL DE MIGRACIÓN "C"". Hay que definir de dónde sale el **cargo** que se imprime: ¿la jerarquía, un campo propio o captura por expediente?
- **14 empleados sin número de empleado** en la Estancia.
- Se agregó una llave **solo de desarrollo** al `backend/.env` local de la Estancia. Git lo ignora y no sirve en producción.

---

## Fase 2 — Oficios en Viajes (pendiente)

### Inventario de formatos (USB `E:\`)

Son 14 formatos distintos. Los demás archivos de la USB son copias ya llenadas por idioma y por oficial, y sirven para detectar qué partes son variables y cuáles son texto fijo. **Traen datos reales de extranjeros: no subirlos al repo.**

| # | Formato | ¿Traducción real? | Alcance |
|---|---|---|---|
| 02 | Constancia de uso de traductor electrónico | **Sí** (145 caracteres en chino, 535 en ruso) | ❓ |
| 03 | Canalización / notificación de segunda revisión | **Sí** (71 en chino, 255 en ruso) | ❓ |
| 04 | Cuestionario de segunda revisión | **Mucha** (778 en chino; en francés el texto crece 50 %) | ❓ |
| 04.1 | Cuestionario para residentes | ? | ❓ |
| 05 | Constancia de condición o servicio médico (+ variante "FOTO") | No | ❓ |
| 06 | Constancia de atención SNDIF | — | *fuera de la v1* |
| 07 | Constancia de llamada consular | Casi nada (5 a 11 caracteres) | ❓ |
| 08 | Constancia de llamada personal | Casi nada | ❓ |
| 09 | Constancia de verificación de información (+ "FOTO - VARIOS") | Casi nada | ❓ |
| 10 | Constancia de ampliación de término | — | *fuera de la v1* |
| 11 | Notificación de rechazo aéreo | No | ❓ |
| 12 | Constancia negativa de firma | No | ❓ |
| 13 | Notificación a la empresa: alimentos y ruta | No | ❓ |
| 14 | Acuerdo de ejecución de acta de rechazo | No | ❓ |

- **Alcance ❓:** el usuario dijo que el lunes confirma cuáles van **uno por persona** y cuáles **uno por expediente**. Es lo primero que hay que preguntar.
- **El texto traducido es idéntico entre oficiales.** Es texto fijo de la plantilla, no algo que se escriba por caso. Eso hace viable tener una variante por idioma.
- **Maquetación:** en los Word, el cuerpo traducido es una tabla de 2 columnas (español | idioma).
- **"Formatos reunidos internación"** = paquete de varios oficios en un solo .docx, con 5 secciones.
- **Los PDF `ORBC_AIMMTJ_AI000278_2026_EXP.pdf` (24 págs.) y `…_AR000316_…` (23 págs.)** son escaneos (Xerox) de expedientes finales ya firmados: son el resultado que debe salir del paquete, sin la hoja 01. No se pudieron abrir porque falta poppler en esta máquina. Hay que revisarlos para fijar el **orden** del paquete.

### Diseño propuesto

Hay que tomar como referencia el motor de la Estancia (`ProyectoEstancia/backend/apps/Oficios`):

- **De ahí se copia:** el patrón de `OficioPlantilla` con variables, el generador de .docx (`services/docx_renderer.py`), la concordancia de género, y membrete, encabezado y tipografía con "un solo activo" (`MembreteAsset`, `ConfiguracionTipografia`).
- **Variante por idioma:** mismo patrón que `OficioPlantillaEstancia` (allá es una variante por estancia; aquí, por idioma).
- **Borrador editable con historial:** mismo patrón que `OficioLibreInstancia` y `OficioLibreHistorial`.

Modelo tentativo para Viajes:

```
Expediente (familia)
 ├─ firmante        → empleados.Empleado (+ copia congelada: nombre_para_oficio, cargo, sexo)
 ├─ testigos[]      → empleados.Empleado (+ copia congelada)
 ├─ idioma          (con opción de cambiarlo por persona)
 └─ personas[]      (extranjeros: los datos salen de Registro/pasajeros, ya existe en uploader)

PlantillaOficio (número, nombre, alcance: POR_PERSONA | POR_EXPEDIENTE, contenido + variables)
 └─ PlantillaOficioIdioma (plantilla, idioma, contenido bilingüe de 2 columnas)
    → si no hay variante para el idioma, sale en español

OficioInstancia (expediente, plantilla, persona?, contenido editable, testigos_override?, historial)
 → se congela al imprimir

Paquete: selector múltiple → expande los POR_PERSONA por cada integrante → orden por número
 → un .docx (una sección por oficio) y un PDF
```

### Puntos técnicos a tener en cuenta

- **Las correcciones se hacen dentro de la app**, en el borrador editable. El Word es una exportación opcional. Si corrigen en Word, la app ya no sabe qué se imprimió y lo guardado no coincide con lo firmado.
- **PDF en el servidor .12:** Viajes ya tiene `SOFFICE_BIN` (LibreOffice) configurado para la vista previa de Redacciones. Reusar eso para convertir .docx → PDF.
- **Fuentes:**
  - Noto Sans cubre español, inglés, francés y ruso.
  - El chino necesita **Noto Sans SC**.
  - El árabe necesita **Noto Sans Arabic**.
  - Sin ellas salen cuadritos. Instalarlas en el servidor .12 para LibreOffice.
- **Árabe = de derecha a izquierda (RTL):** en la columna árabe hay que poner la dirección del párrafo en el .docx, y el relleno de guiones va del lado contrario.
- **Guiones medios (`------`) al final de cada párrafo:** el usuario dijo que "ya le dieron una solución". **Hay que preguntar cuál es.** Afecta las tablas bilingües (cada columna necesita su propio guionado) y al árabe. En la Estancia, el guionado distinto por impresora es la razón de que exista `OficioPlantillaEstancia`.
- **Autocompletado de firmante y testigos:** usar `GET /empleados/buscar/?q=&municipio=`, que ya existe y devuelve `nombre_para_oficio`, `cargo` y `sexo`.

### Preguntas abiertas para el usuario

1. ¿Qué oficios van **uno por persona** y cuáles **uno por expediente**? (Quedó en confirmar el lunes.)
2. ¿Cuál es la **solución de los guiones** que le dieron?
3. ¿Quién proporciona y valida las traducciones al **inglés** y al **árabe**? (Las de chino, ruso y francés ya están en los Word.)
4. ¿De dónde sale el **cargo** que se imprime ("JEFE DE DEPARTAMENTO")? Ver las observaciones de la fase 1.
5. ¿En qué **orden** van los oficios en el paquete? (Confirmar con los PDF de ejemplo.)
6. ¿El idioma se define por expediente o puede variar por persona dentro de la misma familia?
7. ¿Qué datos de los extranjeros salen de los registros que ya existen (vuelo, pasajero, documento) y cuáles se capturan a mano?

### Orden sugerido para la siguiente sesión

1. Cerrar el despliegue de la fase 1 (checklist de arriba).
2. Resolver las preguntas 1, 2 y 4.
3. Revisar los 2 PDF de ejemplo para fijar el orden del paquete.
4. Modelos de la fase 2: `Expediente`, `PlantillaOficio`, `PlantillaOficioIdioma`, `OficioInstancia` y sus migraciones.
5. Primer oficio de punta a punta. Se sugiere el **11 (Notificación de rechazo aéreo)**: es corto, sin traducción y por expediente (a confirmar). Debe tener variables, borrador editable, .docx y PDF.
6. Paquete con selector múltiple.
7. Variantes por idioma, empezando por el **04 en chino** (el que tiene más traducción).

---

## Cómo correr los tests

**Estancia** (desde `backend/`, con el venv del proyecto):

```powershell
env/Scripts/python.exe manage.py test apps.Personal.tests.test_integracion_empleados --settings=EstanciaBackend.settings.test --noinput
```

**Viajes** (desde `Viajes/`, sin MySQL):

```powershell
python manage.py test apps.empleados --settings=Viajes.settings.test
```

En esta máquina, Viajes no tiene un `env` propio. Para correr sus tests hay que crear uno e instalar `requirements.txt` sin `mysqlclient` ni `PyMySQL`.
