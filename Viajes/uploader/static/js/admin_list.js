// Variables globales
let searchTimeout;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const batchFilter = document.getElementById('batchFilter');
const confirmadoFilter = document.getElementById('confirmadoFilter');
const inadmitidoFilter = document.getElementById('inadmitidoFilter');

// Auto-focus en el buscador si tiene contenido al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    if (searchInput.value.trim()) {
        // Si hay búsqueda activa, hacer focus y mover el cursor al final
        searchInput.focus();
        searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
        clearSearchBtn.classList.remove('hidden');
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
    
    // Confirmado
    if (confirmadoFilter.checked) {
        params.set('confirmado', 'true');
    }
    
    // Inadmitido
    if (inadmitidoFilter.checked) {
        params.set('inadmitido', 'true');
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