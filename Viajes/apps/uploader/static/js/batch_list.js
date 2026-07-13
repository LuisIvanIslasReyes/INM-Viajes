document.addEventListener('DOMContentLoaded', function () {
    // -------- Confirmación destructiva tipada --------
    var dialog = document.getElementById('modal-eliminar-lote');
    var form = document.getElementById('form-eliminar-lote');
    var input = document.getElementById('mel-input');
    var submit = document.getElementById('mel-submit');
    var idLabel = document.getElementById('mel-id-label');
    var archivo = document.getElementById('mel-archivo');
    var registros = document.getElementById('mel-registros');
    var idEsperado = '';

    // Plantilla de url con placeholder 0 (la define el bootstrap inline del template).
    var urlTpl = window.DELETE_BATCH_URL_TPL || '';

    document.querySelectorAll('.btn-eliminar-lote').forEach(function (btn) {
        btn.addEventListener('click', function () {
            idEsperado = this.dataset.loteId;
            idLabel.textContent = idEsperado;
            archivo.textContent = this.dataset.loteArchivo;
            registros.textContent = this.dataset.loteRegistros;
            form.action = urlTpl.replace('0', idEsperado);
            input.value = '';
            submit.disabled = true;
            dialog.showModal();
            input.focus();
        });
    });

    input.addEventListener('input', function () {
        submit.disabled = this.value.trim() !== idEsperado;
    });

    // -------- Atajos rápidos de fecha --------
    var ff = document.getElementById('filtros-form');
    if (ff) {
        var fecha = document.getElementById('f-fecha');
        var inicio = document.getElementById('f-inicio');
        var fin = document.getElementById('f-fin');
        var fmt = function (d) { return d.toISOString().slice(0, 10); };

        ff.querySelectorAll('[data-quick]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var today = new Date(); today.setHours(0, 0, 0, 0);
                var kind = this.dataset.quick;
                fecha.value = ''; inicio.value = ''; fin.value = '';
                if (kind === 'today') {
                    fecha.value = fmt(today);
                } else if (kind === 'yesterday') {
                    var y = new Date(today); y.setDate(y.getDate() - 1);
                    fecha.value = fmt(y);
                } else if (kind === 'week') {
                    var s = new Date(today); s.setDate(s.getDate() - 6);
                    inicio.value = fmt(s); fin.value = fmt(today);
                } else if (kind === 'month') {
                    var s2 = new Date(today); s2.setDate(s2.getDate() - 29);
                    inicio.value = fmt(s2); fin.value = fmt(today);
                }
                ff.submit();
            });
        });

        // Día exacto y rango son mutuamente excluyentes (evita confusión)
        fecha.addEventListener('change', function () {
            if (fecha.value) { inicio.value = ''; fin.value = ''; }
        });
        [inicio, fin].forEach(function (inp) {
            inp.addEventListener('change', function () {
                if (inp.value) fecha.value = '';
            });
        });
    }
});
