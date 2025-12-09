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
        // Mostrar botón de limpiar
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

// Función de búsqueda en tiempo real (búsqueda del lado del servidor)
searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const searchValue = this.value.trim();
    
    // Mostrar/ocultar botón de limpiar
    if (searchValue) {
        clearSearchBtn.classList.remove('hidden');
    } else {
        clearSearchBtn.classList.add('hidden');
    }
    
    // Esperar 500ms antes de buscar en el servidor (debounce)
    searchTimeout = setTimeout(() => {
        applyFilters();
    }, 500);
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
        editForm.action = '/viajes/update/' + registroId + '/';
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

// Interceptar el formulario de Rechazo para abrir modal de foto
document.addEventListener('DOMContentLoaded', function() {
    // Interceptar todos los botones de "R" (Rechazo)
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        const form = button.closest('form');
        if (form && form.querySelector('input[name="rechazado"]')) {
            form.addEventListener('submit', function(e) {
                const rechazadoInput = this.querySelector('input[name="rechazado"]');
                const nuevoValor = rechazadoInput.value === 'true';
                
                // Si está activando "R", interceptar y abrir modal
                if (nuevoValor) {
                    e.preventDefault();
                    
                    // Primero marcar como rechazado
                    fetch(this.action, {
                        method: 'POST',
                        body: new FormData(this),
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    })
                    .then(response => {
                        if (response.ok) {
                            // Obtener ID del registro desde la URL del form
                            const registroId = this.action.match(/update\/(\d+)\//)[1];
                            
                            // Abrir modal de foto
                            abrirModalFoto(registroId);
                        }
                    });
                }
            });
        }
    });
});

// Función para abrir modal de subida de foto
function abrirModalFoto(registroId) {
    const modal = document.getElementById('modalFotoRechazo');
    const form = document.getElementById('formFotoRechazo');
    const comentarioTextarea = document.getElementById('comentarioRechazo');
    
    // Configurar la acción del formulario con el ID del registro
    form.action = `/camara/subir/${registroId}/`;
    
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
                alert('❌ Formato no permitido. Solo JPG, JPEG, PNG o WEBP.');
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
    
    // Validar que haya un archivo
    if (!inputFile.files || inputFile.files.length === 0) {
        alert('❌ Por favor selecciona o pega una imagen');
        return;
    }
    
    // Validar que sea una imagen
    const file = inputFile.files[0];
    if (!file.type.startsWith('image/')) {
        alert('❌ El archivo debe ser una imagen');
        return;
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
            alert('✅ Foto subida correctamente');
            
            // Remover event listener de paste
            document.removeEventListener('paste', manejarPegadoImagen);
            
            document.getElementById('modalFotoRechazo').close();
            location.reload(); // Recargar para ver el rechazo aplicado
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (error) {
        alert('❌ Error al subir la foto: ' + error);
    }
}