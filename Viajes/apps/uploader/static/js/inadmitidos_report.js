/* Reporte de Inadmitidos */

const COLORES = {
    rojo: '#700606',
    rosa: '#FED8D8',
    gris: '#DDDDDD',
    blanco: '#F3F3F2',
    blanco_puro: '#FFFFFF',
};

let reporteData = null;

function hoy() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const finInput = document.getElementById('fecha_fin');
    if (!finInput.value) finInput.value = hoy();
});

/* --- Generar reporte (tabla HTML preview) --- */

async function generarReporte() {
    const inicio = document.getElementById('fecha_inicio').value;
    const fin = document.getElementById('fecha_fin').value;

    if (!inicio || !fin) { mostrarError('Selecciona ambas fechas.'); return; }
    if (fin < inicio) { mostrarError('La fecha fin debe ser mayor o igual a la fecha inicio.'); return; }

    ocultarError();
    mostrarSpinner(true);
    document.getElementById('tabla-preview').classList.add('hidden');
    document.getElementById('btn-pdf').classList.add('hidden');

    const url = `${window.INADMITIDOS_DATA_URL}?fecha_inicio=${inicio}&fecha_fin=${fin}`;

    try {
        const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!resp.ok) {
            const d = await resp.json().catch(() => ({}));
            throw new Error(d.error || `Error ${resp.status}`);
        }
        reporteData = await resp.json();
        renderTabla(reporteData);
        document.getElementById('btn-pdf').classList.remove('hidden');
    } catch (e) {
        mostrarError(e.message || 'Error al obtener los datos.');
    } finally {
        mostrarSpinner(false);
    }
}

/* --- Renderizar tabla de previsualización --- */

function renderTabla(data) {
    const tabla = document.getElementById('tabla-inadmitidos');
    const n = data.dates.length;
    const nats = Object.keys(data.nationalities);

    let html = '<tbody>';

    // Fila Vuelo/Origen — proporciones tipo Img1: label / valor / label / valor
    html += `<tr class="row-vuelo">
        <td class="col-label">Vuelo:</td>
        <td colspan="${Math.max(Math.floor(n / 2), 1)}">${data.vuelo}</td>
        <td>Origen:</td>
        <td colspan="${Math.max(n - Math.floor(n / 2) - 1, 1)}">${data.origen}</td>
    </tr>`;

    // INADMITIDOS
    html += `<tr class="row-title"><td colspan="${n + 1}">INADMITIDOS</td></tr>`;

    // Días de la semana (vacío + nombres)
    const dias = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
    html += `<tr class="row-dias"><td class="col-label"></td>`;
    for (const rd of data.raw_dates) {
        const d = new Date(rd + 'T00:00:00');
        html += `<td>${dias[d.getDay()]}</td>`;
    }
    html += '</tr>';

    // Nacionalidad + fechas
    html += `<tr class="row-header-nac"><td class="col-label">Nacionalidad</td>`;
    for (const fecha of data.dates) {
        html += `<td>${fecha}</td>`;
    }
    html += '</tr>';

    // Filas de nacionalidades (alternadas)
    nats.forEach((nat, idx) => {
        const altClass = idx % 2 === 1 ? ' row-alt' : '';
        html += `<tr class="row-nac${altClass}"><td class="col-label">${nat}</td>`;
        for (let d = 0; d < n; d++) html += `<td>${data.nationalities[nat][d] ?? 0}</td>`;
        html += '</tr>';
    });

    // 2 filas vacías (separador antes del total)
    const tdSep = `<td></td>`;
    for (let k = 0; k < 2; k++) {
        html += `<tr class="row-sep">${tdSep.repeat(n + 1)}</tr>`;
    }

    // Total Inadmitidos
    html += `<tr class="row-total-inad"><td class="col-label">Total Inadmitidos</td>`;
    for (const v of data.totals_inadmitidos) html += `<td>${v}</td>`;
    html += '</tr>';

    // Total Internaciones
    html += `<tr class="row-subtotal"><td class="col-label">Total Internaciones:</td>`;
    for (const v of data.totals_internaciones) html += `<td>${v}</td>`;
    html += '</tr>';

    // Total SR
    html += `<tr class="row-subtotal"><td class="col-label">Total Segundas Revisiones:</td>`;
    for (const v of data.totals_sr) html += `<td>${v}</td>`;
    html += '</tr>';

    // Separador
    html += `<tr class="row-sep">${tdSep.repeat(n + 1)}</tr>`;

    // Local
    html += `<tr class="row-pax"><td class="col-label">Local:</td>`;
    for (const v of data.local) html += `<td>${v}</td>`;
    html += '</tr>';

    // Tránsito
    html += `<tr class="row-pax"><td class="col-label">En tránsito:</td>`;
    for (const v of data.transito) html += `<td>${v}</td>`;
    html += '</tr>';

    // Total pasajeros
    html += `<tr class="row-total-pax"><td class="col-label">Total pasajeros:</td>`;
    for (const v of data.total_pasajeros) html += `<td>${v}</td>`;
    html += '</tr>';

    html += '</tbody>';
    tabla.innerHTML = html;

    // Motivos de rechazo
    const motivosSection = document.getElementById('motivos-section');
    const motivosLista = document.getElementById('motivos-lista');
    if (data.motivos_rechazo && data.motivos_rechazo.length > 0) {
        motivosLista.innerHTML = data.motivos_rechazo.map((m) =>
            `<p class="mb-1"><strong>Extranjero de ${m.nacionalidad}</strong> [${m.fecha}] ${m.nombre}, ${m.numero_documento}: ${m.comentario}</p>`
        ).join('');
        motivosSection.classList.remove('hidden');
    } else {
        motivosSection.classList.add('hidden');
    }

    document.getElementById('tabla-preview').classList.remove('hidden');
}

