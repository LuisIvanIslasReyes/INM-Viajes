/*
 * Autocompletado de empleados sobre GET /empleados/buscar/?q= (réplica local de la Estancia).
 *
 *   <div class="emp-auto" data-empleado-auto data-url="/empleados/buscar/" data-fundamento="1">
 *     <input type="text" class="ds-input" data-auto-texto>
 *     <input type="hidden" name="firmante" data-auto-valor>
 *     <ul class="emp-auto-lista" role="listbox" hidden></ul>
 *     <p class="ds-small emp-auto-info" data-auto-info></p>
 *   </div>
 *
 * data-fundamento="1": avisa si el empleado elegido no tiene fundamento (solo el firmante lo necesita).
 * Borrar el texto deja el campo vacío.
 */
(function () {
    'use strict';

    function info(emp, pideFundamento) {
        if (!emp) return '';
        var partes = [emp.cargo || 'Sin cargo'];
        if (pideFundamento) {
            partes.push(emp.fundamento ? 'Fundamento: ' + emp.fundamento : '⚠ Sin fundamento: no podrá imprimir');
        }
        return partes.join(' · ');
    }

    function iniciar(caja) {
        var texto = caja.querySelector('[data-auto-texto]');
        var valor = caja.querySelector('[data-auto-valor]');
        var lista = caja.querySelector('.emp-auto-lista');
        var ayuda = caja.querySelector('[data-auto-info]');
        var pideFundamento = caja.dataset.fundamento === '1';
        var resultados = [];
        var activo = -1;
        var temporizador = null;
        var ultimoElegido = texto.value;

        function cerrar() { lista.hidden = true; activo = -1; texto.setAttribute('aria-expanded', 'false'); }

        function pintar() {
            lista.innerHTML = '';
            if (!resultados.length) {
                var vacio = document.createElement('li');
                vacio.className = 'emp-auto-op';
                vacio.textContent = 'Sin coincidencias';
                lista.appendChild(vacio);
            }
            resultados.forEach(function (emp, i) {
                var li = document.createElement('li');
                li.className = 'emp-auto-op';
                li.setAttribute('role', 'option');
                li.setAttribute('aria-selected', i === activo ? 'true' : 'false');
                var nombre = document.createElement('strong');
                nombre.textContent = emp.nombre_para_oficio + (emp.firmante_habitual ? ' ★' : '');
                var detalle = document.createElement('span');
                detalle.textContent = info(emp, pideFundamento);
                li.appendChild(nombre);
                li.appendChild(detalle);
                li.addEventListener('mousedown', function (e) { e.preventDefault(); elegir(emp); });
                lista.appendChild(li);
            });
            lista.hidden = false;
            texto.setAttribute('aria-expanded', 'true');
        }

        function elegir(emp) {
            valor.value = emp.id;
            texto.value = emp.nombre_para_oficio;
            ultimoElegido = texto.value;
            if (ayuda) ayuda.textContent = info(emp, pideFundamento);
            cerrar();
        }

        function buscar() {
            var q = texto.value.trim();
            if (q.length < 2) { cerrar(); return; }
            fetch(caja.dataset.url + '?q=' + encodeURIComponent(q), { headers: { 'Accept': 'application/json' } })
                .then(function (r) { return r.ok ? r.json() : { resultados: [] }; })
                .then(function (datos) { resultados = datos.resultados || []; activo = -1; pintar(); })
                .catch(function () { resultados = []; cerrar(); });
        }

        texto.setAttribute('role', 'combobox');
        texto.setAttribute('aria-autocomplete', 'list');
        texto.setAttribute('aria-expanded', 'false');
        texto.setAttribute('autocomplete', 'off');

        texto.addEventListener('input', function () {
            if (!texto.value.trim()) { valor.value = ''; if (ayuda) ayuda.textContent = ''; }
            clearTimeout(temporizador);
            temporizador = setTimeout(buscar, 250);
        });
        texto.addEventListener('keydown', function (e) {
            if (lista.hidden || !resultados.length) return;
            if (e.key === 'ArrowDown') { activo = (activo + 1) % resultados.length; pintar(); e.preventDefault(); }
            else if (e.key === 'ArrowUp') { activo = (activo - 1 + resultados.length) % resultados.length; pintar(); e.preventDefault(); }
            else if (e.key === 'Enter' && activo >= 0) { elegir(resultados[activo]); e.preventDefault(); }
            else if (e.key === 'Escape') { cerrar(); }
        });
        texto.addEventListener('blur', function () {
            // Si escribió algo y no eligió de la lista, se regresa a lo último válido.
            setTimeout(function () {
                cerrar();
                if (texto.value.trim() && texto.value !== ultimoElegido) texto.value = ultimoElegido;
            }, 120);
        });
    }

    document.querySelectorAll('[data-empleado-auto]').forEach(iniciar);
})();
