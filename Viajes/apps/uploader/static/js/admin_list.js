// Variables globales
let searchTimeout;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const paisFilter = document.getElementById('paisFilter');
// País aplicado (el del URL); el texto del input puede diferir mientras se escribe.
let paisSeleccionado = paisFilter ? paisFilter.dataset.seleccionado : '';
// El lote ya no tiene selector; llega por ?batch= desde Cargas y se quita con su chip.
let loteActivo = new URLSearchParams(window.location.search).get('batch') || '';
const segundaRevisionFilter = document.getElementById('segundaRevisionFilter');  // ← CAMBIO 1
const rechazadoFilter = document.getElementById('rechazadoFilter');              // ← CAMBIO 2
const internacionFilter = document.getElementById('internacionFilter');          // ← CAMBIO 3

// Auto-focus en el buscador si tiene contenido al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const highlightId = urlParams.get('highlight');
    
    // Si hay búsqueda activa, SIEMPRE hacer focus en el buscador
    if (searchInput.value.trim()) {
        // Mostrar botón de limpiarp
        clearSearchBtn.classList.remove('hidden');
        
        // Hacer focus inmediato en el buscador
        setTimeout(() => {
            searchInput.focus();
            searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        }, 100);
        
        // Si también hay un registro actualizado en esta página, hacer scroll
        if (highlightId) {
            const registroElement = document.getElementById(`registro-${highlightId}`);
            if (registroElement) {
                setTimeout(() => {
                    registroElement.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                    
                    // Efecto visual temporal (resaltado de fila del design system)
                    registroElement.classList.add('ds-row-selected');
                    setTimeout(() => {
                        registroElement.classList.remove('ds-row-selected');
                    }, 2000);
                }, 300);
            }
        }
    }
});

// Función para mostrar/ocultar botón de limpiar mientras escribes
searchInput.addEventListener('input', function() {
    const searchValue = this.value.trim();
    
    // Mostrar/ocultar botón de limpiar
    if (searchValue) {
        clearSearchBtn.classList.remove('hidden');
    } else {
        clearSearchBtn.classList.add('hidden');
    }
});

// Búsqueda SOLO al presionar Enter (sin búsqueda automática)
searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        applyFilters();
    }
});

// Limpiar búsqueda
function clearSearchFilter() {
    searchInput.value = '';
    clearSearchBtn.classList.add('hidden');
    
    // Aplicar filtros sin el parámetro search
    applyFilters();
}

function quitarFiltroLote() {
    loteActivo = '';
    applyFilters();
}

// Aplicar filtros cuando cambien
if (segundaRevisionFilter) {                                                    // ← CAMBIO 4
    segundaRevisionFilter.addEventListener('change', applyFilters);
}

if (rechazadoFilter) {                                                          // ← CAMBIO 5
    rechazadoFilter.addEventListener('change', applyFilters);
}

if (internacionFilter) {                                                        // ← CAMBIO 6
    internacionFilter.addEventListener('change', applyFilters);
}

function applyFilters() {
    const params = new URLSearchParams();
    
    // Búsqueda
    const searchValue = searchInput.value.trim();
    if (searchValue) {
        params.set('search', searchValue);
    }
    
    // Nacionalidad (país de emisión)
    if (paisSeleccionado) {
        params.set('pais', paisSeleccionado);
    }

    // Lote (solo si se llegó con ?batch=)
    if (loteActivo) {
        params.set('batch', loteActivo);
    }
    
    // Segunda Revisión (SR)
    if (segundaRevisionFilter.checked) {                                        // ← CAMBIO 7
        params.set('segunda_revision', 'true');                                 // ← CAMBIO 8
    }
    
    // Rechazo (R)
    if (rechazadoFilter.checked) {                                              // ← CAMBIO 9
        params.set('rechazado', 'true');                                        // ← CAMBIO 10
    }
    
    // Internación (I)
    if (internacionFilter.checked) {                                            // ← CAMBIO 11
        params.set('internacion', 'true');                                      // ← CAMBIO 12
    }
    
    // Redirigir con los nuevos filtros (siempre a la página 1)
    window.location.search = params.toString();
}

