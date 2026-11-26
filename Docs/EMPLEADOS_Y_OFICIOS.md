# Empleados y Oficios en INM-Viajes — handoff para iterar

> Documento vivo para retomar el feature en la siguiente sesión.
> Última actualización: 25/11/2026 (fase 2: iteraciones 1, 2 y 3 hechas; traducciones al chino, ruso y francés).

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
| Alcance de los oficios | **Todos son uno por persona.** No hay oficios por expediente ni por familia (por ahora). | Respuesta del usuario (24/11). |
| Guiones | **No se calculan.** Se usan **tabuladores con relleno de guiones** de Word (`w:leader="hyphen"`): el separador centrado (`-----HACE CONSTAR-----`) y el relleno al final del párrafo los dibuja Word o LibreOffice solo, según el ancho disponible. | Respuesta del usuario (24/11) y revisión de los PDF. Hoy los Word tienen los guiones escritos a mano, sin tabuladores. |
| Traducciones | La base es **nuestra versión original en español**. La traducción se captura **una sola vez por formato e idioma** (ej. 04 en chino) y queda para **todos los oficios futuros** de ese idioma. La pegan los propios agentes. | No repetir la captura en cada caso. Si no hay traducción, sale solo en español. |
| Datos variables en la traducción | El nombre, el documento, la fecha, etc. van como `{{variables}}` también en el texto traducido. La pantalla de captura avisa si falta una variable del español. | Si no, al siguiente extranjero le saldrían los datos del anterior. |
| Quién edita una traducción | Solo SuperUser y Aeropuerto, con historial. Las correcciones de un solo caso se hacen en el borrador de ese oficio, sin tocar la traducción guardada. | Un cambio a la traducción afecta a todos los oficios futuros. Los ya impresos quedan congelados. Confirmado por el usuario (24/11). |
| Nacionalidad | Se precarga con `Registro.pais_emision` y el usuario la puede corregir a mano. | Confirmado por el usuario (24/11). `Registro` no tiene un campo de nacionalidad. |
| Maquetación de la traducción | La variante por idioma es **una copia completa del formato, bilingüe y entrelazada**, no una tabla de 2 columnas: cada párrafo o etiqueta va en español, luego ` / ` y la traducción. | Así se ve en los PDF firmados (02 y 04 en chino, 02 y 04 en ruso). |
| Orden del paquete | Por número de formato, del 02 al 14. El usuario elige cuáles van; un paquete puede llevar solo unos cuantos. | Respuesta del usuario (24/11). |
| Idioma | **Por persona**: a cada extranjero le toca la variante de su idioma (un chino recibe la de chino). Si no hay variante, sale en español. | Respuesta del usuario (24/11). |
| Datos del extranjero | Nombres, nacionalidad, fecha de nacimiento y número de pasaporte o documento. Se **precargan** de `uploader.Registro`, pero **siempre se pueden editar a mano**. | El Excel puede venir incompleto. |
| Fundamento por plaza | El párrafo del fundamento cita un artículo distinto según la **plaza** del firmante. Hay 6, en un catálogo **propio de Viajes** (`FundamentoPlaza`); ver la tabla de la fase 1. Si la plaza no lo determina, se asigna **a mano** por empleado. Sin fundamento, el oficio no se genera (fase 2). | Decisión del usuario (24/11). No se toca la Estancia ni la API. |
| Motor de oficios | **Texto editable en la app** (patrón de la Estancia): plantilla con `{{variables}}` → borrador por persona → se congela al imprimir. **Un solo renderizador:** python-docx genera el .docx y LibreOffice lo convierte a PDF. | Decisión del usuario (25/11). La Estancia genera PDF (WeasyPrint) y Word (python-docx) por separado y documenta diferencias entre los dos; aquí el PDF es el mismo Word. |
| Testigos | **Exactamente 2** por expediente (los formatos tienen 2 lugares), cambiables por oficio. | Los Word oficiales. |
| Respuestas a mano | El 04, 08 y 09 solo precargan los datos de identificación; las respuestas se escriben en el papel. | Decisión del usuario (25/11). |
| Cargo impreso de testigos (y firmante) | Sin el nivel de la plaza: `AGENTE FEDERAL DE MIGRACIÓN "B"` → `AGENTE FEDERAL DE MIGRACIÓN`. Solo se quita una letra A–E suelta al final. | Decisión del usuario (25/11). Así aparece en los firmados. |
| Recuadro | Marcador `[[ RECUADRO ]]` … `[[ /RECUADRO ]]` en el texto: lo de en medio va en una tabla con borde (el motivo del 11). | Decisión del usuario (25/11). |
| Nacionalidad precargada | **Gentilicio** en minúsculas (china, rusa, francesa…) desde el código del país emisor (`apps/oficios/gentilicios.py`). Si no está en el catálogo, el nombre del país. Siempre editable. | Decisión del usuario (25/11): el texto dice "de nacionalidad china". |
| Evidencias del 09 | El extranjero presenta **de 1 a N evidencias** y el 09 da a **cada una su propio espacio**, con su verificación (a quién se verificó, hora, si hubo respuesta, intentos), su foto y una nota. Nombre, nacionalidad y requisito van una sola vez. Las fotos se suben en la app o se toman de la app Cámara; sin foto, recuadro vacío. **Hecho en la iteración 4** (también para el 05, con su foto y observaciones). | Sugerencia del usuario (25/11). Hoy se imprime un 09 por evidencia (AI000278, págs. 12 y 13). |

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
    - **Fundamento (24/11):** `fundamento` es el texto que se imprime. `fundamento_origen` vale `manual`, `plaza` o `''`. También están `fundamento_aplicable`, `fundamento_de_su_plaza` y `fundamento_asignado`.
  - `models.FundamentoPlaza`: catálogo propio de Viajes. Las 6 filas las siembra la migración 0004:

    | Fundamento | Texto | Se asigna solo si… |
    |---|---|---|
    | Titular | Artículo 12, apartado B, fracciones I, II y III | la plaza empieza con `TITULAR` |
    | Sub Representante Federal | Artículo 13, apartado B, fracciones I, II y III | nunca: hoy no existe esa plaza, solo a mano |
    | Representante Local | Artículo 14, apartado B, fracciones I, II y III | la plaza es `REPRESENTANTE LOCAL` |
    | Sub Representante Local | Artículo 15, apartado B, fracciones I, II y III | la plaza es `SUB REPRESENTANTE LOCAL` |
    | Subdirector de Control y Verificación Migratoria | Artículo 19, fracciones I, II, IV, V y IX | la plaza empieza con `SUBDIRECTOR` **y** la descripción contiene `CONTROL Y VERIFICACION` |
    | Jefe de Departamento | Artículo 23, fracciones I, II, III y IV | la plaza es `JEFE DE DEPARTAMENTO` |

    - Las reglas están en `fundamentos.py`: se compara sin acentos y en palabras completas, y gana la regla más específica.
    - Las otras subdirecciones (Regulación y Atención al Migrante) quedan **sin fundamento**: decisión del usuario.
    - `Empleado.fundamento_manual` le gana a la plaza, no lo toca la sincronización y solo cuenta si el fundamento sigue activo.
    - `precargar_fundamentos()` hace que el listado, el JSON y el admin consulten el catálogo una sola vez.
    - El texto se corrige en el admin, y solo el SuperUser puede. Se tomó del oficio 02 (Víctor, Art. 14) y del 07 (Melissa, Art. 23).
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
    - `<pk>/fundamento/`: POST, solo SuperUser y Aeropuerto. Asigna a mano un fundamento activo; vacío regresa al de su plaza.
    - Columna **Fundamento** en el listado:
      - "Sin fundamento" solo se marca en los firmantes habituales; los demás muestran "—".
      - "Cambiar" despliega el selector.
      - El contenedor pasó al ancho estándar de tablas operativas (1400px).
    - `buscar/` ahora devuelve también `fundamento` y `fundamento_origen`.
  - Admin de solo consulta, salvo `firmante_habitual` y `fundamento_manual`. Link "Empleados" en el menú lateral (`uploader/base_ds.html`).
