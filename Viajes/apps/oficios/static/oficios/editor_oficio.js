/*
 * Editor de oficios y plantillas (Quill 2, guardado en static/oficios/vendor/quill).
 *
 *   <div id="editor" data-destino="id_contenido_html" data-solo-lectura="0"></div>
 *   {{ contenido|json_script:"contenido-inicial" }}
 *
 * - Al enviar el formulario copia el HTML del editor al <input hidden> de `data-destino`.
 * - [data-insertar="{{var}}"]   inserta una variable donde está el cursor.
 * - [data-separador="HACE CONSTAR"] agrega un renglón separador `[[ HACE CONSTAR ]]`
 *   (vacío = línea completa de guiones) después del renglón actual.
 * - [data-relleno="--"|"__"]  agrega ` --` (guiones) o ` __` (línea para escribir) al final del renglón.
 * - [data-linea="[[ RENGLÓN ]]"]  agrega un renglón con ese marcador después del actual.
 * - [data-bloque="RECUADRO"|"TABLA"]  agrega apertura y cierre, con el cursor en medio.
 * - [data-campo]  inserta «» (campo que se llena antes de imprimir).
 * - [data-preview="url"] carga la vista previa en PDF en el iframe #vista-previa.
 * Los guiones los dibuja Word al generar el documento (services/html_docx.py).
 */
(function () {
    'use strict';

    var contenedor = document.getElementById('editor');
    if (!contenedor || typeof Quill === 'undefined') return;

    var soloLectura = contenedor.dataset.soloLectura === '1';
    var quill = new Quill(contenedor, {
        theme: 'snow',
        readOnly: soloLectura,
        modules: {
            toolbar: soloLectura ? false : [
                ['bold', 'italic', 'underline', 'strike'],
                [{ size: ['small', false] }, { script: 'super' }],  // chico = 1.5 pt menos; superíndice (notas)
                [{ align: [] }],
                [{ list: 'ordered' }, { list: 'bullet' }],
                [{ indent: '-1' }, { indent: '+1' }],
                ['clean'],
            ],
        },
    });

    var inicial = document.getElementById('contenido-inicial');
    var html = inicial ? JSON.parse(inicial.textContent) : '';
    quill.setContents(quill.clipboard.convert({ html: html || '' }), 'silent');
    quill.history.clear();

    var destino = document.getElementById(contenedor.dataset.destino);
    var sinGuardar = false;
    var enviando = false;
    quill.on('text-change', function () { sinGuardar = true; });

    if (destino && destino.form) {
        destino.form.addEventListener('submit', function () {
            destino.value = quill.root.innerHTML;
            enviando = true;
        });
        destino.form.addEventListener('change', function () { sinGuardar = true; });
    }
    window.addEventListener('beforeunload', function (e) {
        if (sinGuardar && !enviando && !soloLectura) { e.preventDefault(); e.returnValue = ''; }
    });

    function rangoActual() {
        return quill.getSelection(true) || { index: quill.getLength() - 1, length: 0 };
    }

    function finDelRenglon(indice) {
        var linea = quill.getLine(indice)[0];
        return linea ? quill.getIndex(linea) + linea.length() - 1 : quill.getLength() - 1;
    }

    document.querySelectorAll('[data-insertar]').forEach(function (boton) {
        boton.addEventListener('click', function () {
            if (soloLectura) return;
            var rango = rangoActual();
            var texto = boton.dataset.insertar;
            quill.deleteText(rango.index, rango.length, 'user');
            quill.insertText(rango.index, texto, 'user');
            quill.setSelection(rango.index + texto.length, 0, 'user');
        });
    });

    /* Agrega uno o varios renglones nuevos después del renglón actual, sin heredar su
       alineación ni su lista. Deja el cursor en el renglón `cursorEn` (0 = el primero). */
    function agregarRenglones(renglones, cursorEn) {
        var fin = finDelRenglon(rangoActual().index);
        var texto = renglones.join('\n');
        quill.insertText(fin, '\n' + texto, 'user');
        quill.formatLine(fin + 1, texto.length, { align: false, list: false, indent: false }, 'user');
        var posicion = fin + 1;
        for (var i = 0; i < cursorEn; i++) posicion += renglones[i].length + 1;
        quill.setSelection(posicion + renglones[cursorEn].length, 0, 'user');
    }

    function alHacerClic(selector, accion) {
        document.querySelectorAll(selector).forEach(function (boton) {
            boton.addEventListener('click', function () { if (!soloLectura) accion(boton); });
        });
    }

    // [[ TÍTULO ]] o [[ ]]: separador con guiones.
    alHacerClic('[data-separador]', function (boton) {
        var titulo = boton.dataset.separador.trim();
        agregarRenglones([titulo ? '[[ ' + titulo + ' ]]' : '[[ ]]'], 0);
    });

    // Un renglón con un marcador fijo: [[ RENGLÓN ]], [[ FIRMA: … ]], [[ NUEVA HOJA ]].
    alHacerClic('[data-linea]', function (boton) { agregarRenglones([boton.dataset.linea], 0); });

    // [[ RECUADRO ]] … [[ /RECUADRO ]] (o TABLA), con el cursor en el renglón de en medio.
    alHacerClic('[data-bloque]', function (boton) {
        var tipo = boton.dataset.bloque;
        agregarRenglones(['[[ ' + tipo + ' ]]', '', '[[ /' + tipo + ' ]]'], 1);
    });

    // ' --' (guiones) o ' __' (línea para escribir) al final del renglón actual.
    alHacerClic('[data-relleno]', function (boton) {
        var marca = ' ' + (boton.dataset.relleno || '--');
        var fin = finDelRenglon(rangoActual().index);
        var final = quill.getText(Math.max(0, fin - 3), 3);
        if (/\s(--|__)$/.test(final)) return;  // ya tiene relleno
        quill.insertText(fin, marca, 'user');
        quill.setSelection(fin + marca.length, 0, 'user');
    });

    // «» con el cursor en medio: lo que se llena antes de imprimir.
    alHacerClic('[data-campo]', function () {
        var rango = rangoActual();
        quill.deleteText(rango.index, rango.length, 'user');
        quill.insertText(rango.index, '«»', 'user');
        quill.setSelection(rango.index + 1, 0, 'user');
    });

    var marco = document.getElementById('vista-previa');
    document.querySelectorAll('[data-preview]').forEach(function (boton) {
        boton.addEventListener('click', function () {
            if (!marco) return;
            if (sinGuardar && !soloLectura) {
                var aviso = document.getElementById('aviso-preview');
                if (aviso) aviso.hidden = false;
            }
            marco.hidden = false;
            marco.src = boton.dataset.preview + (boton.dataset.preview.indexOf('?') < 0 ? '?' : '&') + 'inline=1&t=' + Date.now();
            marco.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });
})();