// =====================================================================
// Buscador de nacionalidad (combobox): la lista se filtra en cada tecla
// sin distinguir acentos ni mayúsculas ("esta" → Estados Unidos,
// "mexico" → México). Al elegir un país se recarga con ?pais=.
// =====================================================================
(function () {
    if (!paisFilter) return;
    const lista = document.getElementById('paisListbox');
    const btnLimpiar = document.getElementById('paisClear');
    const dataEl = document.getElementById('nacionalidadesData');
    const placeholderBase = paisFilter.placeholder;

    function normalizar(s) {
        return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }

    function escapar(s) {
        return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    const paises = (dataEl ? JSON.parse(dataEl.textContent) : []).map((p) => ({
        nombre: p.pais_emision,
        total: p.total,
        clave: normalizar(p.pais_emision),
    }));
    // Primera opción con el texto vacío: quita el filtro.
    const todas = { nombre: '', total: paises.reduce((s, p) => s + p.total, 0), clave: '' };
    let visibles = [];
    let activo = -1;

    // Resalta la coincidencia. Quitar acentos conserva la longitud en los
    // nombres en español, así que los índices de la clave sirven en el original.
    function resaltar(p, q) {
        const i = q ? p.clave.indexOf(q) : -1;
        if (i < 0 || p.clave.length !== p.nombre.length) return escapar(p.nombre);
        return escapar(p.nombre.slice(0, i)) + '<mark>' + escapar(p.nombre.slice(i, i + q.length)) + '</mark>' + escapar(p.nombre.slice(i + q.length));
    }

    // Orden: empieza con el texto → empieza una palabra → lo contiene.
    // El sort es estable, así que dentro de cada grupo queda alfabético.
    function filtrar(q) {
        if (!q) return [todas, ...paises];
        const rango = (p) => {
            const i = p.clave.indexOf(q);
            if (i < 0) return -1;
            if (i === 0) return 0;
            return p.clave[i - 1] === ' ' ? 1 : 2;
        };
        return paises
            .map((p) => ({ p, r: rango(p) }))
            .filter((x) => x.r >= 0)
            .sort((a, b) => a.r - b.r)
            .map((x) => x.p);
    }

    function render(q) {
        visibles = filtrar(q);
        if (!visibles.length) {
            lista.innerHTML = `<li class="ds-combo-empty" role="presentation">Sin coincidencias para “${escapar(paisFilter.value.trim())}”</li>`;
        } else {
            lista.innerHTML = visibles.map((p, i) => {
                const sel = p.nombre === paisSeleccionado;
                const nombre = p === todas ? 'Todas las nacionalidades' : resaltar(p, q);
                return `<li id="paisOpt-${i}" class="ds-combo-opt" role="option" aria-selected="${sel}" data-i="${i}">` +
                    `<svg class="ds-icon ds-icon-sm ds-combo-check" aria-hidden="true" viewBox="0 0 24 24">${sel ? '<path d="M20 6 9 17l-5-5"/>' : ''}</svg>` +
                    `<span class="ds-combo-name">${nombre}</span>` +
                    `<span class="ds-combo-count">${p.total.toLocaleString('es-MX')}</span></li>`;
            }).join('');
        }
        abrir();
        // Con texto, la primera coincidencia queda activa (Enter la elige);
        // sin texto, se posiciona sobre el país ya aplicado.
        marcarActivo(q ? (visibles.length ? 0 : -1) : visibles.findIndex((p) => p.nombre === paisSeleccionado));
    }

    function marcarActivo(i) {
        const prev = lista.querySelector('.is-active');
        if (prev) prev.classList.remove('is-active');
        activo = i;
        if (i < 0) {
            paisFilter.removeAttribute('aria-activedescendant');
            return;
        }
        const opt = document.getElementById(`paisOpt-${i}`);
        opt.classList.add('is-active');
        // Scroll solo dentro de la lista (scrollIntoView movería también la página)
        const arriba = opt.offsetTop;
        const abajo = arriba + opt.offsetHeight;
        if (arriba < lista.scrollTop) lista.scrollTop = arriba;
        else if (abajo > lista.scrollTop + lista.clientHeight) lista.scrollTop = abajo - lista.clientHeight;
        paisFilter.setAttribute('aria-activedescendant', opt.id);
    }

    function abrir() {
        lista.hidden = false;
        paisFilter.setAttribute('aria-expanded', 'true');
    }

    function cerrar() {
        lista.hidden = true;
        paisFilter.setAttribute('aria-expanded', 'false');
        paisFilter.removeAttribute('aria-activedescendant');
        activo = -1;
    }

    function elegir(nombre) {
        cerrar();
        paisFilter.value = nombre;
        if (nombre === paisSeleccionado) return;
        paisSeleccionado = nombre;
        applyFilters();
    }

    // Al entrar se vacía el campo para teclear directo; el país aplicado
    // queda como placeholder y se restaura al salir sin elegir.
    paisFilter.addEventListener('focus', () => {
        paisFilter.value = '';
        paisFilter.placeholder = paisSeleccionado || placeholderBase;
        render('');
    });

    paisFilter.addEventListener('blur', () => {
        cerrar();
        paisFilter.value = paisSeleccionado;
        paisFilter.placeholder = placeholderBase;
    });

    paisFilter.addEventListener('input', () => render(normalizar(paisFilter.value.trim())));

    paisFilter.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            if (lista.hidden) { render(normalizar(paisFilter.value.trim())); return; }
            if (!visibles.length) return;
            const paso = e.key === 'ArrowDown' ? 1 : -1;
            marcarActivo((activo + paso + visibles.length) % visibles.length);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activo >= 0) elegir(visibles[activo].nombre);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            paisFilter.blur();
        }
    });

    // mousedown (no click) para elegir antes de que el input pierda el foco
    lista.addEventListener('mousedown', (e) => {
        e.preventDefault();
        const opt = e.target.closest('.ds-combo-opt');
        if (opt) elegir(visibles[Number(opt.dataset.i)].nombre);
    });

    // ✕ visible solo con texto: con país aplicado lo quita; si no, limpia lo tecleado.
    btnLimpiar.addEventListener('mousedown', (e) => e.preventDefault());
    btnLimpiar.addEventListener('click', () => {
        if (paisSeleccionado) { elegir(''); return; }
        paisFilter.value = '';
        render('');
    });
})();