- **Settings** en `settings/base.py`: `ESTANCIA_EMPLEADOS_URL`, `ESTANCIA_API_KEY`, `ESTANCIA_API_TIMEOUT`, `ESTANCIA_API_VERIFICAR_SSL`.
- **`settings/test.py`**: SQLite en memoria para correr tests sin MySQL ni `.env`.
- **`.bat`:**
  - `sincronizar_empleados.bat [--completa]` corre la sincronización y escribe en `logs\sincronizar_empleados.log`.
  - `programar_sincronizacion_empleados.bat` crea dos tareas de Windows, las dos como SYSTEM:
    - `INMViajes\SincronizarEmpleados`: cada 15 minutos, incremental.
    - `INMViajes\SincronizarEmpleadosCompleta`: diario a las 03:00, completa.
- **README:** tiene la sección "Catálogo de empleados".
- **Tests:** `apps.empleados` (67). Los 113 de Viajes pasan (24/11, en Linux con SQLite y el `env` de la raíz, Python 3.11).
- **Revisión visual (24/11):** la pantalla Empleados se probó con datos ficticios en Firefox headless, como Aeropuerto, como General y en ancho de celular. Falta revisarla con los datos reales.

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
- [ ] **Viajes (.12):** correr `actualizar_produccion.bat` y elegir **M** (migrate) para crear las tablas `empleados_*`. Son las migraciones 0001 a 0004; la 0004 siembra los 6 fundamentos.
- [ ] **Viajes (.12):** probar `sincronizar_empleados.bat` y revisar el log.
- [ ] **Viajes (.12):** correr `programar_sincronizacion_empleados.bat` como Administrador. Crea las 2 tareas.
- [ ] Probar de punta a punta contra la Estancia con D-144: primero una completa, luego una incremental. Esta vez no se probó con HTTP real, solo con tests.
- [ ] Revisar la pantalla **Empleados** en el navegador. No se revisó visualmente: solo se probó con tests.
- [ ] Marcar a los firmantes habituales (Carrillo, Melissa, Merenteria, Tello, Víctor…).
- [ ] Después de la primera completa con D-144, revisar en **Empleados** a los firmantes con "Sin fundamento" y asignarles uno a mano.
  - Víctor (REPRESENTANTE LOCAL) debe salir con el Art. 14.
  - Melissa (JEFA DE DEPARTAMENTO) debe salir con el Art. 23.
  - Sin D-144, la plaza llega con el texto viejo ("REPRESENTACION LOCAL DEL I.N.M. …") y no se asigna nada automáticamente.

