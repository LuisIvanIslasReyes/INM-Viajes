# Empleados y Oficios en INM-Viajes — handoff para iterar

> Documento vivo para retomar el feature en la siguiente sesión.
> Última actualización: 24/11/2026.

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
| Datos que viajan | Número, título, nombres, apellidos, sexo, plaza, descripción de la plaza, jerarquía, municipio y estado | Lo que imprime un oficio. Sin CURP, RFC, teléfono, foto ni fecha de nacimiento. |
| Cargo impreso | La **plaza**, en femenino si firma una mujer; sin plaza, la jerarquía | Mismo criterio que la Estancia desde D-144 (`36e5b97`). |
| Frecuencia | Incremental cada 15 min y completa cada noche | La incremental no ve los borrados físicos; la completa sí. |
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

### Estancia (ProyectoEstancia, rama `Back-dev`, commits `2594c7b` y `36e5b97`)

- **Endpoint** `GET /api/v1/personal/integracion/empleados/` en `backend/apps/Personal/integracion.py`.
  - Auth: `ApiKeyIntegracionAuthentication` revisa `X-API-Key` contra `settings.INTEGRACION_API_KEYS`. Sin llaves configuradas, el endpoint queda cerrado. Un JWT de usuario no sirve.
  - Filtros: `municipio=<id>`, `q=<texto>` (por palabras), `incluir_bajas=1`. Paginado de 500 por página, con tope de 2000.
  - `jerarquia` = jerarquía **principal vigente** del empleado.
  - Desde `36e5b97` (D-144): `plaza` es el puesto genérico y `plaza_descripcion` la plaza concreta. Además:
    - **Incremental:** con `modificado_desde=<ISO>`, devuelve solo lo que cambió (bajas incluidas). Pagina por cursor: el `next` trae `modificado_desde` + `despues_de_id`.
    - **`actualizado`:** la fecha efectiva de la fila; también cambia si se mueve la plaza, la jerarquía o el municipio.
    - **`proximo_desde`:** sale en los dos modos y es el punto de partida de la siguiente incremental.
- **Setting** `INTEGRACION_API_KEYS = env.dict(...)`, con formato `viajes=<clave>,otra=<clave>`.
- **Tests:** `apps.Personal.tests.test_integracion_empleados` (15).

### Viajes (INM-Viajes, `main`, commit `4f8d0e7`)

- **App** `Viajes/apps/empleados/`:
  - `models.Empleado`: réplica con `id_estancia` único, más `activo` y `firmante_habitual`, que son lo único propio de Viajes.
    - Campos `plaza`, `plaza_descripcion` y `jerarquia`. La migración 0002 renombró la vieja columna `cargo` a `jerarquia`.
    - Propiedades `nombre_completo`, `titulo_abreviado` y `nombre_para_oficio` (ej. `LIC. MELISSA GALLEGOS`), más `es_mujer` y `cargo`.
    - **`cargo`** es la plaza, en femenino si firma una mujer (ej. `JEFA DE DEPARTAMENTO`); sin plaza, la jerarquía. `plaza_en_femenino()` es una copia de `apps/Personal/plazas.py` de la Estancia: si allá cambia, hay que copiarla aquí.
  - `models.SincronizacionEmpleados`: bitácora de cada intento (origen, **modo**, usuario, contadores, error y **`proximo_desde`**).
  - `services.py`: `descargar_empleados(modificado_desde=None)` usa `urllib`, sin dependencias nuevas, y devuelve `Descarga(filas, proximo_desde)`.
    - En la incremental se toma el cursor del `next`, pero se aplica sobre la URL propia, por si nginx reescribe el host.
    - Se guarda el `proximo_desde` **menor** de todas las páginas.
    - `aplicar_empleados()` hace el upsert en bloque y desactiva a los ausentes, pero solo en la completa.
    - `sincronizar(completa=False)` es incremental si la última sincronización exitosa dejó un `proximo_desde`; si no, es completa. Deja registro siempre.
    - Si la descarga falla, la réplica no se toca.
    - Si la completa devuelve 0 empleados y aquí hay activos, se aborta. Una incremental vacía es normal.
    - Si la Estancia no manda `proximo_desde` (versión anterior a D-144), la siguiente sincronización vuelve a ser completa.
  - Comando `python manage.py sincronizar_empleados [--completa]`: sale con código 1 si falla.
  - Vistas en `/empleados/`:
    - `listado`: todos los roles; búsqueda, municipio e inactivos.
    - `buscar/`: JSON para autocompletar, con firmantes habituales primero. Tope de 20.
    - `sincronizar/`: POST, solo SuperUser y Aeropuerto. Siempre hace una completa.
    - `<pk>/firmante/`: POST para alternar la marca de firmante habitual.
  - Admin de solo consulta. Link "Empleados" en el menú lateral (`uploader/base_ds.html`).