// Modal functions
function openEditModal(registroId, comentario) {
    const modal = document.getElementById('editModal');
    const editForm = document.getElementById('editForm');
    const comentarioTextarea = document.getElementById('comentario');
    
    if (editForm && comentarioTextarea) {
        const urlPrefix = window.URL_PREFIX || '';
        editForm.action = `${window.location.origin}${urlPrefix}/update/${registroId}/`;
        comentarioTextarea.value = comentario;
        modal.showModal();
    }
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) {
        modal.close();
    }
}

// Abrir modal de captura de menor; precarga fecha de hoy si está vacía
function abrirModalMenor() {
    const modal = document.getElementById('modalCapturaMenor');
    const fechaInput = document.getElementById('menorFechaVuelo');
    if (fechaInput && !fechaInput.value) {
        const hoy = new Date();
        const yyyy = hoy.getFullYear();
        const mm = String(hoy.getMonth() + 1).padStart(2, '0');
        const dd = String(hoy.getDate()).padStart(2, '0');
        fechaInput.value = `${yyyy}-${mm}-${dd}`;
    }
    modal.showModal();
}

// Router de modal desde botón Acciones:
//   rechazado=true  -> modal foto+comentario
//   en otro caso    -> modal de comentario simple
function openAccionesModal(registroId, comentario, rechazado) {
    if (rechazado) {
        abrirModalFoto(registroId);
    } else {
        openEditModal(registroId, comentario);
    }
}