### Observaciones a revisar

- **61 bajas** en la BD local, cuando se esperaban de 1 a 5. Confirmar en producción; puede ser que la copia local esté vieja.
- ~~**El cargo impreso no coincide con los datos.**~~ **Resuelto (24/11)** con D-144 en la Estancia: el cargo sale de la plaza, en femenino según quien firme, y Viajes ya usa el mismo criterio. Falta confirmar en producción que las plazas de los firmantes habituales traigan el puesto correcto. La migración 0021 de la Estancia separa el texto por prefijos, así que conviene revisar su tabla antes→después.
- **14 empleados sin número de empleado** en la Estancia.
- Se agregó una llave **solo de desarrollo** al `backend/.env` local de la Estancia. Git lo ignora y no sirve en producción.

---

## Fase 2 — Oficios en Viajes (iteraciones 1 a 4 hechas, 26/11)

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

- **Alcance (resuelto 24/11):** todos los formatos de la v1 van **uno por persona**. Los ❓ de la tabla quedan como "por persona"; solo falta decidir cuáles entran a la v1.
- **El texto traducido es idéntico entre oficiales.** Es texto fijo de la plantilla, no algo que se escriba por caso. Eso hace viable tener una variante por idioma.
- **Maquetación:** ~~tabla de 2 columnas~~. En lo impreso, el texto va **entrelazado**: el párrafo en español, luego ` / ` y la traducción, dentro del mismo párrafo. En el 04, cada etiqueta y cada pregunta va como `Nombre completo / 姓名`. El título también es bilingüe: `CONSTANCIA … (Chino) / 使用电子翻译器的证明 (中文)`.
- **"Formatos reunidos internación"** = paquete de varios oficios en un solo .docx, con 5 secciones.

#### Revisión de los 2 PDF firmados (24/11)

Son escaneos sin texto, de una Xerox VersaLink. **Cada PDF corresponde a una sola persona** y se nombra por su número de acta (`ORBC_AIMMTJ_<acta>_2026_EXP`). Por eso, en una familia, cada integrante tiene su propio expediente impreso.

| PDF | Tipo | Orden de las hojas |
|---|---|---|
| `AI000278` (24 págs.) | Internación, chino | 01 Acta de internación (5 págs.) → 02 → 03 → 04 (2 págs.) → 07 → 08 → 09 → 09 con foto → anexos (pasaporte, cartas, reservas, seguro) |
| `AR000316` (23 págs.) | Rechazo, ruso | 01 Acta de rechazo (5 págs.) → 02 → 03 → 04 en ruso (2 págs.) → 05 → hoja de evidencia fotográfica → 07 → 08 → 09 → 11 → 13 (+ hoja de requerimientos de alimentación) → 14 (2 págs.) → anexos (pasaporte, autorización electrónica, vuelo) |

- **Confirmado:** van **por número de formato**, del 02 al 14, y solo los que aplican. El 01 sale de CDMX y va antes. Los anexos son escaneos que no genera la app.
- **Con varias personas:** como cada persona tiene su propio PDF y su propia acta, el paquete se arma **por persona**: todos los oficios de A (02 → 14), luego todos los de B. Si conviene, se puede generar un archivo por persona.
- **Separadores:** la línea es `--------- HACE CONSTAR ---------`: título en negritas y centrado, con guiones a los dos lados y a todo lo ancho. Igual con `FUNDAMENTO`, `INICIO Y DESAHOGO DE LA SEGUNDA REVISIÓN` y `SE CIERRA Y SE AUTORIZA LO ACTUADO`. Además, los párrafos terminan con guiones hasta el margen y entre párrafos hay una línea completa de guiones. **En los PDF el título va sin espacios entre letras** (`HACE CONSTAR`, no `H A C E   C O N S T A R`).
- Algunos formatos ocupan más de una hoja: el 04 (2), el 14 (2), el 13 (+ requerimientos de alimentación) y el 05 (+ evidencia fotográfica).

### Iteración 1 — hecha (25/11) ✅

App `Viajes/apps/oficios/`. Sin commit todavía.