- **Settings** en `settings/base.py`: `ESTANCIA_EMPLEADOS_URL`, `ESTANCIA_API_KEY`, `ESTANCIA_API_TIMEOUT`, `ESTANCIA_API_VERIFICAR_SSL`.
- **`settings/test.py`**: SQLite en memoria para correr tests sin MySQL ni `.env`.
- **`.bat`:**
  - `sincronizar_empleados.bat [--completa]` corre la sincronización y escribe en `logs\sincronizar_empleados.log`.
  - `programar_sincronizacion_empleados.bat` crea dos tareas de Windows, las dos como SYSTEM:
    - `INMViajes\SincronizarEmpleados`: cada 15 minutos, incremental.
    - `INMViajes\SincronizarEmpleadosCompleta`: diario a las 03:00, completa.
- **README:** tiene la sección "Catálogo de empleados".
- **Tests:** `apps.empleados` (44). Los 90 de Viajes pasan (24/11, en Linux con SQLite).

### Prueba de punta a punta (local, 20/11)

La Estancia local en el puerto 8000 y Viajes con SQLite, conectados por HTTP real:

- Llegaron **341** empleados en 0.3 s: **280 activos** y **61 de baja**.
- La segunda corrida no cambió nada.
- Sin llave → 401. Llave equivocada → 401.

### ⏳ Falta para cerrar la fase 1 (despliegue)

- [ ] **Estancia (producción):** desplegar también `36e5b97` (D-144), con sus migraciones Personal 0020-0022. Sin ese commit, Viajes funciona, pero solo hace completas y `plaza_descripcion` queda vacía.
- [ ] Generar la llave: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- [ ] **Estancia (producción):** agregar `INTEGRACION_API_KEYS=viajes=<llave>` al `.env`, revisar que `DJANGO_ALLOWED_HOSTS` acepte el host con el que llama Viajes, y desplegar `Back-dev`.
- [ ] **Viajes (.12):** agregar `ESTANCIA_EMPLEADOS_URL` (URL completa, con IP 10.100.152.x y el prefijo de nginx) y `ESTANCIA_API_KEY` en el `.env` de la raíz.
- [ ] **Viajes (.12):** correr `actualizar_produccion.bat` y elegir **M** (migrate) para crear las tablas `empleados_*`. Son las migraciones 0001 y 0002.
- [ ] **Viajes (.12):** probar `sincronizar_empleados.bat` y revisar el log.
- [ ] **Viajes (.12):** correr `programar_sincronizacion_empleados.bat` como Administrador. Crea las 2 tareas.
- [ ] Probar de punta a punta contra la Estancia con D-144: primero una completa, luego una incremental. Esta vez no se probó con HTTP real, solo con tests.
- [ ] Revisar la pantalla **Empleados** en el navegador. No se revisó visualmente: solo se probó con tests.
- [ ] Marcar a los firmantes habituales (Carrillo, Melissa, Merenteria, Tello, Víctor…).

### Observaciones a revisar

- **61 bajas** en la BD local, cuando se esperaban de 1 a 5. Confirmar en producción; puede ser que la copia local esté vieja.
- ~~**El cargo impreso no coincide con los datos.**~~ **Resuelto (24/11)** con D-144 en la Estancia: el cargo sale de la plaza, en femenino según quien firme, y Viajes ya usa el mismo criterio. Falta confirmar en producción que las plazas de los firmantes habituales traigan el puesto correcto. La migración 0021 de la Estancia separa el texto por prefijos, así que conviene revisar su tabla antes→después.
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
4. ~~¿De dónde sale el **cargo** que se imprime?~~ **Resuelto:** de la plaza (D-144). Ver las observaciones de la fase 1.
5. ¿En qué **orden** van los oficios en el paquete? (Confirmar con los PDF de ejemplo.)
6. ¿El idioma se define por expediente o puede variar por persona dentro de la misma familia?
7. ¿Qué datos de los extranjeros salen de los registros que ya existen (vuelo, pasajero, documento) y cuáles se capturan a mano?

### Orden sugerido para la siguiente sesión

1. Cerrar el despliegue de la fase 1 (checklist de arriba).
2. Resolver las preguntas 1 y 2.
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

Viajes no tiene un `env` propio en el repo. Para correr sus tests hay que crear uno e instalar `requirements.txt` sin `mysqlclient` ni `PyMySQL`. En Linux con Python 3.14, `pandas` se instala desde wheel.
