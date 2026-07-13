document.addEventListener('DOMContentLoaded', function () {
    var resumen = document.getElementById('resumen-acceso');
    var texto = document.getElementById('resumen-texto');
    var username = document.getElementById('id_username');
    var cards = Array.prototype.slice.call(document.querySelectorAll('.rol-card'));

    function pintar() {
        cards.forEach(function (c) {
            var checked = c.querySelector('input[name="rol"]').checked;
            c.style.borderColor = checked ? 'var(--ds-primary)' : 'var(--ds-border-strong)';
            c.style.borderWidth = checked ? '1.5px' : '1px';
            c.style.background = checked ? 'var(--ds-warm-50)' : 'transparent';
        });
    }
    function actualizar() {
        var sel = document.querySelector('input[name="rol"]:checked');
        if (!sel) { resumen.style.display = 'none'; return; }
        // Descripción tomada de la etiqueta real de la choice (label del <span>)
        var desc = sel.closest('.rol-card').querySelector('.ds-small').textContent.trim();
        var quien = (username.value || '').trim() || 'La cuenta';
        texto.textContent = quien + ' tendrá el rol ' + sel.value + ' — ' + desc;
        resumen.style.display = 'flex';
    }
    document.querySelectorAll('input[name="rol"]').forEach(function (radio) {
        radio.addEventListener('change', function () { pintar(); actualizar(); });
    });
    username.addEventListener('input', actualizar);
    pintar(); actualizar(); // refleja el estado inicial (p. ej. tras un error de validación)
});