- **Modelos:**
  - `DatosOficina`: un solo registro, con Tijuana sembrado.
  - `HojaMembretada`: si no hay una activa, se usa `assets/hoja_membretada_2026.png`, que sale del Word oficial.
  - `MotivoRechazo`: los 6 del Word del 11.
  - `PlantillaOficio`: el **02** y el **11**, sembrados con el texto del Word oficial.
  - `Expediente`: con folio `VJ-2026-0001`.
  - `PersonaExpediente`, `OficioInstancia` y `OficioHistorial`.
- **Servicios (`services/`):**
  - `contexto.py`: 26 variables, con la fecha larga en español y la concordancia de género del firmante.
  - `variables.py`: sustitución con escape HTML.
  - `html_docx.py`: HTML de Quill → python-docx, con guiones por tabuladores con relleno. También tiene la limpieza del HTML por lista blanca.
  - `docx_oficio.py`: membrete, bloque institucional, título, fecha y firmas. Arma una sección por oficio, lista para el paquete.
  - `pdf.py`: usa `apps/redacciones/utils/conversion.py::convertir_a_pdf`, un alias público nuevo.
  - `expedientes.py`: todo el flujo.
- **Pantallas en `/oficios/`:**
  - Lista.
  - Nuevo: búsqueda en `Registro`, con "solo SR/R" por defecto.
  - Detalle:
    - firmante y testigos con autocompletado sobre `/empleados/buscar/`, mostrando cargo y fundamento;
    - personas editables;
    - formatos por persona con su estado.
  - Editor del oficio: Quill 2, guardado en `static/oficios/vendor/quill`, sin CDN.
    - Panel de variables y botones de separador y relleno.
    - Vista previa en PDF, descarga en Word y PDF, "Marcar como impreso" y "Reabrir" con motivo.
    - Historial.
  - Plantillas.
- **Permisos:** todo es `flujo_principal_required` (SuperUser y Aeropuerto). En el admin, los catálogos solo los edita el SuperUser.
- **Marcadores del texto:**
  - `[[ HACE CONSTAR ]]` es un separador con título.
  - `[[ ]]` es una línea completa de guiones.
  - Un párrafo que termina en ` --` se rellena con guiones hasta el margen.
- **Maquetación** (medida contra los PDF firmados):
  - Carta, Noto Sans a 10 pt con interlineado sencillo.
  - Márgenes: 1.59 cm a los lados, 3.4 cm arriba y 4 cm abajo, para librar la bandera y el pie "2026 Margarita Maza".
  - La hoja membretada se ancla con la misma posición y tamaño que en el Word oficial (`header2.xml` del 02: 21.58 × 27.46 cm, subida ~0.45 cm).
  - Una fila de firmas nunca se parte entre hojas (`cantSplit`).
  - Con datos ficticios, el 02 y el 11 caben en una hoja cada uno.
- **Dependencias:**
  - `python-docx==1.1.2` y `lxml==6.1.3` en `requirements.txt`.
  - Wheels para Windows y Python 3.11 en `vendor/python-docx-wheels.zip`.
  - Pasos de despliegue en el README, sección "Oficios".
- **Tests:** `apps.oficios` (56), incluida una conversión real a PDF que se salta si no hay LibreOffice. Los 169 de Viajes pasan (25/11).
- **Prueba de punta a punta** (local, con una instancia temporal y datos ficticios):
  - buscar pasajeros y crear el expediente;
  - firmas, con validación de que el firmante y los testigos no se repitan;
  - borradores, guardar (el `<script>` se elimina) e imprimir;
  - intentar editar congelado, descargar Word y PDF y reabrir.
  - Pantallas revisadas con Firefox headless.

**Observaciones de la iteración 1:** las tres primeras se resolvieron en la iteración 2.
- ~~**Cargo del testigo:** se imprimía con el nivel.~~ Ahora sale sin él.
- ~~**Recuadro del 11.**~~ Ahora el motivo va en un recuadro.
- ~~**Nacionalidad como país.**~~ Ahora se precarga el gentilicio.
- **Fuentes en el .12:** falta instalar Noto Sans; sin ella, LibreOffice usa otra fuente.
- **Antecedente en Redacciones:** `subir.html` y `editar.html` usan `var(--ds-sp-5)`, que no existe en el sistema de diseño, así que no hay espacio entre bloques. En Oficios se usa `--ds-sp-6`.

### Iteración 2 — hecha (25/11) ✅

Hecho:
- **Paquete** (`/oficios/<id>/paquete/`):
  - Se eligen oficios del expediente con casillas; cada persona tiene "Todos".
  - Sale un solo **Word** o **PDF**, ordenado por persona y luego del 02 al 14. Si se eligen los de una sola persona, el archivo lleva su nombre.
  - **Marcar como impresos** congela varios oficios a la vez y reporta, uno por uno, los que no se pudieron imprimir.
  - Los oficios ya impresos salen con lo congelado.
  - Nuevo campo `OficioInstancia.snap_formato`: congela el título, las firmas y la fecha de la plantilla, para que el oficio impreso salga igual aunque la plantilla cambie después.
