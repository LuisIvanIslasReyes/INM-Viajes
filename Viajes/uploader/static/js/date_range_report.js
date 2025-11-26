document.addEventListener('DOMContentLoaded', function() {
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    const minDate = '2025-11-10';

    // Validar que las fechas no sean anteriores al mínimo
    function validateMinDate(input) {
        if (input.value && input.value < minDate) {
            input.value = minDate;
            alert('La fecha no puede ser anterior al 10 de noviembre de 2025');
        }
    }

    // Validar que fecha_fin no sea anterior a fecha_inicio
    function validateRange() {
        if (fechaInicio.value && fechaFin.value && fechaFin.value < fechaInicio.value) {
            alert('La fecha de fin no puede ser anterior a la fecha de inicio');
            fechaFin.value = fechaInicio.value;
        }
    }

    if (fechaInicio) {
        fechaInicio.addEventListener('change', function() {
            validateMinDate(this);
            validateRange();
        });
    }

    if (fechaFin) {
        fechaFin.addEventListener('change', function() {
            validateMinDate(this);
            validateRange();
        });
    }
});
