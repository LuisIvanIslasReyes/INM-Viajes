"""
Réplica local del catálogo de empleados de la Estancia (ProyectoEstancia → Personal).

La fuente de verdad es la Estancia: allá RRHH da de alta, corrige y da de baja.
Aquí solo se copia, para que Viajes siga teniendo el catálogo si la Estancia se
apaga. Por eso los datos del empleado NO se editan en Viajes (se sobrescriben en
cada sincronización); lo único propio de Viajes es `firmante_habitual`.

Llave de cruce: `id_estancia` (el `id_empleado` de la Estancia). No se usa el número
de empleado porque allá es opcional (registros legacy sin número).

Nunca se borran filas: un empleado dado de baja (o que ya no viene en la respuesta)
queda `activo=False`, porque oficios ya generados pueden mencionarlo.
"""
from django.conf import settings
from django.db import models

# Abreviatura impresa del título académico (mismos códigos que Personal.Empleado.AcademicTitle).
TITULOS_ABREVIADOS = {
    'LIC': 'LIC.',
    'MTRO': 'MTRO.',
    'MTRA': 'MTRA.',
    'ING': 'ING.',
    'DR': 'DR.',
    'DRA': 'DRA.',
    'MC': 'M.C.',
    'MTI': 'M.T.I.',
    'CP': 'C.P.',
    'ARQ': 'ARQ.',
}


class Empleado(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'

    # ---- Datos replicados de la Estancia (solo lectura aquí) ----
    id_estancia = models.PositiveIntegerField(
        unique=True, help_text='id_empleado en la Estancia. Llave de sincronización.',
    )
    numero_empleado = models.CharField(max_length=10, blank=True, default='', db_index=True)
    titulo_academico = models.CharField(max_length=10, blank=True, default='')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    sexo = models.CharField(max_length=1, choices=Sexo.choices, blank=True, default='')
    plaza = models.CharField(max_length=150, blank=True, default='')
    cargo = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Jerarquía principal vigente en la Estancia (ej. JEFE DE DEPARTAMENTO).',
    )
    municipio_id_estancia = models.PositiveIntegerField(null=True, blank=True)
    municipio = models.CharField(max_length=100, blank=True, default='')
    estado_estancia = models.CharField(
        max_length=10, blank=True, default='',
        help_text='DISPONIBLE / ACTIVO / BAJA tal como lo reporta la Estancia.',
    )
    modificado_en_estancia = models.DateTimeField(null=True, blank=True)

    # ---- Propio de Viajes ----
    activo = models.BooleanField(
        default=True, db_index=True,
        help_text='False si en la Estancia está de baja o ya no aparece en el catálogo.',
    )
    firmante_habitual = models.BooleanField(
        default=False,
        help_text='Se muestra primero en el buscador. No lo toca la sincronización.',
    )
    sincronizado_en = models.DateTimeField()

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['-firmante_habitual', 'apellidos', 'nombres']
        indexes = [
            models.Index(fields=['apellidos', 'nombres']),
            models.Index(fields=['municipio_id_estancia']),
        ]

    def __str__(self):
        if self.numero_empleado:
            return f'{self.numero_empleado} — {self.nombre_completo}'
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'.strip()

    @property
    def titulo_abreviado(self):
        return TITULOS_ABREVIADOS.get(self.titulo_academico, '')

    @property
    def nombre_para_oficio(self):
        """Como se imprime en un oficio: 'LIC. MELISSA GALLEGOS'."""
        return f'{self.titulo_abreviado} {self.nombre_completo}'.strip()


class SincronizacionEmpleados(models.Model):
    """Bitácora de cada intento de sincronización (para saber qué tan fresca está la réplica)."""

    class Origen(models.TextChoices):
        PROGRAMADA = 'PROGRAMADA', 'Tarea programada'
        MANUAL = 'MANUAL', 'Botón "Sincronizar ahora"'

    origen = models.CharField(max_length=12, choices=Origen.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
    )
    iniciada_en = models.DateTimeField(auto_now_add=True)
    terminada_en = models.DateTimeField(null=True, blank=True)
    exitosa = models.BooleanField(default=False)
    recibidos = models.PositiveIntegerField(default=0)
    creados = models.PositiveIntegerField(default=0)
    actualizados = models.PositiveIntegerField(default=0)
    desactivados = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Sincronización de empleados'
        verbose_name_plural = 'Sincronizaciones de empleados'
        ordering = ['-iniciada_en']

    def __str__(self):
        estado = 'OK' if self.exitosa else 'ERROR'
        return f'{self.iniciada_en:%Y-%m-%d %H:%M} · {self.get_origen_display()} · {estado}'