- **Borradores para toda la familia:**
  - En el detalle se crean los mismos formatos para todas las personas, sin duplicar.
  - Vienen marcados los formatos sugeridos según el resultado (`FORMATOS_SUGERIDOS`, tomado de los 2 PDF firmados).
- **Plantilla 07** (Constancia de llamada consular):
  - Sin la línea "Ciudad, fecha.", porque la fecha va dentro del texto.
  - Las mismas negritas que el original, para que quepa en una hoja.
- **Bloque de firmas `EMPRESA`** (representante de la aerolínea y autoridad), listo para el 13.
- **Recuadro, cargo sin nivel y gentilicios:** ver la tabla de decisiones. En el editor hay un botón "Agregar recuadro".
- **Firmas más compactas:**
  - La línea de firma ahora es el **borde superior del nombre** (`w:pBdr`, insertado en el orden que exige el esquema), no un renglón de guiones bajos.
  - Ya no hay un párrafo vacío antes de la tabla de firmas.
  - Con eso, una familia de 2 personas con 02, 07 y 11 sale en **6 hojas exactas**, comparado con 8 antes.
  - En el 11, la persona firma sobre una línea a lo ancho de su columna, con "Recibí original…" debajo.
- **Migraciones:** 0003 (esquema: `snap_formato` y EMPRESA) y 0004 (datos: el 07, más el recuadro del 11 si su texto no se había editado).
- **Tests:** `apps.oficios` (72). Los 185 de Viajes pasan (25/11).

**Segunda parte, ya con la USB: plantillas 08, 09, 12, 13 y 14** (migraciones 0005 a 0007).
- **Texto:** se copió de cada Word oficial, con las mismas negritas, y se comparó con los impresos de `AR000316`.
- **Formatos:**
  - **08:** constancia de llamada personal. Sin línea de fecha; los datos de la llamada se escriben a mano.
  - **09:** tabla de datos con una fila con borde por dato, renglones para observaciones y recuadro alto para la evidencia. Firmas solo de la autoridad y la persona (bloque `AUTORIDAD_PERSONA`); no pide testigos.
  - **12:** usa `{{numero_acta}}`. Su cierre `[[ CONSTE | SE CIERRA Y SE AUTORIZA LO ACTUADO ]]` lleva dos títulos.
  - **13:** dos hojas, separadas con `[[ NUEVA HOJA ]]`, que repite el encabezado institucional.
    - Acuse con `[[ FIRMA: … ]]` del representante.
    - Requerimientos de alimentación con `[[ RENGLÓN ]]`.
    - Bloque `EMPRESA`.
  - **14:** bloque `ACUERDO` en 3 filas: autoridad y persona; representante de la aerolínea centrado en una celda combinada; testigos.
- **Marcadores nuevos del editor**, cada uno con su botón en el panel:
  - `[[ RENGLÓN ]]` y ` __`: líneas para escribir a mano (tabulador con relleno de guion bajo).
  - `[[ A | B ]]`: separador con varios títulos.
  - `[[ TABLA ]]…[[ /TABLA ]]`: una fila con borde por párrafo.
  - `[[ FIRMA: leyenda ]]`, `[[ NUEVA HOJA ]]` y `«campo»`.
- **Campos `«…»`:** lo que se llena en cada caso, como el representante, el vuelo de salida o el destino del 13, o la ruta del 14. `revisar()` lo reporta como **error**, así que no deja imprimir hasta llenarlo.
- **Persona:** se agregan `fecha_arribo` y `origen`. Se precargan del `Registro` (`vuelo_fecha` y `aeropuerto_salida`, con un catálogo de aeropuertos); la aerolínea sale del prefijo IATA del vuelo (`apps/oficios/catalogos.py`).
- **Tamaño de letra por plantilla** (`tamano_letra_pt`, el `w:sz` de cada Word oficial):
  - 02, 07 y 08: 9.5 pt; 09, 12, 13 y 14: 9 pt; 11: 10 pt.
  - Se congela al imprimir y se edita en la pantalla de plantillas.
  - Con 10 pt para todos, el 09, el 12 y el 14 se pasaban de hoja.
- **Renglón vacío:** el `<p><br></p>` de Quill ahora es un solo renglón vacío (antes ocupaba dos).
- **Resultado:** con datos ficticios, 08 + 09 + 12 + 13 + 14 salen en **7 hojas**, como los originales (el 13 y el 14 en 2 cada uno). Y 02 + 07 + 11 de 2 personas sigue en 6 hojas.
- **Tests:** `apps.oficios` (85). Los 198 de Viajes pasan (25/11).