// Función para abrir modal de subida de foto
function abrirModalFoto(registroId) {
    const modal = document.getElementById('modalFotoRechazo');
    const form = document.getElementById('formFotoRechazo');
    const comentarioTextarea = document.getElementById('comentarioRechazo');
    
    // Configurar la acción del formulario con el ID del registro
    const urlPrefix = window.URL_PREFIX || '';
    form.action = `${window.location.origin}${urlPrefix}/camara/subir/${registroId}/`;
    
    // Limpiar preview anterior
    limpiarFotoRechazo();
    
    // Obtener el comentario actual del registro desde la fila de la tabla
    const filaRegistro = document.getElementById(`registro-${registroId}`);
    if (filaRegistro) {
        // Buscar el td que contiene el comentario (4ta columna sticky)
        const comentarioTd = filaRegistro.querySelector('td:nth-child(4) div');
        const comentarioActual = comentarioTd ? comentarioTd.getAttribute('title') : '';
        comentarioTextarea.value = comentarioActual || '';
    } else {
        comentarioTextarea.value = '';
    }
    
    // Mostrar modal
    modal.showModal();
    
    // Agregar event listener para pegar desde portapapeles
    document.addEventListener('paste', manejarPegadoImagen);
}

// Función para manejar pegado desde portapapeles
function manejarPegadoImagen(event) {
    const modal = document.getElementById('modalFotoRechazo');
    
    // Solo procesar si el modal está abierto
    if (!modal.open) {
        return;
    }
    
    const items = event.clipboardData?.items;
    if (!items) return;
    
    // Buscar imagen en el portapapeles
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        
        // Validar que sea una imagen
        if (item.type.indexOf('image') !== -1) {
            event.preventDefault();
            
            const blob = item.getAsFile();
            
            // Validar formato de imagen
            const formatosPermitidos = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
            if (!formatosPermitidos.includes(blob.type)) {
                alert('Formato no permitido. Solo JPG, JPEG, PNG o WEBP.');
                return;
            }
            
            // Crear archivo para el input
            const inputFile = document.getElementById('inputFotoRechazo');
            const dataTransfer = new DataTransfer();
            
            // Crear archivo con nombre descriptivo
            const nombreArchivo = `rechazo_${new Date().getTime()}.${blob.type.split('/')[1]}`;
            const file = new File([blob], nombreArchivo, { type: blob.type });
            
            dataTransfer.items.add(file);
            inputFile.files = dataTransfer.files;
            
            // Mostrar preview
            mostrarPreviewFotoRechazo(file);
            
            break;
        }
    }
}

// Función para mostrar preview de la imagen
function mostrarPreviewFotoRechazo(file) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const preview = document.getElementById('previewFotoRechazo');
        const img = document.getElementById('imgPreviewRechazo');
        
        img.src = e.target.result;
        preview.classList.remove('hidden');
    };
    
    reader.readAsDataURL(file);
}

// Función para limpiar la foto y preview
function limpiarFotoRechazo() {
    const inputFile = document.getElementById('inputFotoRechazo');
    const preview = document.getElementById('previewFotoRechazo');
    const img = document.getElementById('imgPreviewRechazo');
    
    inputFile.value = '';
    img.src = '';
    preview.classList.add('hidden');
}

// Event listener para mostrar preview cuando se selecciona archivo
document.addEventListener('DOMContentLoaded', function() {
    const inputFile = document.getElementById('inputFotoRechazo');
    if (inputFile) {
        inputFile.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                mostrarPreviewFotoRechazo(this.files[0]);
            }
        });
    }
});

// Función para subir foto
async function subirFotoRechazo(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const inputFile = document.getElementById('inputFotoRechazo');
    
    // Validar que haya archivo O comentario
    const tieneArchivo = inputFile.files && inputFile.files.length > 0;
    const comentario = formData.get('comentario');
    
    if (!tieneArchivo && !comentario) {
        mostrarNotificacionRechazo('Sube una imagen o escribe un comentario', 'error');
        return;
    }
    
    // Si hay archivo, validar que sea una imagen
    if (tieneArchivo) {
        const file = inputFile.files[0];
        if (!file.type.startsWith('image/')) {
            mostrarNotificacionRechazo('El archivo debe ser una imagen', 'error');
            return;
        }
    }
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarNotificacionRechazo(data.message || 'Guardado correctamente', 'success');
            
            // Remover event listener de paste
            document.removeEventListener('paste', manejarPegadoImagen);
            
            document.getElementById('modalFotoRechazo').close();
            
            // Esperar 2 segundos antes de recargar para que el usuario vea el mensaje
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            mostrarNotificacionRechazo(data.error || 'Error al guardar', 'error');
        }
    } catch (error) {
        mostrarNotificacionRechazo('Error al guardar: ' + error.message, 'error');
    }
}

