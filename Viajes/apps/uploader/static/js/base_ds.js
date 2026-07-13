/* ============ JS del shell (vanilla, sin dependencias) ============ */
(function () {
    'use strict';

    /* --- Sidebar: siempre inicia oculta; solo el burger la abre/cierra --- */
    var side = document.getElementById('dsSidebar');
    var toggle = document.getElementById('dsSidebarToggle');
    var overlay = document.getElementById('dsSideOverlay');
    var mqDesktop = window.matchMedia('(min-width: 1100px)');

    function setSide(open) {
        if (!side) return;
        side.classList.toggle('ds-side-closed', !open);
        if (toggle) toggle.setAttribute('aria-expanded', String(open));
        if (overlay) overlay.hidden = !(open && !mqDesktop.matches);
    }
    if (side) {
        setSide(false);
        if (toggle) toggle.addEventListener('click', function () {
            setSide(side.classList.contains('ds-side-closed'));
        });
        if (overlay) overlay.addEventListener('click', function () { setSide(false); });
    }

    /* --- Menús kebab (details): cerrar con clic fuera y Esc --- */
    document.addEventListener('click', function (e) {
        document.querySelectorAll('details.ds-menu[open]').forEach(function (d) {
            if (!d.contains(e.target)) d.removeAttribute('open');
        });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('details.ds-menu[open]').forEach(function (d) {
                d.removeAttribute('open');
                var s = d.querySelector('summary'); if (s) s.focus();
            });
        }
    });

    /* --- Toasts (sustituye los toasts DaisyUI generados por JS) --- */
    var ICONS = {
        success: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
        danger:  '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
        warning: '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/>',
        info:    '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>'
    };
    window.dsToast = function (text, kind, opts) {
        kind = kind || 'info'; opts = opts || {};
        var region = document.getElementById('dsToasts');
        if (!region) return;
        var t = document.createElement('div');
        t.className = 'ds-toast ds-toast-' + kind;
        t.innerHTML =
            '<svg class="ds-icon" aria-hidden="true" viewBox="0 0 24 24">' + (ICONS[kind] || ICONS.info) + '</svg>' +
            '<div></div>' +
            '<button class="ds-toast-close" aria-label="Cerrar aviso">' +
            '<svg class="ds-icon ds-icon-sm" aria-hidden="true" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg></button>';
        t.children[1].textContent = text;
        t.querySelector('.ds-toast-close').addEventListener('click', function () { t.remove(); });
        region.appendChild(t);
        if (!opts.sticky) setTimeout(function () { t.remove(); }, opts.duration || 6000);
    };

    /* --- Django messages → toasts --- */
    var dataEl = document.getElementById('dsDjangoMessages');
    if (dataEl) {
        try {
            JSON.parse(dataEl.textContent).forEach(function (m) {
                var kind = m.tags.indexOf('success') > -1 ? 'success'
                         : m.tags.indexOf('error')   > -1 ? 'danger'
                         : m.tags.indexOf('warning') > -1 ? 'warning' : 'info';
                window.dsToast(m.text, kind, { duration: 8000 });
            });
        } catch (e) {}
    }
})();