**Observaciones de la segunda parte (para el usuario):**
- **El 14 trae dos errores en el texto oficial**, que también aparecen en el acta firmada: "…a los servidores públicos adscritos a las Delegaciones del Instituto Nacional de publicado…" (le falta "Migración,") y "…por el que se determina la y circunscripción…" (le falta "sede"). Se copiaron tal cual. Si se corrigen, se hace en Oficios → Plantillas → 14.
- **14, "Así lo acuerda y firma…":** el Word dice "Sub Representación **Federal**" y el impreso de Tijuana "Sub Representación **Local**". Se usó Local, que es lo que se imprime aquí.
- **El 13 se precarga con Noto Sans**, como todos, aunque su Word use Arial.
- **Evidencia fotográfica del 09:** el recuadro sale vacío para pegar o anexar la evidencia en papel. Meter la foto desde la app queda para la iteración 4.

**Nota de maquetación:** el arte del pie de la hoja membretada empieza a ~24 cm, porque se respeta la posición del Word oficial. Por eso el texto no puede bajar de ahí. En los escaneos el arte se ve más abajo, pero es por la escala de la impresora o del escáner (el logo de arriba también aparece desplazado), así que no sirven para medir.

### Iteración 3 — hecha (25/11) ✅

Traducciones por idioma (migraciones 0008 y 0009).
- **Modelo `PlantillaOficioIdioma`:** una por formato e idioma (chino, ruso, francés, inglés o árabe). Lleva:
  - título bilingüe;
  - texto bilingüe completo (vacío = el mismo texto en español de la plantilla);
  - leyenda bajo la firma de la persona ("NOMBRE Y FIRMA / 姓名和签名");
  - si está activa.

  Cada versión que se guarda, de la plantilla o de una traducción, queda en `PlantillaHistorial`.
- **Borradores:** se crean en el idioma de la persona si su formato tiene traducción activa; si no, en español, y la app avisa cuáles quedaron en español. En el oficio, "Recargar texto" cambia el idioma de un borrador.
- **Al imprimir** se congelan el título bilingüe y la leyenda (`snap_formato`).
- **Pantalla de traducción** (Plantillas → "+ Traducción" o el nombre del idioma):
  - Empieza con el texto en español para pegar la traducción donde va.
  - Avisa de las variables del español que faltan y bloquea las que no existen.
  - Avisa si el español cambió después de la traducción y deja el español a la vista como referencia.
  - Solo SuperUser y Aeropuerto.
- **Texto chico:** el editor tiene un tamaño "chico" que sale a 8 pt. Así van las traducciones en los Word oficiales, con el español a 9.5 pt, y por eso el 02 bilingüe cabe en una hoja.
- **Fuentes:**
  - El chino usa `Microsoft YaHei`, que viene con Windows. Aquí en Linux, LibreOffice tomó Noto Sans CJK sin cuadritos.
  - El árabe usa `Arial` como escritura compleja. Sus tramos van como runs de derecha a izquierda y un párrafo mayormente árabe sale bidireccional y alineado a la derecha.
- **Campos `«…»`:** solo cuentan los que están EN MAYÚSCULAS. En ruso y francés `«…»` son comillas normales; por ejemplo, la traducción oficial dice «Vasco Translator V4 (electronic translator)».
- **Sembradas, del texto de la USB:**
  - 02 en chino, ruso y francés: título, párrafo del HACE CONSTAR y leyenda.
  - 07, 08 y 09 en chino y ruso: solo la leyenda.
  - En los demás formatos implementados, las copias por idioma no traen traducción.
- **Datos personales:** las copias tenían datos de casos reales. El nombre pasó a `{{extranjero_nombre}}` y la nacionalidad escrita en francés a `«NATIONALITÉ EN FRANÇAIS»`.
- **Tests:** `apps.oficios` (99). Los 212 de Viajes pasan.

**Observaciones de la iteración 3 (para el usuario):**
- El título ruso del 02 dice "(китайский язык)", que significa "(idioma chino)": parece un error de la copia. Se dejó tal cual y se corrige en Plantillas → 02 → Ruso.
- La copia francesa del 09 trae la leyenda en chino ("姓名及签名"), así que no se sembró francés para el 09.
- La traducción francesa del 02 terminaba con un "。" chino de sobra; se quitó.
- No hay traducciones al inglés ni al árabe en la USB. Las capturan los agentes desde la app.

### Iteración 4 — hecha (26/11) ✅

Formularios 03, 04, 04.1 y 05, y el 09 con 1 a N evidencias (migraciones 0010 a 0012).

- **Plantillas nuevas**, convertidas de los Word de la USB (los Word no se suben al repo porque traen datos reales):

  | # | Formato | Letra | Firmas | Notas |
  |---|---|---|---|---|
  | 03 | Notificación de segunda revisión | 7 pt (notas al pie 5.5 pt) | En el texto: persona y acompañantes lado a lado, y la autoridad que canaliza | Casillas ☐, superíndices y notas al pie. Cabe en **1 hoja**, como el original. |
  | 04 | Cuestionario de segunda entrevista | 8 pt | Persona (en el texto) | Solo se precargan los datos de identificación; las respuestas van a mano. **2 hojas**. |
  | 04.1 | Cuestionario para residentes | 8 pt | Persona (en el texto) | Su único Word ya venía con chino; la base en español es ese texto sin el chino. **2 hojas**. |
  | 05 | Constancia de condición médica | 9.5 pt | Autoridad y persona | Evidencias fotográficas. Con una evidencia cabe en **1 hoja**. |

