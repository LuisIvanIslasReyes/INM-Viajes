"""
Réplica local del catálogo de empleados de la Estancia (ProyectoEstancia → Personal).

La fuente de verdad es la Estancia: allá RRHH da de alta, corrige y da de baja.
Aquí solo se copia, para que Viajes siga teniendo el catálogo si la Estancia se
apaga. Por eso los datos del empleado NO se editan en Viajes (se sobrescriben en
cada sincronización); lo único propio de Viajes es `firmante_habitual` y
`fundamento_manual`.

El fundamento legal que se imprime según la plaza de quien firma también es de
Viajes: catálogo `FundamentoPlaza` + reglas en `fundamentos.py`.

Llave de cruce: `id_estancia` (el `id_empleado` de la Estancia). No se usa el número
de empleado porque allá es opcional (registros legacy sin número).

Nunca se borran filas: un empleado dado de baja (o que ya no viene en la respuesta)
queda `activo=False`, porque oficios ya generados pueden mencionarlo.
"""
from django.conf import settings
from django.db import models

from .fundamentos import elegir_fundamento

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


# De dónde sale el fundamento de un empleado (`Empleado.fundamento_origen`).
ORIGEN_MANUAL = 'manual'
ORIGEN_PLAZA = 'plaza'


class FundamentoPlaza(models.Model):
    """Fundamento legal que se imprime en los oficios según la plaza de quien firma.

    Propio de Viajes. Se asigna solo por la plaza (ver `fundamentos.py`) o a mano
    por empleado (`Empleado.fundamento_manual`). Si el Acuerdo cambia, se corrige
    `texto` en el admin; los oficios ya impresos guardan su propia copia.
    """

    clave = models.SlugField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100, help_text='Ej. Representante Local.')
    texto = models.CharField(
        max_length=300,
        help_text='Tal como se imprime en el oficio, ej. "Artículo 14, apartado B, fracciones I, II y III".',
    )
    plaza_empieza_con = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Se asigna solo a las plazas que empiezan con este texto (palabras completas, '
                  'sin importar acentos). Vacío: nunca se asigna solo, únicamente a mano.',
    )
    descripcion_contiene = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Opcional: además, la descripción de la plaza debe contener este texto.',
    )
    activo = models.BooleanField(default=True, help_text='Inactivo: no se asigna ni se imprime.')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Fundamento por plaza'
        verbose_name_plural = 'Fundamentos por plaza'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    @classmethod
    def catalogo(cls):
        """Los fundamentos activos, ya cargados (una consulta)."""
        return list(cls.objects.filter(activo=True))


def precargar_fundamentos(empleados, catalogo=None):
    """Deja el catálogo cargado en cada empleado: una consulta para toda la lista."""
    catalogo = FundamentoPlaza.catalogo() if catalogo is None else catalogo
    for empleado in empleados:
        empleado._catalogo_fundamentos = catalogo
    return catalogo


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
    fundamento_manual = models.ForeignKey(
        FundamentoPlaza, on_delete=models.PROTECT, null=True, blank=True,
        related_name='empleados_asignados',
        help_text='Asignado a mano cuando la plaza no lo determina. Gana sobre el de la plaza. '
                  'No lo toca la sincronización.',
    )
    sincronizado_en = models.DateTimeField()

    # Catálogo de fundamentos ya cargado (lo deja `precargar_fundamentos`); si falta,
    # se consulta la primera vez que se pide el fundamento.
    _catalogo_fundamentos = None

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

    # ---- Fundamento legal (ver fundamentos.py) ----

    def _catalogo(self):
        if self._catalogo_fundamentos is None:
            self._catalogo_fundamentos = FundamentoPlaza.catalogo()
        return self._catalogo_fundamentos

    @property
    def fundamento_de_su_plaza(self):
        """El que le toca por su plaza, sin contar el asignado a mano (o None)."""
        return elegir_fundamento(self.plaza, self.plaza_descripcion, self._catalogo())

    @property
    def fundamento_asignado(self):
        """El asignado a mano, si sigue activo (o None)."""
        if not self.fundamento_manual_id:
            return None
        return next((f for f in self._catalogo() if f.pk == self.fundamento_manual_id), None)

    @property
    def fundamento_aplicable(self):
        """El `FundamentoPlaza` que se imprime: gana el asignado a mano; si no, el de la plaza."""
        return self.fundamento_asignado or self.fundamento_de_su_plaza

    @property
    def fundamento_origen(self):
        """'manual', 'plaza' o '' (sin fundamento)."""
        if self.fundamento_asignado:
            return ORIGEN_MANUAL
        if self.fundamento_de_su_plaza:
            return ORIGEN_PLAZA
        return ''

    @property
    def fundamento(self):
        """El texto que va en el oficio (ej. 'Artículo 14, apartado B, fracciones I, II y III'), o ''."""
        aplicable = self.fundamento_aplicable
        return aplicable.texto if aplicable else ''


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
