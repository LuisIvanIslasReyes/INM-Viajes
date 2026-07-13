function selectCaso(id) {
    document.querySelectorAll('[data-caso-panel]').forEach(function (p) { p.hidden = String(p.dataset.casoPanel) !== String(id); });
    document.querySelectorAll('[data-caso-row]').forEach(function (r) { r.setAttribute('aria-selected', String(r.dataset.casoRow) === String(id)); });
}
function updateRegistro(registroId, campo, valor) {
    // window.CSRF_TOKEN lo define el bootstrap inline del template (depende de Django).
    var fd = new FormData();
    fd.append('csrfmiddlewaretoken', window.CSRF_TOKEN || '');
    fd.append(campo, valor);
    fetch((window.URL_PREFIX || '') + '/update-registro/' + registroId + '/', { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d.success) { location.reload(); } else { if (window.dsToast) dsToast('Error al actualizar', 'danger'); location.reload(); } })
        .catch(function () { if (window.dsToast) dsToast('Error al actualizar', 'danger'); location.reload(); });
}
