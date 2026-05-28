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

    const inicioInput = document.getElementById('fecha_inicio');
    [inicioInput, finInput].forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                generarReporte();
            }
        });
    });
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
    const sumar = (arr) => arr.reduce((acc, v) => acc + (Number(v) || 0), 0);
    const totalCols = n + 2; // etiqueta + n fechas + columna Total

    let html = '<tbody>';

    // Fila Vuelo/Origen — proporciones tipo Img1: label / valor / label / valor
    html += `<tr class="row-vuelo">
        <td class="col-label">Vuelo:</td>
        <td colspan="${Math.max(Math.floor(n / 2), 1)}">${data.vuelo}</td>
        <td>Origen:</td>
        <td colspan="${Math.max(n - Math.floor(n / 2), 1)}">${data.origen}</td>
    </tr>`;

    // INADMITIDOS
    html += `<tr class="row-title"><td colspan="${totalCols}">INADMITIDOS</td></tr>`;

    // Días de la semana (vacío + nombres + Total)
    const dias = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
    html += `<tr class="row-dias"><td class="col-label"></td>`;
    for (const rd of data.raw_dates) {
        const d = new Date(rd + 'T00:00:00');
        html += `<td>${dias[d.getDay()]}</td>`;
    }
    html += `<td>Total</td>`;
    html += '</tr>';

    // Nacionalidad + fechas
    html += `<tr class="row-header-nac"><td class="col-label">Nacionalidad</td>`;
    for (const fecha of data.dates) {
        html += `<td>${fecha}</td>`;
    }
    html += `<td></td>`;
    html += '</tr>';

    // Filas de nacionalidades (alternadas) — suma horizontal por nacionalidad
    nats.forEach((nat, idx) => {
        const altClass = idx % 2 === 1 ? ' row-alt' : '';
        html += `<tr class="row-nac${altClass}"><td class="col-label">${nat}</td>`;
        let totalNat = 0;
        for (let d = 0; d < n; d++) {
            const v = data.nationalities[nat][d] ?? 0;
            totalNat += Number(v) || 0;
            html += `<td>${v}</td>`;
        }
        html += `<td><strong>${totalNat}</strong></td>`;
        html += '</tr>';
    });

    // 2 filas vacías (separador antes del total)
    const tdSep = `<td></td>`;
    for (let k = 0; k < 2; k++) {
        html += `<tr class="row-sep">${tdSep.repeat(totalCols)}</tr>`;
    }

    // Total Inadmitidos
    html += `<tr class="row-total-inad"><td class="col-label">Total Inadmitidos</td>`;
    for (const v of data.totals_inadmitidos) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.totals_inadmitidos)}</td></tr>`;

    // Total Internaciones
    html += `<tr class="row-subtotal row-subtotal-intern"><td class="col-label">Total Internaciones:</td>`;
    for (const v of data.totals_internaciones) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.totals_internaciones)}</td></tr>`;

    // Total SR
    html += `<tr class="row-subtotal row-subtotal-sr"><td class="col-label">Total Segundas Revisiones:</td>`;
    for (const v of data.totals_sr) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.totals_sr)}</td></tr>`;

    // Separador
    html += `<tr class="row-sep">${tdSep.repeat(totalCols)}</tr>`;

    // Local
    html += `<tr class="row-pax"><td class="col-label">Pasajeros Locales:</td>`;
    for (const v of data.local) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.local)}</td></tr>`;

    // Tránsito
    html += `<tr class="row-pax"><td class="col-label">Pasajeros en tránsito:</td>`;
    for (const v of data.transito) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.transito)}</td></tr>`;

    // Total pasajeros
    html += `<tr class="row-total-pax"><td class="col-label">Total pasajeros:</td>`;
    for (const v of data.total_pasajeros) html += `<td>${v}</td>`;
    html += `<td>${sumar(data.total_pasajeros)}</td></tr>`;

    // Separador antes de tiempos
    html += `<tr class="row-sep">${tdSep.repeat(totalCols)}</tr>`;

    const horaInicio = data.hora_inicio || [];
    const horaFin = data.hora_fin || [];
    const tFma = data.tiempo_fma || [];
    const tMex = data.tiempo_mexicanos || [];
    const tExt = data.tiempo_extranjeros || [];
    const tRS = data.tiempo_revisiones_secundarias || [];

    // Título Tiempos de atención
    html += `<tr class="row-dias"><td colspan="${totalCols}">Tiempos de atención</td></tr>`;

    // Hora Inicio
    html += `<tr class="row-pax"><td class="col-label">Hora Inicio:</td>`;
    for (let d = 0; d < n; d++) html += `<td>${horaInicio[d] ?? ''}</td>`;
    html += `<td></td></tr>`;

    // Hora Fin
    html += `<tr class="row-pax"><td class="col-label">Hora Fin:</td>`;
    for (let d = 0; d < n; d++) html += `<td>${horaFin[d] ?? ''}</td>`;
    html += `<td></td></tr>`;

    const fmtMin = (mins) => {
        const num = Number(mins);
        if (!Number.isFinite(num) || num <= 0) return '0m';
        const h = Math.floor(num / 60);
        const m = num % 60;
        if (h === 0) return `${m}m`;
        if (m === 0) return `${h}h`;
        return `${h}h ${m}m`;
    };

    const renderRubro = (label, arr) => {
        html += `<tr class="row-pax"><td class="col-label">${label}:</td>`;
        let totalRub = 0;
        for (let d = 0; d < n; d++) {
            const v = arr[d];
            if (v !== '' && v !== null && v !== undefined) totalRub += Number(v) || 0;
            html += `<td>${v ?? ''}</td>`;
        }
        html += `<td><strong>${totalRub}</strong></td></tr>`;
    };

    renderRubro('FMA', tFma);
    renderRubro('Mexicanos', tMex);
    renderRubro('Extranjeros', tExt);
    renderRubro('Revisiones Secundarias', tRS);

    // Total por día (suma de los 4 rubros, en min → "Xh Ym")
    html += `<tr class="row-total-pax"><td class="col-label">Total por día:</td>`;
    let totalGlobal = 0;
    for (let d = 0; d < n; d++) {
        const fma = Number(tFma[d]) || 0;
        const mex = Number(tMex[d]) || 0;
        const ext = Number(tExt[d]) || 0;
        const rs = Number(tRS[d]) || 0;
        const hayDatos = tFma[d] !== '' || tMex[d] !== '' || tExt[d] !== '' || tRS[d] !== '';
        const sumaDia = fma + mex + ext + rs;
        totalGlobal += sumaDia;
        html += `<td><strong>${hayDatos ? fmtMin(sumaDia) : ''}</strong></td>`;
    }
    html += `<td><strong>${fmtMin(totalGlobal)}</strong></td></tr>`;

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

/* --- Captura de nodos como PNG (helper compartido) --- */

async function capturarNodo(nodo) {
    return await html2canvas(nodo, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        ignoreElements: (el) => el.classList && el.classList.contains('no-capturar'),
    });
}

async function copiarCanvasComoImagen(canvas, nombreDescarga, mensajeExito) {
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
    if (!blob) throw new Error('No se pudo generar la imagen.');

    if (navigator.clipboard && window.ClipboardItem) {
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        mostrarToast(mensajeExito, 'success');
    } else {
        descargarBlob(blob, nombreDescarga);
        mostrarToast('Tu navegador no soporta copiar imágenes. Se descargó el PNG.', 'warning');
    }
}

async function capturarYCopiar(nodoId, btnId, nombreDescarga, mensajeExito) {
    const btn = document.getElementById(btnId);
    const nodo = document.getElementById(nodoId);
    if (!nodo) return;

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Capturando...';

    try {
        const canvas = await capturarNodo(nodo);
        await copiarCanvasComoImagen(canvas, nombreDescarga, mensajeExito);
    } catch (e) {
        console.error(e);
        mostrarToast('Error al copiar la imagen: ' + (e.message || ''), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

/* --- Copiar tabla como imagen --- */

function copiarImagen() {
    return capturarYCopiar(
        'tabla-capture',
        'btn-copiar-imagen',
        'inadmitidos.png',
        'Tabla copiada. Pégala donde necesites.'
    );
}

/* --- Copiar comentarios como imagen --- */

function copiarComentariosImagen() {
    if (!reporteData || !reporteData.motivos_rechazo || reporteData.motivos_rechazo.length === 0) {
        mostrarToast('No hay comentarios para copiar.', 'warning');
        return;
    }
    return capturarYCopiar(
        'motivos-capture',
        'btn-copiar-comentarios-img',
        'comentarios.png',
        'Imagen de comentarios copiada.'
    );
}

/* --- Copiar todo: tabla (imagen) + comentarios (texto rich) en un solo Ctrl+V --- */

async function copiarTodo() {
    const btn = document.getElementById('btn-copiar-todo');
    const nodoTabla = document.getElementById('tabla-capture');
    if (!nodoTabla) return;

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Capturando...';

    try {
        const canvas = await capturarNodo(nodoTabla);
        const imgDataUrl = canvas.toDataURL('image/png');

        const tieneMotivos = reporteData && reporteData.motivos_rechazo && reporteData.motivos_rechazo.length > 0;

        let html = '<div style="font-family:Arial,sans-serif;font-size:11pt;">';
        html += `<img src="${imgDataUrl}" style="max-width:100%;" alt="Reporte de Inadmitidos"/>`;
        if (tieneMotivos) {
            html += '<br/><br/>';
            const motivosHtml = formatearComentariosHTML(reporteData.motivos_rechazo);
            html += motivosHtml.replace(/^<div[^>]*>|<\/div>$/g, '');
        }
        html += '</div>';

        let plano = 'Reporte de Inadmitidos\n\n';
        if (tieneMotivos) plano += formatearComentariosPlano(reporteData.motivos_rechazo);

        if (navigator.clipboard && window.ClipboardItem) {
            const htmlBlob = new Blob([html], { type: 'text/html' });
            const planoBlob = new Blob([plano], { type: 'text/plain' });
            await navigator.clipboard.write([new ClipboardItem({
                'text/html': htmlBlob,
                'text/plain': planoBlob,
            })]);
            mostrarToast('Reporte completo copiado. Pega en Word/Outlook/Gmail.', 'success');
        } else {
            mostrarToast('Tu navegador no soporta este formato combinado.', 'warning');
        }
    } catch (e) {
        console.error(e);
        mostrarToast('Error al copiar todo: ' + (e.message || ''), 'error');
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

/* --- Copiar comentarios con formato enriquecido (HTML + texto plano) --- */

async function copiarComentarios() {
    if (!reporteData || !reporteData.motivos_rechazo || reporteData.motivos_rechazo.length === 0) {
        mostrarToast('No hay comentarios para copiar.', 'warning');
        return;
    }

    const html = formatearComentariosHTML(reporteData.motivos_rechazo);
    const plano = formatearComentariosPlano(reporteData.motivos_rechazo);

    try {
        if (navigator.clipboard && window.ClipboardItem) {
            const htmlBlob = new Blob([html], { type: 'text/html' });
            const planoBlob = new Blob([plano], { type: 'text/plain' });
            await navigator.clipboard.write([new ClipboardItem({
                'text/html': htmlBlob,
                'text/plain': planoBlob,
            })]);
            mostrarToast('Comentarios copiados con formato. Pégalos donde necesites.', 'success');
        } else {
            await navigator.clipboard.writeText(plano);
            mostrarToast('Comentarios copiados (sin formato enriquecido).', 'success');
        }
    } catch (e) {
        console.error(e);
        mostrarToast('Error al copiar: ' + (e.message || ''), 'error');
    }
}

function formatearComentariosHTML(motivos) {
    let html = '<div style="font-family:Arial,sans-serif;font-size:11pt;">';
    html += '<p style="margin:0 0 8px 0;"><strong>Motivos de rechazo del día</strong></p>';
    motivos.forEach((m) => {
        html += '<p style="margin:0 0 8px 0;">';
        html += `<strong>${escapeHTML(m.nacionalidad)}</strong> - ${escapeHTML(m.nombre)} (${escapeHTML(m.numero_documento)})<br/>`;
        html += `<em>Fecha:</em> ${escapeHTML(m.fecha)}<br/>`;
        html += `${escapeHTML(m.comentario)}`;
        html += '</p>';
    });
    html += '</div>';
    return html;
}

function formatearComentariosPlano(motivos) {
    const lineas = ['Motivos de rechazo del día', ''];
    motivos.forEach((m) => {
        lineas.push(`${m.nacionalidad} - ${m.nombre} (${m.numero_documento})`);
        lineas.push(`Fecha: ${m.fecha}`);
        lineas.push(m.comentario);
        lineas.push('');
    });
    return lineas.join('\n').trimEnd();
}

function escapeHTML(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
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