/* --- Descargar PDF (generado en el servidor con ReportLab) --- */

function descargarPDF() {
    const inicio = document.getElementById('fecha_inicio').value;
    const fin = document.getElementById('fecha_fin').value;
    if (!inicio || !fin) return;
    const url = `${window.INADMITIDOS_PDF_URL}?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    window.open(url, '_blank');
}

/* --- Copiar tabla como imagen al portapapeles --- */

async function copiarImagen() {
    const btn = document.getElementById('btn-copiar-imagen');
    const nodo = document.getElementById('tabla-capture');
    if (!nodo) return;

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Capturando...';

    try {
        const canvas = await html2canvas(nodo, {
            backgroundColor: '#ffffff',
            scale: 2,
            useCORS: true,
        });

        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
        if (!blob) throw new Error('No se pudo generar la imagen.');

        if (navigator.clipboard && window.ClipboardItem) {
            await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
            mostrarToast('Imagen copiada. Pégala en WhatsApp con Ctrl+V.', 'success');
        } else {
            descargarBlob(blob, 'inadmitidos.png');
            mostrarToast('Tu navegador no soporta copiar imágenes. Se descargó el PNG.', 'warning');
        }
    } catch (e) {
        console.error(e);
        mostrarToast('Error al copiar la imagen: ' + (e.message || ''), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

function descargarBlob(blob, nombre) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/* --- Copiar comentarios formateados para WhatsApp --- */

async function copiarComentarios() {
    if (!reporteData || !reporteData.motivos_rechazo || reporteData.motivos_rechazo.length === 0) {
        mostrarToast('No hay comentarios para copiar.', 'warning');
        return;
    }

    const texto = formatearComentariosWhatsApp(reporteData.motivos_rechazo);

    try {
        await navigator.clipboard.writeText(texto);
        mostrarToast('Comentarios copiados. Pégalos en WhatsApp.', 'success');
    } catch (e) {
        console.error(e);
        mostrarToast('Error al copiar: ' + (e.message || ''), 'error');
    }
}

function formatearComentariosWhatsApp(motivos) {
    const lineas = ['*Motivos de rechazo del día*', ''];
    motivos.forEach((m) => {
        lineas.push(`*${m.nacionalidad}* - ${m.nombre} (${m.numero_documento})`);
        lineas.push(`_Fecha:_ ${m.fecha}`);
        lineas.push(m.comentario);
        lineas.push('');
    });
    return lineas.join('\n').trimEnd();
}

/* --- Helpers UI --- */

function mostrarToast(mensaje, tipo = 'info') {
    const cont = document.getElementById('toast-container');
    if (!cont) { alert(mensaje); return; }

    const clases = {
        success: 'alert-success',
        error: 'alert-error',
        warning: 'alert-warning',
        info: 'alert-info',
    };
    const iconos = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
    };

    const div = document.createElement('div');
    div.className = `alert ${clases[tipo] || clases.info}`;
    div.innerHTML = `<i class="fas ${iconos[tipo] || iconos.info}"></i><span>${mensaje}</span>`;
    cont.appendChild(div);

    setTimeout(() => { div.remove(); }, 3500);
}

function mostrarSpinner(visible) {
    const el = document.getElementById('loading-spinner');
    el.classList.toggle('hidden', !visible);
}

function mostrarError(msg) {
    document.getElementById('error-text').textContent = msg;
    document.getElementById('error-msg').classList.remove('hidden');
}

function ocultarError() {
    document.getElementById('error-msg').classList.add('hidden');
}