// AJAX toggle para SR, R e I (sin reload de página)
document.addEventListener('submit', async function(e) {
    const form = e.target;
    if (!form.classList.contains('ajax-toggle')) return;

    e.preventDefault();

    const formData = new FormData(form);
    const csrfToken = formData.get('csrfmiddlewaretoken');

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            }
        });

        const data = await response.json();

        if (data.success) {
            const row = form.closest('tr');
            actualizarFilaToggle(row, data);
            mostrarToastRapido('Actualizado', 'success');
        } else {
            mostrarToastRapido(data.error || 'Error al actualizar', 'error');
        }
    } catch (err) {
        mostrarToastRapido('Error de conexión', 'error');
    }
});

function actualizarFilaToggle(row, data) {
    const srInput = row.querySelector('[name=segunda_revision]');
    const rInput  = row.querySelector('[name=rechazado]');
    const iInput  = row.querySelector('[name=internacion]');

    // Actualizar valores hidden para el próximo clic
    if (srInput) srInput.value = data.segunda_revision ? 'false' : 'true';
    if (rInput)  rInput.value  = data.rechazado         ? 'false' : 'true';
    if (iInput)  iInput.value  = data.internacion       ? 'false' : 'true';

    // Refleja el estado en el botón .ds-toggle-cell: clase is-on-* + aria-pressed.
    // El ícono es estático (ds-icon); el color lo da el CSS del estado, no el JS.
    function pintar(input, onClass, activo) {
        const btn = input?.closest('form')?.querySelector('button');
        if (!btn) return null;
        btn.classList.toggle(onClass, !!activo);
        btn.setAttribute('aria-pressed', activo ? 'true' : 'false');
        return btn;
    }

    pintar(srInput, 'is-on-sr', data.segunda_revision);
    const rBtn = pintar(rInput, 'is-on-r', data.rechazado);
    const iBtn = pintar(iInput, 'is-on-i', data.internacion);

    // R e I dependen de SR: se habilitan solo con SR activo.
    [rBtn, iBtn].forEach((btn) => {
        if (!btn) return;
        btn.disabled = !data.segunda_revision;
        if (data.segunda_revision) {
            btn.removeAttribute('data-ds-tip');
        } else {
            btn.setAttribute('data-ds-tip', 'Requiere SR activo');
        }
    });
}

// Feedback breve de toggles → toast del design system (window.dsToast, definido en base_ds.html)
function mostrarToastRapido(mensaje, tipo = 'success') {
    window.dsToast(mensaje, tipo === 'success' ? 'success' : 'danger', { duration: 1500 });
}

// Notificaciones toast en rechazos → toast del design system
function mostrarNotificacionRechazo(mensaje, tipo = 'success') {
    window.dsToast(mensaje, tipo === 'success' ? 'success' : 'danger', { duration: 4000 });
}

