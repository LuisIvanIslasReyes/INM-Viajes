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
// Variable global para guardar los datos del PIN
let pinData = null;

async function abrirModalPin(fecha, fechaTexto, totalPasajeros, totalSR, totalInternaciones, totalRechazos) {
    const modal = document.getElementById('modalPin');
    const contenido = document.getElementById('contenidoPin');
    
    // Mostrar loading
    contenido.innerHTML = '<div class="text-center"><span class="loading loading-spinner loading-lg"></span></div>';
    modal.showModal();
    
    try {
        // Hacer petición para obtener datos completos
        // Usar prefijo de URL dinámico (vacío en dev, /viajes en prod)
        const urlPrefix = window.URL_PREFIX || '';
        const url = `${urlPrefix}/pin/${fecha}/`;
        console.log('Solicitando PIN desde:', url);
        
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        // Verificar si la respuesta es correcta
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                throw new Error('Sesión expirada. Por favor, recarga la página e inicia sesión nuevamente.');
            }
            if (response.status === 502 || response.status === 503) {
                throw new Error('El servidor está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos.');
            }
            if (response.status === 404) {
                throw new Error('No se encontraron registros para esta fecha.');
            }
            if (response.status === 500) {
                throw new Error('Error interno del servidor. Por favor, contacta al administrador.');
            }
            throw new Error(`Error del servidor (${response.status}). Por favor, intenta de nuevo.`);
        }
        
        // Verificar que la respuesta sea JSON ANTES de intentar parsear
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Si no es JSON, probablemente es una página de error HTML
            const text = await response.text();
            if (text.includes('<!DOCTYPE') || text.includes('<html')) {
                throw new Error('El servidor devolvió una página de error. Por favor, verifica que el servidor Django esté corriendo.');
            }
            throw new Error('La respuesta del servidor no es válida. Posiblemente el servidor se reinició. Por favor, recarga la página.');
        }
        
        // Intentar parsear JSON de forma segura
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Error al parsear JSON:', jsonError);
            throw new Error('Error al procesar la respuesta del servidor. El servidor puede estar reiniciándose.');
        }
        
        // Validar que tenemos los datos necesarios
        if (!data || typeof data.vuelo_numero === 'undefined') {
            throw new Error('Datos incompletos recibidos del servidor.');
        }
        
        // Guardar datos globalmente para el PDF (incluyendo fechaTexto formateada)
        pinData = {
            fechaTexto: fechaTexto,
            ...data
        };
        
        // Generar el contenido del PIN
        let pinTexto = `<strong>INSTITUTO NACIONAL DE MIGRACIÓN</strong>
<strong>Oficina de Representación Baja California</strong>

<strong>${fechaTexto.toUpperCase()}</strong>

Por este medio se informa que el día de la fecha arribó al Aeropuerto Internacional de Tijuana el vuelo <strong>${data.vuelo_numero}</strong> proveniente de Pekín con <strong>${data.total_pasajeros} pasajeros</strong>.

`;

        // Siempre mostrar el número de segundas revisiones
        pinTexto += `En dicho proceso migratorio se llevó a cabo <strong>${String(data.total_sr).padStart(2, '0')} segunda${data.total_sr != 1 ? 's' : ''} revisión${data.total_sr != 1 ? 'es' : ''}</strong>`;
        
        if (data.total_sr > 0) {
            pinTexto += `, las cuales, derivaron en:\n`;
            
            if (data.total_internaciones > 0) {
                pinTexto += `${String(data.total_internaciones).padStart(2, '0')} internación${data.total_internaciones != 1 ? 'es' : ''} por entrevista.\n`;
            }
            
            if (data.total_rechazos > 0) {
                pinTexto += `${String(data.total_rechazos).padStart(2, '0')} rechazo${data.total_rechazos != 1 ? 's' : ''} por entrevista.\n`;
            }
            pinTexto += '\n';
        } else {
            pinTexto += `.\n\n`;
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
        
        // Mostrar mensaje de error detallado
        contenido.innerHTML = `
            <div class="alert alert-error shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                    <h3 class="font-bold">Error al cargar el PIN</h3>
                    <div class="text-sm">${error.message}</div>
                </div>
            </div>
            <div class="mt-4 text-center">
                <button onclick="location.reload()" class="btn btn-primary btn-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Recargar Página
                </button>
            </div>
        `;
    }
}

function cerrarModalPin() {
    document.getElementById('modalPin').close();
}

