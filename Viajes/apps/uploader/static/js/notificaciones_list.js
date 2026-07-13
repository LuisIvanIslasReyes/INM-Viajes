document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss cargas exitosas
    var cont = document.getElementById('exitosas-container');
    if (cont) {
        var cards = cont.querySelectorAll('.notif-exitosa');
        setTimeout(function () {
            cards.forEach(function (c, i) {
                setTimeout(function () {
                    c.style.opacity = '0'; c.style.transform = 'translateX(20px)';
                    c.style.maxHeight = c.offsetHeight + 'px';
                    setTimeout(function () { c.style.maxHeight = '0'; c.style.marginBottom = '0'; c.style.overflow = 'hidden'; c.style.padding = '0'; }, 600);
                }, i * 120);
            });
            setTimeout(function () { cont.style.opacity = '0'; setTimeout(function () { cont.remove(); }, 400); }, cards.length * 120 + 700);
        }, 2000);
    }
    // Marcar como leída (conserva endpoint y flujo). La URL plantilla y el token
    // CSRF llegan desde el bootstrap inline del template (dependen de Django).
    document.querySelectorAll('.marcar-leida-btn').forEach(function (btn) {
        btn.addEventListener('click', async function () {
            var id = this.dataset.notifId, card = this.closest('.group');
            card.style.opacity = '0.5'; card.style.pointerEvents = 'none';
            try {
                var url = (window.MARCAR_LEIDA_URL_TPL || '').replace('0', id);
                var r = await fetch(url, { method: 'POST', headers: { 'X-CSRFToken': window.CSRF_TOKEN || '', 'Content-Type': 'application/json' } });
                var data = await r.json();
                if (data.success) { if (window.dsToast) dsToast('Notificación marcada como leída', 'success'); location.reload(); }
                else { card.style.opacity = '1'; card.style.pointerEvents = 'auto'; }
            } catch (e) { card.style.opacity = '1'; card.style.pointerEvents = 'auto'; if (window.dsToast) dsToast('No se pudo actualizar', 'danger'); }
        });
    });
});
