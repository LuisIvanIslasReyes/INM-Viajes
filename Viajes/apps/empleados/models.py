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

# Sin sexo capturado, el título decide (mismo criterio que la Estancia en sus oficios).
TITULOS_FEMENINOS = {'MTRA', 'DRA'}

# Copia de `apps/Personal/plazas.py` de la Estancia (D-144): solo la primera palabra
# y con un diccionario cerrado; lo que no está (SUB REPRESENTANTE, AGENTE, ANALISTA,
# OFICIAL, TITULAR…) ya es invariable o no se adivina. Si allá cambia, copiar aquí.
FEMENINO_PRIMERA_PALABRA = {
    'JEFE': 'JEFA',
    'SUBJEFE': 'SUBJEFA',
    'DIRECTOR': 'DIRECTORA',
    'SUBDIRECTOR': 'SUBDIRECTORA',
    'COORDINADOR': 'COORDINADORA',
    'SUPERVISOR': 'SUPERVISORA',
    'DICTAMINADOR': 'DICTAMINADORA',
    'TÉCNICO': 'TÉCNICA',
    'TECNICO': 'TECNICA',
    'ENCARGADO': 'ENCARGADA',
}


def plaza_en_femenino(texto):
    """'JEFE DE DEPARTAMENTO' → 'JEFA DE DEPARTAMENTO'; si no aplica, igual."""
    palabras = (texto or '').split(' ', 1)
    femenino = FEMENINO_PRIMERA_PALABRA.get(palabras[0].upper())
    if not femenino:
        return texto or ''
    return ' '.join([femenino, *palabras[1:]])


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
    plaza = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Puesto genérico de la plaza en la Estancia (ej. JEFE DE DEPARTAMENTO).',
    )
    plaza_descripcion = models.CharField(
        max_length=250, blank=True, default='',
        help_text='La plaza concreta (ej. JEFATURA DE DEPARTAMENTO DE RECURSOS HUMANOS).',
    )
    jerarquia = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Jerarquía principal vigente en la Estancia (la labor, ej. AFM).',
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

    @property
    def es_mujer(self):
        if self.sexo:
            return self.sexo == self.Sexo.FEMENINO
        return self.titulo_academico in TITULOS_FEMENINOS

    @property
    def cargo(self):
        """El puesto que se imprime bajo la firma (mismo criterio que la Estancia, D-144).

        Manda la plaza, en femenino si firma una mujer; sin plaza, la jerarquía.
        """
        puesto = ' '.join((self.plaza or '').upper().split())
        if puesto:
            return plaza_en_femenino(puesto) if self.es_mujer else puesto
        return ' '.join((self.jerarquia or '').upper().split())


class SincronizacionEmpleados(models.Model):
    """Bitácora de cada intento de sincronización (para saber qué tan fresca está la réplica)."""

    class Origen(models.TextChoices):
        PROGRAMADA = 'PROGRAMADA', 'Tarea programada'
        MANUAL = 'MANUAL', 'Botón "Sincronizar ahora"'

    class Modo(models.TextChoices):
        COMPLETA = 'COMPLETA', 'Completa'
        INCREMENTAL = 'INCREMENTAL', 'Incremental'

    origen = models.CharField(max_length=12, choices=Origen.choices)
    modo = models.CharField(max_length=12, choices=Modo.choices, default=Modo.COMPLETA)
    proximo_desde = models.DateTimeField(
        null=True, blank=True,
        help_text='Lo devuelve la Estancia; la siguiente incremental pide los cambios desde aquí.',
    )
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