// Función para copiar PIN (con ** para negritas de WhatsApp)
async function copiarPin(event) {
    event.preventDefault();
    
    if (!pinData) {
        alert('❌ No hay datos del PIN disponibles');
        return;
    }
    
    try {
        // Generar texto con * para WhatsApp
        let texto = `*INSTITUTO NACIONAL DE MIGRACIÓN*\n*Oficina de Representación Baja California*\n\n`;
        texto += `*${pinData.fechaTexto.toUpperCase()}*\n\n`;
        texto += `Por este medio se informa que el día de la fecha arribó al Aeropuerto Internacional de Tijuana el vuelo *${pinData.vuelo_numero}* proveniente de Pekín con *${pinData.total_pasajeros} pasajeros*.\n\n`;
        
        // Siempre mostrar el número de segundas revisiones
        texto += `En dicho proceso migratorio se llevó a cabo *${String(pinData.total_sr).padStart(2, '0')} segunda${pinData.total_sr != 1 ? 's' : ''} revisión${pinData.total_sr != 1 ? 'es' : ''}*`;
        
        if (pinData.total_sr > 0) {
            texto += `, las cuales, derivaron en:\n`;
            
            if (pinData.total_internaciones > 0) {
                texto += `${String(pinData.total_internaciones).padStart(2, '0')} internación${pinData.total_internaciones != 1 ? 'es' : ''} por entrevista.\n`;
            }
            
            if (pinData.total_rechazos > 0) {
                texto += `${String(pinData.total_rechazos).padStart(2, '0')} rechazo${pinData.total_rechazos != 1 ? 's' : ''} por entrevista.\n`;
            }
            texto += '\n';
        } else {
            texto += `.\n\n`;
        }
        
        // Detalles de rechazos
        if (pinData.rechazados_detalle && pinData.rechazados_detalle.length > 0) {
            texto += `*RECHAZO${pinData.total_rechazos != 1 ? 'S' : ''}*\n`;
            pinData.rechazados_detalle.forEach((rechazado, index) => {
                texto += `${index + 1}. NOMBRE: ${rechazado.nombre.toUpperCase()}\n`;
                texto += `   GÉNERO: ${rechazado.genero}\n`;
                texto += `   NACIONALIDAD: ${rechazado.nacionalidad.toUpperCase()}\n`;
                texto += `   N. PASAPORTE: ${rechazado.pasaporte}\n`;
                texto += `   FDN: ${rechazado.fecha_nacimiento}\n\n`;
            });
        }
        
        texto += `Cabe resaltar que los procesos mencionados fueron en apego a Derechos Humanos.\n\n`;
        texto += `*Conexiones: ${pinData.total_conexiones}*\n\n`;
        texto += `Sin otro particular, se envía un cordial saludo.`;
        
        // Copiar al portapapeles
        await navigator.clipboard.writeText(texto);
        
        // Mostrar notificación toast
        mostrarNotificacion('✅ Texto copiado', 'success');
        
    } catch (err) {
        console.error('Error al copiar:', err);
        mostrarNotificacion('❌ Error al copiar', 'error');
    }
}

// Función para mostrar notificaciones toast
function mostrarNotificacion(mensaje, tipo = 'success') {
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
    
    // Remover la notificación después de 2 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 500);
    }, 2000);
}

function mostrarNotificacionExito() {
    // Crear notificación toast
    const toast = document.createElement('div');
    toast.className = 'alert alert-success shadow-lg fixed top-4 right-4 w-auto z-50 animate-bounce';
    toast.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span><strong>¡PIN copiado al portapapeles!</strong></span>
    `;
    
    document.body.appendChild(toast);
    
    // Remover la notificación después de 3 segundos
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 500);
    }, 3000);
}

function mostrarModalCopiaManual(texto) {
    const contenido = document.getElementById('contenidoPin');
    
    const container = document.createElement('div');
    container.className = 'space-y-3';
    
    const alerta = document.createElement('div');
    alerta.className = 'alert alert-warning shadow-lg';
    alerta.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
            <h3 class="font-bold text-base">⚠️ Copia manual necesaria</h3>
            <div class="text-sm mt-1">
                <p>Por favor, selecciona el texto abajo y presiona <kbd class="kbd kbd-sm">Ctrl</kbd> + <kbd class="kbd kbd-sm">C</kbd></p>
            </div>
        </div>
    `;
    
    const textarea = document.createElement('textarea');
    textarea.value = texto;
    textarea.className = 'textarea textarea-bordered w-full h-64 font-mono text-sm';
    textarea.readOnly = true;
    
    container.appendChild(alerta);
    container.appendChild(textarea);
    
    contenido.innerHTML = '';
    contenido.appendChild(container);
    
    textarea.select();
    textarea.focus();
}