- **Número `04.1`:** `PlantillaOficio.numero` pasó a decimal (migración 0011). `clave` imprime `04.1` y el paquete lo ordena entre el 04 y el 05.
- **Traducciones sembradas:** 03 en chino, ruso y francés (título y leyendas de firma); 04 en chino y francés (cuestionario completo); 04.1 en chino.
- **Motor (`html_docx.py`):**
  - `[[ TABLA ]]` acepta varias columnas: las celdas de una fila se separan con ` || ` y la última abarca lo que sobre.
  - `[[ FIRMA: A || B ]]`: dos firmas lado a lado. La línea de firma mide al menos 7 cm.
  - `<sup>` (superíndice). El tamaño "chico" es el cuerpo menos 1.5 pt, con un mínimo de 5 pt.
  - `[[ EVIDENCIAS ]]`: ahí van los bloques de evidencia (ver abajo).
  - LibreOffice no dibujaba el relleno (guiones o línea) de un tabulador que cierra un párrafo **dentro de una tabla**. Ahora va un espacio de ancho cero después del tabulador. Arregla las líneas ` __` de los recuadros y tablas.
- **Evidencias (modelo `Evidencia`, ligada a la persona y al formato):**
  - Campos: `verificacion_a`, `hora`, `respuesta` (Sí / No / sin dato), `intentos`, `nota`, `foto` (`oficios/evidencias/%Y/%m/`) y `foto_rechazo` (si se tomó de Cámara).
  - La plantilla dice qué evidencias lleva (`PlantillaOficio.evidencias`): **VERIFICACION** en el 09 (a quién, hora, respuesta, intentos, observaciones y foto) y **FOTO** en el 05 (observaciones y foto).
  - **Captura:** en el detalle, dentro de cada persona, una sección "Evidencias del 05/09" con alta, edición y quitar. El campo de foto abre la cámara en el celular; acepta JPG, PNG o WEBP de hasta 15 MB. "Usar foto de Cámara" copia una `FotoRechazo` del registro de la persona.
  - **Impreso:** cada evidencia sale en su propio bloque con borde que no se parte entre hojas. La foto se reduce (lado máximo 1400 px, girada según EXIF) y se ajusta al ancho, con alto máximo de 7 cm en el 09 y 5 cm en el 05. Sin foto sale el espacio en blanco con su leyenda; sin evidencias, un bloque en blanco para llenar a mano.
  - **Al imprimir** se congelan los datos (`snap_formato['evidencias']`) y las fotos quedan dentro del .docx. Con el oficio impreso, sus evidencias no se pueden agregar, cambiar ni quitar hasta reabrirlo.
  - `revisar()` avisa (no bloquea) si no hay evidencias o si alguna no tiene foto.
- **Plantilla 09:** el recuadro fijo se cambió por `[[ EVIDENCIAS ]]`, solo si su texto seguía igual al sembrado en la 0006.
- **Resultado visual** (datos y fotos ficticios): el 09 con 3 evidencias (2 con foto, 1 sin foto) sale en 2 hojas con las firmas al final. Los paquetes anteriores no cambiaron: 08–14 en 7 hojas, 02+07+11 de 2 personas en 6 y las traducciones de la iteración 3 en 4.
- **Tests:** `apps.oficios` (115). Los 228 de Viajes pasan (26/11).

**Observaciones de la iteración 4 (para el usuario):**
- **04.1 en chino:** la leyenda de la firma del Word decía "以下是该短语的对应中文：" ("esta es la traducción al chino de la frase"), que es un residuo de traductor automático. Se cambió por la del 04, "外国人姓名及签名".
- **03 en ruso:** la leyenda de acompañantes empieza "случае путешествия…" y le falta la "В" inicial ("В случае…"). Se dejó como en la USB.
- **04 en francés:** la copia de la USB traduce solo una parte de las etiquetas (por ejemplo "País de Residencia habitual", "Numero de Pasaporte" o "Numero de vuelo de llegada" van solo en español). Se copió tal cual; se completa en Plantillas → 04 → Francés.
- Las respuestas del 04 y el 04.1 se siguen escribiendo a mano.

### Diseño propuesto

Hay que tomar como referencia el motor de la Estancia (`ProyectoEstancia/backend/apps/Oficios`):

- **De ahí se copia:** el patrón de `OficioPlantilla` con variables, el generador de .docx (`services/docx_renderer.py`), la concordancia de género, y membrete, encabezado y tipografía con "un solo activo" (`MembreteAsset`, `ConfiguracionTipografia`).
- **Variante por idioma:** mismo patrón que `OficioPlantillaEstancia` (allá es una variante por estancia; aquí, por idioma).
- **Borrador editable con historial:** mismo patrón que `OficioLibreInstancia` y `OficioLibreHistorial`.

