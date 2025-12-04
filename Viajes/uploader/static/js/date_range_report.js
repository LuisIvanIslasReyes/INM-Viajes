document.addEventListener('DOMContentLoaded', function() {
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    const minDate = '2025-11-10';

    // Validar que las fechas no sean anteriores al mínimo
    function validateMinDate(input) {
        if (input.value && input.value < minDate) {
            input.value = minDate;
            alert('La fecha no puede ser anterior al 10 de noviembre de 2025');
        }
    }

    // Validar que fecha_fin no sea anterior a fecha_inicio
    function validateRange() {
        if (fechaInicio.value && fechaFin.value && fechaFin.value < fechaInicio.value) {
            alert('La fecha de fin no puede ser anterior a la fecha de inicio');
            fechaFin.value = fechaInicio.value;
        }
    }

    if (fechaInicio) {
        fechaInicio.addEventListener('change', function() {
            validateMinDate(this);
            validateRange();
        });
    }

    if (fechaFin) {
        fechaFin.addEventListener('change', function() {
            validateMinDate(this);
            validateRange();
        });
    }
});

// Función para colapsar/expandir fechas
function toggleFecha(header) {
    const grupo = header.closest('.fecha-grupo');
    const content = grupo.querySelector('.fecha-content');
    const toggle = header.querySelector('.fecha-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        toggle.style.transform = 'rotate(-90deg)';
    }
}

// Función para colapsar/expandir filtros
function toggleFiltros() {
    const content = document.getElementById('filtros-content');
    const toggle = document.getElementById('filtros-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        toggle.style.transform = 'rotate(-90deg)';
    }
}


// Función para abrir el modal del PIN
async function abrirModalPin(fecha, fechaTexto, totalPasajeros, totalSR, totalInternaciones, totalRechazos) {
    const modal = document.getElementById('modalPin');
    const contenido = document.getElementById('contenidoPin');
    
    // Mostrar loading
    contenido.innerHTML = '<div class="text-center"><span class="loading loading-spinner loading-lg"></span></div>';
    modal.showModal();
    
    try {
        // Hacer petición para obtener datos completos
        const response = await fetch(`/pin/${fecha}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        // Generar el contenido del PIN
        let pinTexto = `<strong>INSTITUTO NACIONAL DE MIGRACIÓN</strong>
Oficina de Representación Baja California

<strong>${fechaTexto.toUpperCase()}</strong>

Por este medio se informa que el día de la fecha arribó al Aeropuerto Internacional de Tijuana el vuelo <strong>${data.vuelo_numero}</strong> proveniente de Pekín con <strong>${data.total_pasajeros} pasajeros</strong>.

`;

        if (data.total_sr > 0) {
            pinTexto += `En dicho proceso migratorio se llevó a cabo <strong>${String(data.total_sr).padStart(2, '0')} segunda${data.total_sr != 1 ? 's' : ''} revisión${data.total_sr != 1 ? 'es' : ''}</strong>, las cuales, derivaron en:\n`;
            
            if (data.total_internaciones > 0) {
                pinTexto += `${String(data.total_internaciones).padStart(2, '0')} internación${data.total_internaciones != 1 ? 'es' : ''} por entrevista.\n`;
            }
            
            if (data.total_rechazos > 0) {
                pinTexto += `${String(data.total_rechazos).padStart(2, '0')} rechazo${data.total_rechazos != 1 ? 's' : ''} por entrevista.\n`;
            }
            pinTexto += '\n';
        } else {
            pinTexto += `En dicho proceso migratorio no se llevó a cabo ninguna segunda revisión.\n\n`;
        }
        
        // Detalles de rechazos
        if (data.rechazados_detalle && data.rechazados_detalle.length > 0) {
            pinTexto += `<strong>RECHAZO${data.total_rechazos != 1 ? 'S' : ''}</strong>\n`;
            data.rechazados_detalle.forEach((rechazado, index) => {
                pinTexto += `${index + 1}. NOMBRE: ${rechazado.nombre.toUpperCase()}
   GÉNERO: ${rechazado.genero}
   NACIONALIDAD: ${rechazado.nacionalidad.toUpperCase()}
   N. PASAPORTE: ${rechazado.pasaporte}
   FDN: ${rechazado.fecha_nacimiento}\n\n`;
            });
        }
        
        pinTexto += `Cabe resaltar que los procesos mencionados fueron en apego a Derechos Humanos.

<strong>Conexiones: ${data.total_conexiones}</strong>

Sin otro particular, se envía un cordial saludo.`;
        
        // Reemplazar saltos de línea con <br> y mantener el formato
        contenido.innerHTML = `<div style="white-space: pre-wrap;">${pinTexto}</div>`;
        
    } catch (error) {
        console.error('Error al cargar el PIN:', error);
        contenido.innerHTML = '<div class="alert alert-error">Error al cargar el PIN. Intenta de nuevo.</div>';
    }
}

function cerrarModalPin() {
    document.getElementById('modalPin').close();
}

async function copiarPin() {
    const contenido = document.getElementById('contenidoPin');
    const btnCopiar = event.target.closest('button');
    const textoOriginal = btnCopiar.innerHTML;
    
    // Extraer el texto sin las etiquetas HTML pero manteniendo formato
    const textoTemporal = document.createElement('div');
    textoTemporal.innerHTML = contenido.innerHTML;
    let texto = textoTemporal.innerText || textoTemporal.textContent;
    
    // Método 1: Intentar con Clipboard API moderna
    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(texto);
            mostrarExito(btnCopiar, textoOriginal);
            return;
        } catch (err) {
            console.log('Clipboard API falló, intentando método alternativo...');
        }
    }
    
    // Método 2: Usar textarea temporal (método clásico)
    const textarea = document.createElement('textarea');
    textarea.value = texto;
    textarea.style.position = 'fixed';
    textarea.style.left = '-999999px';
    textarea.style.top = '-999999px';
    document.body.appendChild(textarea);
    
    try {
        textarea.focus();
        textarea.select();
        
        const exitoso = document.execCommand('copy');
        document.body.removeChild(textarea);
        
        if (exitoso) {
            mostrarExito(btnCopiar, textoOriginal);
        } else {
            throw new Error('execCommand falló');
        }
    } catch (err) {
        console.error('Error al copiar:', err);
        document.body.removeChild(textarea);
        
        // Método 3: Seleccionar el contenido directamente
        const range = document.createRange();
        range.selectNodeContents(contenido);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        
        alert('El texto ha sido seleccionado. Por favor presiona Ctrl+C (o Cmd+C en Mac) para copiar.');
    }
}

function mostrarExito(btnCopiar, textoOriginal) {
    btnCopiar.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> ¡Copiado!';
    btnCopiar.classList.add('btn-success');
    
    setTimeout(() => {
        btnCopiar.innerHTML = textoOriginal;
        btnCopiar.classList.remove('btn-success');
    }, 2000);
}
