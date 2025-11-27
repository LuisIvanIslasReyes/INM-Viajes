// Variables globales
let searchTimeout;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const batchFilter = document.getElementById('batchFilter');
const confirmadoFilter = document.getElementById('confirmadoFilter');
const inadmitidoFilter = document.getElementById('inadmitidoFilter');
const puntoInternacionFilter = document.getElementById('puntoInternacionFilter');

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

if (confirmadoFilter) {
    confirmadoFilter.addEventListener('change', applyFilters);
}

if (inadmitidoFilter) {
    inadmitidoFilter.addEventListener('change', applyFilters);
}

if (puntoInternacionFilter) {
    puntoInternacionFilter.addEventListener('change', applyFilters);
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
    if (confirmadoFilter.checked) {
        params.set('confirmado', 'true');
    }
    
    // Rechazo (R)
    if (inadmitidoFilter.checked) {
        params.set('inadmitido', 'true');
    }
    
    // Punto de Internación (PI)
    if (puntoInternacionFilter.checked) {
        params.set('punto_internacion', 'true');
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
        editForm.action = '/update/' + registroId + '/';
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