Modelo tentativo para Viajes:

```
Expediente (familia)
 ├─ firmante        → empleados.Empleado (+ copia congelada: nombre_para_oficio, cargo, sexo, fundamento)
 │                    → las plantillas usan {{firmante.fundamento}}; si está vacío, NO se genera el oficio
 ├─ testigos[]      → empleados.Empleado (+ copia congelada)
 └─ personas[]      PersonaExpediente
      ├─ registro?   → uploader.Registro (opcional: solo para precargar)
      ├─ nombre, nacionalidad, fecha_nacimiento, documento   (editables a mano)
      └─ idioma      (por persona; se sugiere por nacionalidad, editable)

PlantillaOficio (número 02–14, nombre, contenido + variables)      ← sin campo "alcance": todas son por persona
 └─ PlantillaOficioIdioma (plantilla, idioma, texto traducido con las mismas {{variables}}, historial)
    → se captura una vez y se reutiliza en todos los oficios futuros de ese idioma
    → si no hay variante para el idioma de la persona, sale en español

OficioInstancia (expediente, plantilla, persona, contenido editable, testigos_override?, historial)
 → se congela al imprimir

Paquete: el usuario elige formatos y personas → un oficio por (formato × persona)
 → orden: por persona y, dentro de cada persona, por número de formato (02 → 14)
 → un .docx (una sección por oficio) y un PDF; opcionalmente uno por persona
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
- **Guiones medios (resuelto 24/11):** no se calcula nada. En el .docx se usan **tabuladores con relleno de guiones**:
  - **Separador con título:** párrafo con una tabulación centrada y otra derecha en el margen, las dos con `leader="hyphen"`. El texto es `⇥HACE CONSTAR⇥`.
  - **Relleno al final del párrafo:** una tabulación derecha en el margen con `leader="hyphen"`, y un `⇥` al final del texto.
  - **Línea completa de guiones:** un párrafo vacío con solo `⇥` y la misma tabulación.

  Word y LibreOffice llenan los guiones solos según el ancho, así que no se rompe con otra impresora ni con otro tamaño de letra. **Implementado (25/11):** en el texto, `[[ HACE CONSTAR ]]`, `[[ ]]` y ` --` al final del párrafo.
- **Autocompletado de firmante y testigos:** usar `GET /empleados/buscar/?q=&municipio=`, que ya existe y devuelve `nombre_para_oficio`, `cargo` y `sexo`.

### Preguntas abiertas para el usuario

Todas respondidas el 24/11. Ver la tabla de decisiones.

1. ~~Por persona o por expediente~~ → todos **por persona**.
2. ~~Solución de los guiones~~ → separadores fijos con título espaciado, sin calcular el relleno.
3. ~~Traducciones al inglés y al árabe~~ → las pegan los agentes. La columna traducida es editable.
4. ~~Cargo impreso~~ → la plaza (D-144).
5. ~~Orden del paquete~~ → del 02 al 14, solo los que elija el usuario.
6. ~~Idioma~~ → **por persona**.
7. ~~Datos del extranjero~~ → nombres, nacionalidad, fecha de nacimiento y documento, precargados de `Registro` y editables a mano.

**Pendientes nuevos:** todos resueltos el 24/11 con la revisión de los PDF y las respuestas del usuario:
- Formato del separador.
- Orden por persona.
- Nacionalidad precargada desde `pais_emision`.
- Permisos para editar traducciones.

### Orden sugerido para la siguiente sesión

1. Cerrar el despliegue de la fase 1 (checklist de arriba) y desplegar Oficios: wheels, fuentes Noto Sans y migrate (0001 a 0012).
2. Revisar con el usuario las observaciones de la iteración 2: errores del texto del 14 y Sub Representación Local o Federal.
3. ~~**Iteración 3:** traducciones.~~ Hecha (25/11). Pendiente: que los agentes capturen inglés y árabe y revisen el título ruso del 02.
4. ~~**Iteración 4:** formularios 03, 04, 04.1 y 05, y el 09 con 1 a N evidencias.~~ Hecha (26/11). Pendiente: revisar con el usuario las observaciones de la iteración 4.

---

## Cómo correr los tests

**Estancia** (desde `backend/`, con el venv del proyecto):

```powershell
env/Scripts/python.exe manage.py test apps.Personal.tests.test_integracion_empleados --settings=EstanciaBackend.settings.test --noinput
```

**Viajes** (desde `Viajes/`, sin MySQL):

```powershell
python manage.py test apps.empleados apps.oficios --settings=Viajes.settings.test
```

Viajes no tiene un `env` propio en el repo. Para correr sus tests hay que crear uno e instalar `requirements.txt` sin `mysqlclient` ni `PyMySQL`. En Linux con Python 3.14, `pandas` se instala desde wheel.
