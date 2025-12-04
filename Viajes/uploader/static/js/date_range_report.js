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
<strong>Oficina de Representación Baja California</strong>

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

function copiarPin(event) {
    const contenido = document.getElementById('contenidoPin');
    const btnCopiar = event.currentTarget;
    
    // Si el botón ya está deshabilitado, no hacer nada
    if (btnCopiar.disabled) {
        return;
    }
    
    const textoOriginal = btnCopiar.innerHTML;
    
    // Extraer el HTML y convertir <strong> a formato WhatsApp
    let html = contenido.innerHTML;
    
    // Convertir <strong>texto</strong> a *texto* para WhatsApp
    html = html.replace(/<strong>(.*?)<\/strong>/gi, '*$1*');
    
    // Crear un elemento temporal para extraer el texto con los asteriscos
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    let texto = tempDiv.innerText || tempDiv.textContent;
    
    // Crear contenedor con instrucciones
    const container = document.createElement('div');
    container.className = 'space-y-3';
    
    // Agregar alerta con instrucciones
    const alerta = document.createElement('div');
    alerta.className = 'alert alert-warning shadow-lg';
    alerta.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div>
            <h3 class="font-bold text-base">📋 Texto listo para copiar</h3>
            <div class="text-sm mt-1">
                <p>1. El texto ya está seleccionado abajo</p>
                <p>2. Presiona <kbd class="kbd kbd-sm">Ctrl</kbd> + <kbd class="kbd kbd-sm">C</kbd> en tu teclado</p>
                <p>3. Pega donde necesites con <kbd class="kbd kbd-sm">Ctrl</kbd> + <kbd class="kbd kbd-sm">V</kbd></p>
            </div>
        </div>
    `;
    
    // Crear textarea visible con el texto
    const textarea = document.createElement('textarea');
    textarea.value = texto;
    textarea.className = 'textarea textarea-bordered w-full h-64 font-mono text-sm';
    textarea.readOnly = true;
    
    // Agregar elementos al contenedor
    container.appendChild(alerta);
    container.appendChild(textarea);
    
    // Limpiar y agregar el contenedor
    contenido.innerHTML = '';
    contenido.appendChild(container);
    
    // Seleccionar todo el texto automáticamente
    textarea.select();
    textarea.focus();
    
    // Detectar cuando el usuario copie con Ctrl+C
    let copiado = false;
    textarea.addEventListener('copy', function() {
        if (!copiado) {
            copiado = true;
            
            // Cambiar la alerta a éxito
            alerta.className = 'alert alert-success shadow-lg';
            alerta.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                    <h3 class="font-bold text-base">✅ ¡Texto copiado exitosamente!</h3>
                    <div class="text-sm mt-1">
                        <p>Ahora puedes pegarlo donde lo necesites con <kbd class="kbd kbd-sm">Ctrl</kbd> + <kbd class="kbd kbd-sm">V</kbd></p>
                        <p class="text-xs mt-1 opacity-70">Esta ventana se cerrará en 2 segundos...</p>
                    </div>
                </div>
            `;
            
            // Cambiar el botón a éxito
            btnCopiar.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> ¡Copiado!';
            
            // Cerrar el modal automáticamente después de 2 segundos
            setTimeout(() => {
                const modal = document.getElementById('modalPin');
                modal.close();
                // Recargar la página para resetear el estado del modal
                location.reload();
            }, 2000);
        }
    });
    
    // Cambiar el botón inicial
    btnCopiar.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg> Esperando copia...';
    btnCopiar.classList.remove('btn-primary');
    btnCopiar.classList.add('btn-warning');
    btnCopiar.disabled = true;
    btnCopiar.style.cursor = 'not-allowed';
}

function copiarConTextarea(texto, btnCopiar, textoOriginal) {
    console.log('Usando método textarea...'); // Debug
    
    // Crear textarea temporal
    const textarea = document.createElement('textarea');
    textarea.value = texto;
    
    // Estilo para asegurar que funcione
    textarea.style.position = 'fixed';
    textarea.style.top = '50%';
    textarea.style.left = '50%';
    textarea.style.width = '2em';
    textarea.style.height = '2em';
    textarea.style.padding = '0';
    textarea.style.border = 'none';
    textarea.style.outline = 'none';
    textarea.style.boxShadow = 'none';
    textarea.style.background = 'transparent';
    
    document.body.appendChild(textarea);
    
    // Seleccionar el texto
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, 99999); // Para móviles
    
    try {
        // Copiar
        const exitoso = document.execCommand('copy');
        console.log('Resultado execCommand:', exitoso); // Debug
        
        if (exitoso) {
            mostrarExito(btnCopiar, textoOriginal);
        } else {
            alert('No se pudo copiar. Por favor, selecciona el texto y presiona Ctrl+C manualmente.');
        }
    } catch (err) {
        console.error('Error al copiar:', err);
        alert('Error al copiar: ' + err.message);
    } finally {
        // Limpiar después de un pequeño delay
        setTimeout(() => {
            document.body.removeChild(textarea);
        }, 100);
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