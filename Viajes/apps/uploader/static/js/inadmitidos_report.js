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
    const R = COLORES.rojo, P = COLORES.rosa, G = COLORES.gris, B = COLORES.blanco;

    let html = '<tbody>';

    // Fila Vuelo/Origen
    html += `<tr>
        <td style="background:${R};color:#fff;font-weight:bold;text-align:left;">Vuelo:</td>
        <td style="background:${R};color:#fff;font-weight:bold;" colspan="2">${data.vuelo}</td>
        <td style="background:${R};color:#fff;font-weight:bold;">Origen:</td>
        <td style="background:${R};color:#fff;font-weight:bold;" colspan="${Math.max(n - 1, 1)}">${data.origen}</td>
    </tr>`;

    // INADMITIDOS
    html += `<tr><td colspan="${n + 1}" style="background:${P};color:${R};font-weight:bold;text-align:center;">INADMITIDOS</td></tr>`;

    // Días de la semana (vacío + nombres)
    html += `<tr><td style="background:${R};"></td>`;
    for (const rd of data.raw_dates) {
        const d = new Date(rd + 'T00:00:00');
        const dias = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
        html += `<td style="background:${R};color:#fff;font-weight:bold;">${dias[d.getDay()]}</td>`;
    }
    html += '</tr>';

    // Nacionalidad + fechas
    html += `<tr><td style="background:${P};color:${R};font-weight:bold;text-align:left;">Nacionalidad</td>`;
    for (const fecha of data.dates) {
        html += `<td style="background:${P};color:${R};font-weight:bold;">${fecha}</td>`;
    }
    html += '</tr>';

    // Filas de nacionalidades
    nats.forEach((nat, idx) => {
        const bg = idx % 2 === 0 ? B : G;
        html += `<tr><td style="background:${bg};font-weight:bold;text-align:left;">${nat}</td>`;
        for (let d = 0; d < n; d++) html += `<td style="background:${bg};">${data.nationalities[nat][d] ?? 0}</td>`;
        html += '</tr>';
    });

    // 2 filas vacías
    const tdVacio = `<td style="background:${B};"></td>`;
    for (let k = 0; k < 2; k++) {
        html += `<tr>${tdVacio.repeat(n + 1)}</tr>`;
    }

    // Total Inadmitidos
    html += `<tr><td style="background:${R};color:#fff;font-weight:bold;text-align:left;">Total Inadmitidos</td>`;
    for (const v of data.totals_inadmitidos) html += `<td style="background:${R};color:#fff;font-weight:bold;">${v}</td>`;
    html += '</tr>';

    // Separador
    const tdSep = `<td style="background:${B};padding:2px;"></td>`;
    html += `<tr>${tdSep.repeat(n + 1)}</tr>`;

    // Total Internaciones
    html += `<tr><td style="background:${P};color:${R};font-weight:bold;text-align:left;">Total Internaciones:</td>`;
    for (const v of data.totals_internaciones) html += `<td style="background:${P};color:${R};font-weight:bold;">${v}</td>`;
    html += '</tr>';

    // Total SR
    html += `<tr><td style="background:${P};color:${R};font-weight:bold;text-align:left;">Total Segundas Revisiones:</td>`;
    for (const v of data.totals_sr) html += `<td style="background:${P};color:${R};font-weight:bold;">${v}</td>`;
    html += '</tr>';

    // Separador
    html += `<tr>${tdSep.repeat(n + 1)}</tr>`;

    // Local
    html += `<tr><td style="background:${B};text-align:left;">Local:</td>`;
    for (const v of data.local) html += `<td style="background:${B};">${v}</td>`;
    html += '</tr>';

    // Tránsito
    html += `<tr><td style="background:${B};text-align:left;">En tránsito:</td>`;
    for (const v of data.transito) html += `<td style="background:${B};">${v}</td>`;
    html += '</tr>';

    // Total pasajeros
    html += `<tr><td style="background:${G};font-weight:bold;text-align:left;">Total pasajeros:</td>`;
    for (const v of data.total_pasajeros) html += `<td style="background:${G};font-weight:bold;">${v}</td>`;
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

/* --- Helpers UI --- */

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