// =====================================================================
// Modal Captura de Tiempos de Atención
// =====================================================================
(function () {
    const modal = document.getElementById('modalTiemposAtencion');
    if (!modal) return;

    const fechaInput = document.getElementById('tiemposFecha');
    const estado = document.getElementById('tiemposEstado');
    const horaInicioInput = modal.querySelector('input[name="hora_inicio"]');
    const horaFinInput = modal.querySelector('input[name="hora_fin"]');
    const URL_PREFIX = window.URL_PREFIX || '';

    function hoyISO() {
        const d = new Date();
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }

    if (fechaInput && !fechaInput.value) {
        fechaInput.value = hoyISO();
    }

    // 'HH:MM' -> minutos desde medianoche (o null si vacío/inválido)
    function aMinutos(hhmm) {
        const m = /^(\d{1,2}):(\d{2})$/.exec((hhmm || '').trim());
        if (!m) return null;
        return Number(m[1]) * 60 + Number(m[2]);
    }

    function formatearDuracion(mins) {
        if (mins == null || mins < 0) return '';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h === 0) return `= ${m}m`;
        if (m === 0) return `= ${h}h`;
        return `= ${h}h ${m}m`;
    }

    // Rubros en orden cronológico (el orden del DOM = orden de tiempos_rubros)
    const rubros = [];
    modal.querySelectorAll('[data-rubro]').forEach((cont) => {
        const key = cont.getAttribute('data-rubro');
        const input = cont.querySelector('[data-hora]');
        const hint = cont.querySelector('[data-hint]');
        if (!input) return;
        input.addEventListener('input', actualizarDuraciones);
        rubros.push({ key, input, hint });
    });

    // Revisiones Secundarias tiene su propia ventana Inicio/Fin.
    const rsInicioInput = modal.querySelector('#rsHoraInicio');
    const rsFinInput = modal.querySelector('#rsHoraFin');
    const rsHint = modal.querySelector('#rsHint');

    // Conteo de personas atendidas en FMA (independiente de las SR).
    const fmaPersonasInput = modal.querySelector('#fmaPersonas');

    function pintarHint(hint, mins) {
        if (!hint) return;
        const texto = (mins == null || mins < 0) ? '' : formatearDuracion(mins);
        hint.textContent = texto || ' ';
        hint.style.color = texto ? '#0f766e' : '';
    }

    // Duración de cada rubro = su hora − Hora Inicio (SIEMPRE desde el inicio,
    // no en cascada). La Hora Fin general no participa en la derivación.
    function actualizarDuraciones() {
        const baseline = aMinutos(horaInicioInput.value);
        rubros.forEach(({ input, hint }) => {
            const val = aMinutos(input.value);
            if (val == null || baseline == null) {
                pintarHint(hint, null);
                return;
            }
            let dur = val - baseline;
            if (dur < 0) dur += 1440; // cruce de medianoche
            pintarHint(hint, dur);
        });

        // Duración de Revisiones Secundarias = RS Fin − RS Inicio.
        const rsIni = aMinutos(rsInicioInput && rsInicioInput.value);
        const rsFin = aMinutos(rsFinInput && rsFinInput.value);
        if (rsIni == null || rsFin == null) {
            pintarHint(rsHint, null);
        } else {
            let dur = rsFin - rsIni;
            if (dur < 0) dur += 1440;
            pintarHint(rsHint, dur);
        }
    }

    horaInicioInput.addEventListener('input', actualizarDuraciones);
    if (rsInicioInput) rsInicioInput.addEventListener('input', actualizarDuraciones);
    if (rsFinInput) rsFinInput.addEventListener('input', actualizarDuraciones);

    // --- Captura en formato 24 h --------------------------------------------
    // El navegador muestra los <input type="time"> en 12 h (AM/PM) según el
    // locale del SO, pero su .value SIEMPRE es "HH:MM" en 24 h. Interceptamos
    // las teclas para que al teclear "22" el campo quede en 22:00 (10 PM).
    function habilitar24h(input) {
        if (!input) return;
        let buffer = '';
        const aplicar = () => {
            if (!buffer) {
                input.value = '';
            } else {
                let h, m;
                if (buffer.length <= 2) { h = parseInt(buffer, 10); m = 0; }
                else { h = parseInt(buffer.slice(0, -2), 10); m = parseInt(buffer.slice(-2), 10); }
                if (h > 23) h = 23;
                if (m > 59) m = 59;
                input.value = String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
            }
            input.dispatchEvent(new Event('input', { bubbles: true }));
        };
        input.addEventListener('focus', () => { buffer = ''; });
        input.addEventListener('keydown', (e) => {
            if (e.key >= '0' && e.key <= '9') {
                e.preventDefault();
                if (buffer.length >= 4) buffer = buffer.slice(1); // desliza al teclear de más
                buffer += e.key;
                aplicar();
            } else if (e.key === 'Backspace' || e.key === 'Delete') {
                e.preventDefault();
                buffer = buffer.slice(0, -1);
                aplicar();
            }
        });
    }

    habilitar24h(horaInicioInput);
    habilitar24h(horaFinInput);
    habilitar24h(rsInicioInput);
    habilitar24h(rsFinInput);
    rubros.forEach(({ input }) => habilitar24h(input));

    function setRubro(key, hhmm) {
        const r = rubros.find((x) => x.key === key);
        if (r) r.input.value = hhmm || '';
    }

    function resetForm() {
        horaInicioInput.value = '';
        horaFinInput.value = '';
        rubros.forEach((r) => { r.input.value = ''; });
        if (rsInicioInput) rsInicioInput.value = '';
        if (rsFinInput) rsFinInput.value = '';
        if (fmaPersonasInput) fmaPersonasInput.value = '';
        actualizarDuraciones();
    }

    function setEstado(tipo, html) {
        if (!estado) return;
        estado.classList.remove('hidden', 'ds-alert-info', 'ds-alert-success', 'ds-alert-warning', 'ds-alert-danger');
        if (tipo === 'nuevo') estado.classList.add('ds-alert-info');
        else if (tipo === 'existe') estado.classList.add('ds-alert-warning');
        else if (tipo === 'error') estado.classList.add('ds-alert-danger');
        estado.innerHTML = html;
    }

    async function cargarTiemposFecha(fecha) {
        if (!fecha) return;
        setEstado('nuevo', 'Cargando...');
        try {
            const resp = await fetch(`${URL_PREFIX}/tiempos-atencion/obtener/${fecha}/`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!resp.ok) throw new Error('Respuesta no valida');
            const data = await resp.json();
            if (data.existe) {
                horaInicioInput.value = data.hora_inicio || '';
                horaFinInput.value = data.hora_fin || '';
                setRubro('fma', data.fma);
                setRubro('mexicanos', data.mexicanos);
                setRubro('extranjeros', data.extranjeros);
                if (fmaPersonasInput) fmaPersonasInput.value = (data.fma_personas ?? '') === '' ? '' : data.fma_personas;
                if (rsInicioInput) rsInicioInput.value = data.rs_hora_inicio || '';
                if (rsFinInput) rsFinInput.value = data.rs_hora_fin || '';
                actualizarDuraciones();
                const meta = data.usuario
                    ? ` (guardado por <b>${data.usuario}</b> el ${data.fecha_modificacion})`
                    : ` (ultima modificacion: ${data.fecha_modificacion})`;
                setEstado('existe', `Editando captura existente${meta}. Al guardar se sobrescribira.`);
            } else {
                resetForm();
                setEstado('nuevo', 'Nueva captura para esta fecha.');
            }
        } catch (e) {
            setEstado('error', 'No se pudieron cargar los datos guardados.');
        }
    }

    if (fechaInput) {
        fechaInput.addEventListener('change', () => cargarTiemposFecha(fechaInput.value));
    }

    function abrirModal() {
        if (fechaInput && !fechaInput.value) fechaInput.value = hoyISO();
        modal.showModal();
        cargarTiemposFecha(fechaInput.value);
    }

    const btnAbrir = document.getElementById('btnAbrirTiempos');
    if (btnAbrir) btnAbrir.addEventListener('click', abrirModal);
})();

/* ====================================================================
   Sincroniza la barra de scroll horizontal superior con la tabla.
   ==================================================================== */
(function () {
    'use strict';
    var top = document.getElementById('tableScrollTop');
    var wrap = document.getElementById('registrosTableWrap');
    if (!top || !wrap) return;
    var spacer = top.firstElementChild;

    function refresh() {
        spacer.style.width = wrap.scrollWidth + 'px';
        // Oculta la barra superior si la tabla no desborda horizontalmente.
        top.hidden = wrap.scrollWidth <= wrap.clientWidth + 1;
    }

    // Reflejo mutuo: comparar antes de asignar evita cualquier bucle de eco.
    top.addEventListener('scroll', function () {
        if (wrap.scrollLeft !== top.scrollLeft) wrap.scrollLeft = top.scrollLeft;
    });
    wrap.addEventListener('scroll', function () {
        if (top.scrollLeft !== wrap.scrollLeft) top.scrollLeft = wrap.scrollLeft;
    });

    refresh();
    window.addEventListener('resize', refresh);
    if (window.ResizeObserver) { new ResizeObserver(refresh).observe(wrap); }
})();