// Función para generar PDF con PIN e imágenes
async function generarPDF() {
    if (!pinData) {
        alert('❌ No hay datos del PIN disponibles');
        return;
    }
    
    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        let y = 20;
        const margen = 20;
        const anchoMaximo = 170;
        
        // Función auxiliar para agregar texto con negritas
        const agregarTexto = (texto, isBold = false) => {
            doc.setFont('helvetica', isBold ? 'bold' : 'normal');
            const lineas = doc.splitTextToSize(texto, anchoMaximo);
            lineas.forEach(linea => {
                if (y > 270) {
                    doc.addPage();
                    y = 20;
                }
                doc.text(linea, margen, y);
                y += 7;
            });
        };
        
        // PÁGINA 1: Texto del PIN
        agregarTexto('INSTITUTO NACIONAL DE MIGRACIÓN', true);
        agregarTexto('Oficina de Representación Baja California', true);
        y += 5;
        
        agregarTexto(pinData.fechaTexto.toUpperCase(), true);
        y += 5;
        
        agregarTexto(`Por este medio se informa que el día de la fecha arribó al Aeropuerto Internacional de Tijuana el vuelo ${pinData.vuelo_numero} proveniente de Pekín con ${pinData.total_pasajeros} pasajeros.`);
        y += 3;
        
        // Siempre mostrar el número de segundas revisiones
        if (pinData.total_sr > 0) {
            agregarTexto(`En dicho proceso migratorio se llevó a cabo ${String(pinData.total_sr).padStart(2, '0')} segunda${pinData.total_sr != 1 ? 's' : ''} revisión${pinData.total_sr != 1 ? 'es' : ''}, las cuales, derivaron en:`);
            
            if (pinData.total_internaciones > 0) {
                agregarTexto(`${String(pinData.total_internaciones).padStart(2, '0')} internación${pinData.total_internaciones != 1 ? 'es' : ''} por entrevista.`);
            }
            
            if (pinData.total_rechazos > 0) {
                agregarTexto(`${String(pinData.total_rechazos).padStart(2, '0')} rechazo${pinData.total_rechazos != 1 ? 's' : ''} por entrevista.`);
            }
            y += 3;
        } else {
            agregarTexto(`En dicho proceso migratorio se llevó a cabo ${String(pinData.total_sr).padStart(2, '0')} segundas revisiones.`);
            y += 3;
        }
        
        // Detalles de rechazos
        if (pinData.rechazados_detalle && pinData.rechazados_detalle.length > 0) {
            agregarTexto(`RECHAZO${pinData.total_rechazos != 1 ? 'S' : ''}`, true);
            y += 3;
            
            pinData.rechazados_detalle.forEach((rechazado, index) => {
                agregarTexto(`${index + 1}. NOMBRE: ${rechazado.nombre.toUpperCase()}`);
                agregarTexto(`   GÉNERO: ${rechazado.genero}`);
                agregarTexto(`   NACIONALIDAD: ${rechazado.nacionalidad.toUpperCase()}`);
                agregarTexto(`   N. PASAPORTE: ${rechazado.pasaporte}`);
                agregarTexto(`   FDN: ${rechazado.fecha_nacimiento}`);
                y += 3;
            });
        }
        
        agregarTexto('Cabe resaltar que los procesos mencionados fueron en apego a Derechos Humanos.');
        y += 5;
        
        agregarTexto(`Conexiones: ${pinData.total_conexiones}`, true);
        y += 5;
        
        agregarTexto('Sin otro particular, se envía un cordial saludo.');
        
        // PÁGINA 2: Imágenes de rechazos (si las hay)
        if (pinData.rechazados_detalle && pinData.rechazados_detalle.length > 0) {
            const fotosPromesas = [];
            
            pinData.rechazados_detalle.forEach(rechazado => {
                if (rechazado.fotos && rechazado.fotos.length > 0) {
                    rechazado.fotos.forEach(fotoUrl => {
                        fotosPromesas.push(
                            fetch(fotoUrl)
                                .then(res => res.blob())
                                .then(blob => {
                                    return new Promise((resolve) => {
                                        const reader = new FileReader();
                                        reader.onloadend = () => resolve({
                                            data: reader.result,
                                            nombre: rechazado.nombre
                                        });
                                        reader.readAsDataURL(blob);
                                    });
                                })
                        );
                    });
                }
            });
            
            if (fotosPromesas.length > 0) {
                const fotos = await Promise.all(fotosPromesas);
                
                if (fotos.length > 0) {
                    doc.addPage();
                    y = 20;
                    
                    doc.setFont('helvetica', 'bold');
                    doc.text('FOTOGRAFÍAS DE RECHAZOS', margen, y);
                    y += 15;
                    
                    fotos.forEach((foto, index) => {
                        if (y > 200) {
                            doc.addPage();
                            y = 20;
                        }
                        
                        doc.setFont('helvetica', 'normal');
                        doc.text(`Rechazo ${index + 1}: ${foto.nombre}`, margen, y);
                        y += 10;
                        
                        // Agregar imagen (ajustar tamaño para que quepa)
                        try {
                            doc.addImage(foto.data, 'JPEG', margen, y, 170, 100);
                            y += 110;
                        } catch (e) {
                            console.error('Error al agregar imagen:', e);
                            doc.text('Error al cargar imagen', margen, y);
                            y += 10;
                        }
                    });
                }
            }
        }
        
        // Descargar PDF
        const nombreArchivo = `PIN_${pinData.fechaTexto.replace(/\s+/g, '_').replace(/,/g, '')}.pdf`;
        doc.save(nombreArchivo);
        
        alert('✅ PDF generado correctamente');
        
    } catch (error) {
        console.error('Error al generar PDF:', error);
        alert('❌ Error al generar el PDF: ' + error.message);
    }
}
