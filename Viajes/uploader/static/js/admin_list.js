// Variables globales
let searchTimeout;
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const batchFilter = document.getElementById('batchFilter');
const confirmadoFilter = document.getElementById('confirmadoFilter');
const inadmitidoFilter = document.getElementById('inadmitidoFilter');

// Función de búsqueda en tiempo real
searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const searchValue = this.value.trim();
    
    // Mostrar/ocultar botón de limpiar
    if (searchValue) {
        clearSearchBtn.classList.remove('hidden');
    } else {
        clearSearchBtn.classList.add('hidden');
    }
    
    // Esperar 300ms antes de filtrar (debounce)
    searchTimeout = setTimeout(() => {
        if (searchValue.length > 0) {
            filterTable(searchValue);
        } else {
            showAllRows();
        }
    }, 300);
});

// Función para filtrar la tabla
function filterTable(searchValue) {
    const rows = document.querySelectorAll('#registrosTable tbody tr:not(#noResults)');
    let visibleCount = 0;
    
    searchValue = searchValue.toLowerCase();
    
    rows.forEach(row => {
        const documento = row.getAttribute('data-documento') ? row.getAttribute('data-documento').toLowerCase() : '';
        const pasajero = row.getAttribute('data-pasajero') ? row.getAttribute('data-pasajero').toLowerCase() : '';
        
        if (documento.includes(searchValue) || pasajero.includes(searchValue)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Actualizar contador
    const totalRegistros = document.getElementById('total-registros');
    if (totalRegistros) {
        totalRegistros.textContent = visibleCount;
    }
    
    // Mostrar mensaje si no hay resultados
    const noResults = document.getElementById('noResults');
    if (visibleCount === 0 && noResults) {
        noResults.style.display = '';
    } else if (noResults) {
        noResults.style.display = 'none';
    }
}

// Mostrar todas las filas
function showAllRows() {
    const rows = document.querySelectorAll('#registrosTable tbody tr:not(#noResults)');
    rows.forEach(row => row.style.display = '');
    
    const totalRegistros = document.getElementById('total-registros');
    if (totalRegistros) {
        totalRegistros.textContent = rows.length;
    }
    
    const noResults = document.getElementById('noResults');
    if (noResults) {
        noResults.style.display = 'none';
    }
}

// Limpiar búsqueda
function clearSearchFilter() {
    searchInput.value = '';
    clearSearchBtn.classList.add('hidden');
    showAllRows();
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
    const params = new URLSearchParams(window.location.search);
    
    // Batch
    if (batchFilter.value) {
        params.set('batch', batchFilter.value);
    } else {
        params.delete('batch');
    }
    
    // Confirmado
    if (confirmadoFilter.checked) {
        params.set('confirmado', 'true');
    } else {
        params.delete('confirmado');
    }
    
    // Inadmitido
    if (inadmitidoFilter.checked) {
        params.set('inadmitido', 'true');
    } else {
        params.delete('inadmitido');
    }
    
    // Mantener búsqueda
    if (searchInput.value) {
        params.set('search', searchInput.value);
    }
    
    // Redirigir con los nuevos filtros
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