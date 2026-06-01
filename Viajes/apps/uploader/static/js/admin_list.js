// Variables globales
let searchTimeout;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const batchFilter = document.getElementById('batchFilter');
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
                    
                    // Efecto visual temporal (flash amarillo)
                    registroElement.classList.add('bg-warning', 'bg-opacity-20');
                    setTimeout(() => {
                        registroElement.classList.remove('bg-warning', 'bg-opacity-20');
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

// Aplicar filtros cuando cambien
if (batchFilter) {
    batchFilter.addEventListener('change', applyFilters);
}

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
    
    // Batch
    if (batchFilter.value) {
        params.set('batch', batchFilter.value);
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

    // SR
    const srBtn = srInput?.closest('form')?.querySelector('button');
    if (srBtn) srBtn.innerHTML = svgSR(data.segunda_revision);

    // R
    const rBtn = rInput?.closest('form')?.querySelector('button');
    if (rBtn) {
        rBtn.disabled = !data.segunda_revision;
        rBtn.innerHTML = svgR(data.rechazado);
    }

    // I
    const iBtn = iInput?.closest('form')?.querySelector('button');
    if (iBtn) {
        iBtn.disabled = !data.segunda_revision;
        iBtn.innerHTML = svgI(data.internacion, data.segunda_revision);
    }
}

function svgSR(activo) {
    const color = activo ? 'text-success' : 'text-gray-300';
    const sw    = activo ? '2.5' : '2';
    return `<svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 ${color}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="${sw}"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
}

function svgR(activo) {
    const color = activo ? 'text-error' : 'text-gray-300';
    const sw    = activo ? '2.5' : '2';
    return `<svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 ${color}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="${sw}"><path stroke-linecap="round" stroke-linejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;
}

function svgI(activo, srActivo) {
    const color = activo ? 'text-info' : (srActivo ? 'text-gray-400' : 'text-gray-200');
    const sw    = activo ? '2.5' : '2';
    return `<svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 ${color}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="${sw}"><path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>`;
}

function mostrarToastRapido(mensaje, tipo = 'success') {
    document.querySelectorAll('.toast-rapido').forEach(t => t.remove());
    const toast = document.createElement('div');
    const bg    = tipo === 'success' ? 'alert-success' : 'alert-error';
    toast.className = `toast-rapido alert ${bg} shadow-lg fixed top-4 right-4 w-auto z-50 py-2 px-4`;
    toast.style.transition = 'opacity 0.3s';
    toast.innerHTML = `<span>${mensaje}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 1500);
}

// Función para mostrar notificaciones toast en rechazos
function mostrarNotificacionRechazo(mensaje, tipo = 'success') {
    const toast = document.createElement('div');
    const bgColor = tipo === 'success' ? 'alert-success' : 'alert-error';
    
    toast.className = `alert ${bgColor} shadow-lg fixed top-4 right-4 w-auto animate-fade-in`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            ${tipo === 'success' 
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
                : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />'
            }
        </svg>
        <span>${mensaje}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Remover la notificación después de 4 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 500);
    }, 4000);
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

    // Duración derivada de cada rubro = su hora − el hito anterior, encadenando
    // desde Hora Inicio. La Hora Fin no participa en la derivación.
    function actualizarDuraciones() {
        let baseline = aMinutos(horaInicioInput.value);
        rubros.forEach(({ input, hint }) => {
            if (!hint) return;
            const val = aMinutos(input.value);
            if (val == null || baseline == null) {
                hint.textContent = ' ';
                hint.style.color = '';
                return;
            }
            let dur = val - baseline;
            if (dur < 0) dur += 1440; // cruce de medianoche
            const texto = formatearDuracion(dur);
            hint.textContent = texto || ' ';
            hint.style.color = texto ? '#0f766e' : '';
            baseline = val;
        });
    }

    horaInicioInput.addEventListener('input', actualizarDuraciones);

    function setRubro(key, hhmm) {
        const r = rubros.find((x) => x.key === key);
        if (r) r.input.value = hhmm || '';
    }

    function resetForm() {
        horaInicioInput.value = '';
        horaFinInput.value = '';
        rubros.forEach((r) => { r.input.value = ''; });
        actualizarDuraciones();
    }

    function setEstado(tipo, html) {
        if (!estado) return;
        estado.classList.remove('hidden', 'alert-info', 'alert-success', 'alert-warning', 'alert-error');
        if (tipo === 'nuevo') estado.classList.add('alert-info');
        else if (tipo === 'existe') estado.classList.add('alert-warning');
        else if (tipo === 'error') estado.classList.add('alert-error');
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
                setRubro('revisiones_secundarias', data.revisiones_secundarias);
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