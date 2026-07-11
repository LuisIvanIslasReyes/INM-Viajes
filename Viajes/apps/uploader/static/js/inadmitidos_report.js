/* Reporte de Inadmitidos */

const COLORES = {
    rojo: '#700606',
    rosa: '#FED8D8',
    gris: '#DDDDDD',
    blanco: '#F3F3F2',
    blanco_puro: '#FFFFFF',
};

let reporteData = null;

function fechaISO(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function hoy() {
    return fechaISO(new Date());
}

function ayer() {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return fechaISO(d);
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

async function generarReporte(mostrarTotal = true) {
    const inicio = document.getElementById('fecha_inicio').value;
    const fin = document.getElementById('fecha_fin').value;

    if (!inicio || !fin) { mostrarError('Selecciona ambas fechas.'); return; }
    if (fin < inicio) { mostrarError('La fecha fin debe ser mayor o igual a la fecha inicio.'); return; }

    ocultarError();
    mostrarSpinner(true);
    document.getElementById('tabla-preview').classList.add('hidden');
    document.getElementById('btn-excel').classList.add('hidden');
    document.getElementById('btn-excel-autoridades').classList.add('hidden');

    const url = `${window.INADMITIDOS_DATA_URL}?fecha_inicio=${inicio}&fecha_fin=${fin}`;

    try {
        const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!resp.ok) {
            const d = await resp.json().catch(() => ({}));
            throw new Error(d.error || `Error ${resp.status}`);
        }
        reporteData = await resp.json();
        renderTabla(reporteData, mostrarTotal);
        document.getElementById('btn-excel').classList.remove('hidden');
        document.getElementById('btn-excel-autoridades').classList.remove('hidden');
    } catch (e) {
        mostrarError(e.message || 'Error al obtener los datos.');
    } finally {
        mostrarSpinner(false);
    }
}

/* --- Generar reporte del día actual (sin columna Total) --- */

function generarReporteDelDia() {
    const fechaHoy = hoy();
    document.getElementById('fecha_inicio').value = fechaHoy;
    document.getElementById('fecha_fin').value = fechaHoy;
    generarReporte(false);
}

/* --- Generar reporte del día de ayer (sin columna Total) --- */

function generarReporteAyer() {
    const fechaAyer = ayer();
    document.getElementById('fecha_inicio').value = fechaAyer;
    document.getElementById('fecha_fin').value = fechaAyer;
    generarReporte(false);
}

/* --- Renderizar tabla de previsualización --- */

function renderTabla(data, mostrarTotal = true) {
    const tabla = document.getElementById('tabla-inadmitidos');
    const n = data.dates.length;
    const nats = Object.keys(data.nationalities);
    const sumar = (arr) => arr.reduce((acc, v) => acc + (Number(v) || 0), 0);
    const totalCols = mostrarTotal ? n + 2 : n + 1; // etiqueta + n fechas [+ columna Total]

    let html = '<tbody>';

    // ── Fila Vuelo / Origen (label / valor / label / valor) ──
    if (totalCols < 4) {
        html += `<tr class="row-vuelo"><td class="col-label" colspan="${totalCols}">Vuelo: ${data.vuelo} — Origen: ${data.origen}</td></tr>`;
    } else {
        const labelSpan = totalCols >= 6 ? 2 : 1;
        const anchoVal = totalCols - 2 * labelSpan;
        const valIzq = Math.max(Math.ceil(anchoVal / 2), 1);
        const valDer = Math.max(anchoVal - valIzq, 1);
        html += `<tr class="row-vuelo">
            <td class="col-label" colspan="${labelSpan}">Vuelo:</td>
            <td class="val" colspan="${valIzq}">${data.vuelo}</td>
            <td class="col-label" colspan="${labelSpan}">Origen:</td>
            <td class="val" colspan="${valDer}">${data.origen}</td>
        </tr>`;
    }

    // ── Título INADMITIDOS ──
    html += `<tr class="row-title"><td colspan="${totalCols}">INADMITIDOS</td></tr>`;

    // ── Encabezado: Nacionalidad (rowspan 2) + días [+ Total] ──
    const dias = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
    html += `<tr class="row-dias"><td class="col-nac-head" rowspan="2">Nacionalidad</td>`;
    for (const rd of data.raw_dates) {
        const d = new Date(rd + 'T00:00:00');
        html += `<td>${dias[d.getDay()]}</td>`;
    }
    if (mostrarTotal) html += `<td class="col-total-head">Total</td>`;
    html += '</tr>';

    // ── Fila de fechas (debajo de los días) ──
    html += `<tr class="row-fechas">`;
    for (const fecha of data.dates) html += `<td>${fecha}</td>`;
    if (mostrarTotal) html += `<td></td>`;
    html += '</tr>';

    // ── Total Inadmitidos ──
    html += `<tr class="row-total-inad"><td class="col-label">Total Inadmitidos</td>`;
    for (const v of data.totals_inadmitidos) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td class="col-total">${sumar(data.totals_inadmitidos)}</td>`;
    html += '</tr>';

    // ── Filas de nacionalidades (inadmitidos) — suma horizontal ──
    nats.forEach((nat) => {
        html += `<tr class="row-data"><td class="col-label">${nat}</td>`;
        let totalNat = 0;
        for (let d = 0; d < n; d++) {
            const v = data.nationalities[nat][d] ?? 0;
            totalNat += Number(v) || 0;
            html += `<td>${v}</td>`;
        }
        if (mostrarTotal) html += `<td class="col-total">${totalNat}</td>`;
        html += '</tr>';
    });

    // ── Total Internaciones ──
    html += `<tr class="row-total-intern"><td class="col-label">Total Internaciones:</td>`;
    for (const v of data.totals_internaciones) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td class="col-total">${sumar(data.totals_internaciones)}</td>`;
    html += '</tr>';

    // ── Desglose por nacionalidad de las internaciones (indentado) ──
    const natsIntern = Object.keys(data.internaciones_nationalities || {});
    natsIntern.forEach((nat) => {
        const fila = data.internaciones_nationalities[nat];
        html += `<tr class="row-intern-nac"><td class="col-label">${nat}</td>`;
        let totalNat = 0;
        for (let d = 0; d < n; d++) {
            const v = fila[d] ?? 0;
            totalNat += Number(v) || 0;
            html += `<td>${v}</td>`;
        }
        if (mostrarTotal) html += `<td class="col-total">${totalNat}</td>`;
        html += '</tr>';
    });

    // ── Total Segundas Revisiones ──
    html += `<tr class="row-total-sr"><td class="col-label">Total Segundas Revisiones:</td>`;
    for (const v of data.totals_sr) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td>${sumar(data.totals_sr)}</td>`;
    html += '</tr>';

    // ── Pasajeros Locales ──
    html += `<tr class="row-data"><td class="col-label">Pasajeros Locales:</td>`;
    for (const v of data.local) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td class="col-total">${sumar(data.local)}</td>`;
    html += '</tr>';

    // ── Pasajeros en tránsito ──
    html += `<tr class="row-data"><td class="col-label">Pasajeros en tránsito:</td>`;
    for (const v of data.transito) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td class="col-total">${sumar(data.transito)}</td>`;
    html += '</tr>';

    // ── Total pasajeros ──
    html += `<tr class="row-total-pax"><td class="col-label">Total pasajeros:</td>`;
    for (const v of data.total_pasajeros) html += `<td>${v}</td>`;
    if (mostrarTotal) html += `<td class="col-total">${sumar(data.total_pasajeros)}</td>`;
    html += '</tr>';

    const horaInicio = data.hora_inicio         || [];
    const horaFin = data.hora_fin               || [];
    const tFma = data.tiempo_fma                || [];
    const pFma = data.fma_personas              || [];
    const tMex = data.tiempo_mexicanos          || [];
    const tExt = data.tiempo_extranjeros        || [];
    const rsIni = data.rs_hora_inicio           || [];
    const rsFin = data.rs_hora_fin              || [];
    const dFma = data.dur_fma                   || [];
    const dMex = data.dur_mexicanos             || [];
    const dExt = data.dur_extranjeros           || [];
    const dRS = data.dur_revisiones_secundarias || [];

    // Encabezado de sección: Tiempos de atención
    html += `<tr class="row-section"><td colspan="${totalCols}">Tiempos de atención</td></tr>`;

    // Hora Inicio
    html += `<tr class="row-data"><td class="col-label">Hora Inicio en fila:</td>`;
    for (let d = 0; d < n; d++) html += `<td>${horaInicio[d] ?? ''}</td>`;
    if (mostrarTotal) html += `<td></td>`;
    html += '</tr>';

    // Hora Fin (se captura aparte; se muestra después de los rubros)
    html += `<tr class="row-data"><td class="col-label">Hora Fin en fila:</td>`;
    for (let d = 0; d < n; d++) html += `<td>${horaFin[d] ?? ''}</td>`;
    if (mostrarTotal) html += `<td></td>`;
    html += '</tr>';

    const fmtMin = (mins) => {
        const num = Number(mins);
        if (!Number.isFinite(num) || num <= 0) return '0m';
        const h = Math.floor(num / 60);
        const m = num % 60;
        if (h === 0) return `${m}m`;
        if (m === 0) return `${h}h`;
        return `${h}h ${m}m`;
    };

    // Convierte 'HH:MM' a minutos desde medianoche (null si vacío/inválido).
    const minDeHora = (str) => {
        if (!str) return null;
        const [h, m] = String(str).split(':').map(Number);
        if (!Number.isFinite(h) || !Number.isFinite(m)) return null;
        return h * 60 + m;
    };

    // Jornada completa: desde Hora Inicio en fila hasta SR Hora Fin
    // (el cierre real del día), con cruce de medianoche.
    const durDia = (inicioStr, finStr) => {
        const ini = minDeHora(inicioStr);
        const fin = minDeHora(finStr);
        if (ini === null || fin === null) return '';
        let d = fin - ini;
        if (d < 0) d += 1440;
        return d;
    };

    // Cada rubro muestra la hora de término capturada y, entre paréntesis, la
    // duración derivada (hora − hito anterior, calculada en el backend).
    //
    // `personasArr` (opcional, sólo FMA) lleva el conteo de personas atendidas.
    // Cuando hay tiempo y personas la celda se subdivide (personas arriba,
    // tiempo abajo); si sólo hay uno de los dos, se muestra ese valor solo.
    const renderRubro = (label, horaArr, durArr, personasArr) => {
        html += `<tr class="row-data"><td class="col-label">${label}:</td>`;
        let totalDur = 0;
        for (let d = 0; d < n; d++) {
            const hora = horaArr[d] ?? '';
            const dur = durArr[d];
            const tieneDur = dur !== '' && dur !== null && dur !== undefined && Number(dur) > 0;
            if (tieneDur) totalDur += Number(dur);
            const durTxt = (hora && tieneDur) ? ` <span class="dur">(${fmtMin(dur)})</span>` : '';
            const tiempoHtml = hora ? `${hora}${durTxt}` : '';

            const personas = personasArr ? personasArr[d] : null;
            const tienePersonas = personas !== '' && personas !== null && personas !== undefined && Number(personas) > 0;

            if (tienePersonas && tiempoHtml) {
                html += `<td class="cell-split"><div class="split-wrap">`
                     +  `<div class="split-top">${Number(personas)} personas</div>`
                     +  `<div class="split-bottom">${tiempoHtml}</div>`
                     +  `</div></td>`;
            } else if (tienePersonas) {
                html += `<td class="cell-personas">${Number(personas)} personas</td>`;
            } else {
                html += `<td>${tiempoHtml}</td>`;
            }
        }
        if (mostrarTotal) html += `<td class="col-total">${totalDur > 0 ? fmtMin(totalDur) : ''}</td>`;
        html += '</tr>';
    };

    renderRubro('Fila FMA', tFma, dFma, pFma);
    renderRubro('Fila Mexicanos', tMex, dMex);
    renderRubro('Fila Extranjeros', tExt, dExt);

    // Revisiones Secundarias: ventana propia en filas separadas
    // (Hora Inicio / Hora Fin / Duración derivada = fin − inicio).
    const renderHorasRS = (label, horaArr) => {
        html += `<tr class="row-data"><td class="col-label">${label}:</td>`;
        for (let d = 0; d < n; d++) html += `<td>${horaArr[d] ?? ''}</td>`;
        if (mostrarTotal) html += `<td></td>`;
        html += '</tr>';
    };
    renderHorasRS('SR Hora Inicio', rsIni);
    renderHorasRS('SR Hora Fin', rsFin);

    html += `<tr class="row-data"><td class="col-label">SR Duración:</td>`;
    let totalRS = 0;
    for (let d = 0; d < n; d++) {
        const dur = dRS[d];
        const tieneDur = dur !== '' && dur !== null && dur !== undefined && Number(dur) > 0;
        if (tieneDur) totalRS += Number(dur);
        html += `<td>${tieneDur ? fmtMin(dur) : ''}</td>`;
    }
    if (mostrarTotal) html += `<td class="col-total">${totalRS > 0 ? fmtMin(totalRS) : ''}</td>`;
    html += '</tr>';

    // Total por día: Hora Inicio en fila → SR Hora Fin (jornada completa).
    html += `<tr class="row-total-dia"><td class="col-label">Total por día:</td>`;
    let totalDiaAcum = 0;
    for (let d = 0; d < n; d++) {
        const dur = durDia(horaInicio[d], rsFin[d]);
        const tieneDur = dur !== '' && Number(dur) > 0;
        if (tieneDur) totalDiaAcum += Number(dur);
        html += `<td>${tieneDur ? fmtMin(dur) : ''}</td>`;
    }
    if (mostrarTotal) html += `<td class="col-total">${totalDiaAcum > 0 ? fmtMin(totalDiaAcum) : ''}</td>`;
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

/* --- Descargar Excel (generado en el servidor con openpyxl) --- */

// Excel completo: toda la información (incluye Tiempos de Atención y motivos).
function descargarExcel() {
    abrirExcel(false);
}

// Excel autoridades: omite la sección Tiempos de Atención y los motivos.
function descargarExcelAutoridades() {
    abrirExcel(true);
}

function abrirExcel(autoridades) {
    const inicio = document.getElementById('fecha_inicio').value;
    const fin = document.getElementById('fecha_fin').value;
    if (!inicio || !fin) return;
    let url = `${window.INADMITIDOS_EXCEL_URL}?fecha_inicio=${inicio}&fecha_fin=${fin}`;
    if (autoridades) url += '&autoridades=1';
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

        let html = '<div style="font-family:Calibri,Carlito,sans-serif;font-size:13pt;">';
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
    let html = '<div style="font-family:Calibri,Carlito,sans-serif;font-size:13pt;">';
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
    // Toast del design system (window.dsToast, definido en base_ds.html).
    // 'error' del API interno mapea a la variante 'danger' del DS.
    const kind = tipo === 'error' ? 'danger' : tipo; // success | warning | info | danger
    if (window.dsToast) {
        window.dsToast(mensaje, kind, { duration: 3500 });
    } else {
        alert(mensaje);
    }
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
