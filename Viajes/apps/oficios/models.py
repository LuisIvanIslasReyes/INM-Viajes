"""
Oficios de Viajes (fase 2): expedientes de familia y sus oficios por persona.

Flujo:
  Expediente (familia) ── firmante + 2 testigos (empleados.Empleado)
   └─ PersonaExpediente (cada extranjero; datos precargados de uploader.Registro
      o capturados a mano, siempre editables)
       └─ OficioInstancia (un oficio de una plantilla para esa persona): borrador con
          su propio texto editable; al imprimir se congela (snap_contexto + .docx).

El texto base de cada formato vive en PlantillaOficio (HTML con {{variables}}). El
membrete, el bloque institucional, el título, la fecha y las firmas los arma el
código (services/docx_oficio.py), no el texto editable.

Todo es por persona (decisión del usuario, 24/11/2026). Ver Docs/EMPLEADOS_Y_OFICIOS.md.
"""
from pathlib import Path

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

ASSETS = Path(__file__).resolve().parent / 'assets'
HOJA_MEMBRETADA_DEFAULT = ASSETS / 'hoja_membretada_2026.png'


class Idioma(models.TextChoices):
    ESPANOL = 'es', 'Español'
    CHINO = 'zh', 'Chino'
    RUSO = 'ru', 'Ruso'
    FRANCES = 'fr', 'Francés'
    INGLES = 'en', 'Inglés'
    ARABE = 'ar', 'Árabe'


# Cómo se nombra el idioma dentro del texto del oficio ("…para traducir al idioma chino").
IDIOMA_EN_TEXTO = {
    Idioma.ESPANOL: 'español',
    Idioma.CHINO: 'chino',
    Idioma.RUSO: 'ruso',
    Idioma.FRANCES: 'francés',
    Idioma.INGLES: 'inglés',
    Idioma.ARABE: 'árabe',
}


class DatosOficina(models.Model):
    """Datos fijos de la oficina que imprimen todos los oficios. Se usa la primera fila."""

    entidad = models.CharField(max_length=100, default='BAJA CALIFORNIA')
    aeropuerto = models.CharField(max_length=150, default='AEROPUERTO INTERNACIONAL DE TIJUANA')
    terminal = models.CharField(max_length=100, blank=True, default='SALA INTERNACIONAL')
    ciudad_encabezado = models.CharField(
        max_length=100, default='Tijuana, Baja California',
        help_text='La que va antes de la fecha, arriba a la derecha.',
    )
    ciudad = models.CharField(
        max_length=100, default='Tijuana, B.C.', help_text='La que se usa dentro del texto ("En Tijuana, B.C., …").',
    )
    domicilio = models.CharField(
        max_length=250,
        default='Carretera Aeropuerto s/n, Col. Nueva Tijuana, Tijuana, B.C., C.P. 22435',
    )
    actualizado_en = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        verbose_name = 'Datos de la oficina'
        verbose_name_plural = 'Datos de la oficina'

    def __str__(self):
        return f'{self.aeropuerto} ({self.entidad})'

    @classmethod
    def actual(cls):
        """La fila configurada, o una sin guardar con los valores por defecto."""
        return cls.objects.order_by('pk').first() or cls()


class HojaMembretada(models.Model):
    """Imagen de página completa (carta) que va detrás del texto. Solo una activa.

    Si no hay ninguna, se usa la de 2026 que viene en `assets/` (la de los Word oficiales).
    """

    imagen = models.ImageField(upload_to='oficios/membrete/')
    descripcion = models.CharField(max_length=100, blank=True, default='', help_text='Ej. "2026 Margarita Maza".')
    activo = models.BooleanField(default=True)
    subida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hoja membretada'
        verbose_name_plural = 'Hojas membretadas'
        ordering = ['-subida_en']

    def __str__(self):
        return self.descripcion or f'Hoja membretada {self.subida_en:%Y-%m-%d}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.activo:
            HojaMembretada.objects.exclude(pk=self.pk).filter(activo=True).update(activo=False)

    @classmethod
    def ruta_actual(cls):
        """Ruta en disco de la hoja activa (o la de 2026 incluida en el proyecto)."""
        activa = cls.objects.filter(activo=True).first()
        if activa and activa.imagen:
            try:
                ruta = Path(activa.imagen.path)
                if ruta.exists():
                    return ruta
            except (NotImplementedError, ValueError):
                pass
        return HOJA_MEMBRETADA_DEFAULT


class MotivoRechazo(models.Model):
    """Supuestos de rechazo del oficio 11 (catálogo del Word oficial)."""

    texto = models.CharField(max_length=300)
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Motivo de rechazo'
        verbose_name_plural = 'Motivos de rechazo'
        ordering = ['orden', 'pk']

    def __str__(self):
        return self.texto


class PlantillaOficio(models.Model):
    """Un formato (02–14): texto base editable con {{variables}} y su bloque de firmas."""

    class BloqueFirmas(models.TextChoices):
        CONSTANCIA = 'CONSTANCIA', 'Constancia: autoridad, persona extranjera y 2 testigos'
        NOTIFICACION = 'NOTIFICACION', 'Notificación: atentamente y "recibí original"'
        EMPRESA = 'EMPRESA', 'Empresa: representante de la aerolínea y autoridad'
        AUTORIDAD_PERSONA = 'AUTORIDAD_PERSONA', 'Autoridad y persona extranjera (sin testigos)'
        ACUERDO = 'ACUERDO', 'Acuerdo: autoridad, persona, representante de la aerolínea y 2 testigos'
        NINGUNO = 'NINGUNO', 'Sin firmas'

    numero = models.DecimalField(max_digits=4, decimal_places=1, unique=True, help_text='Ej. 2, 11 o 4.1.')
    nombre = models.CharField(max_length=150, help_text='Nombre corto para las listas.')
    titulo = models.CharField(max_length=250, help_text='Título que se imprime, centrado y en negritas.')
    contenido_html = models.TextField(blank=True, default='')
    bloque_firmas = models.CharField(max_length=20, choices=BloqueFirmas.choices, default=BloqueFirmas.CONSTANCIA)
    lleva_fecha = models.BooleanField(default=True, help_text='Imprime "Ciudad, fecha." bajo el título.')
    class TipoEvidencia(models.TextChoices):
        NINGUNA = '', 'Sin evidencias'
        VERIFICACION = 'VERIFICACION', 'Verificación (a quién, hora, respuesta, intentos) y foto'
        FOTO = 'FOTO', 'Foto y observaciones'

    evidencias = models.CharField(
        max_length=12, choices=TipoEvidencia.choices, blank=True, default='',
        help_text='Si el formato lleva evidencias de la persona; se imprimen donde el texto dice [[ EVIDENCIAS ]].',
    )
    tamano_letra_pt = models.DecimalField(
        'tamaño de letra (pt)', max_digits=3, decimal_places=1, default=Decimal('10'),
        validators=[MinValueValidator(Decimal('8')), MaxValueValidator(Decimal('12'))],
        help_text='El del Word oficial (9 a 10 pt). Más chico si el oficio no cabe en sus hojas.',
    )
    activo = models.BooleanField(default=True)
    modificado_en = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        verbose_name = 'Plantilla de oficio'
        verbose_name_plural = 'Plantillas de oficio'
        ordering = ['numero']

    def __str__(self):
        return f'{self.clave}. {self.nombre}'

    @property
    def clave(self):
        """'02', '11'; con decimal, '04.1'."""
        entero = int(self.numero)
        return f'{entero:02d}' if self.numero == entero else f'{entero:02d}.{str(self.numero).split(".")[1].rstrip("0")}'

    @property
    def requiere_testigos(self):
        return self.bloque_firmas in (self.BloqueFirmas.CONSTANCIA, self.BloqueFirmas.ACUERDO)

    def variante(self, idioma):
        """La traducción activa a `idioma`, o None (entonces el oficio sale en español)."""
        if not idioma or idioma == Idioma.ESPANOL:
            return None
        return self.variantes.filter(idioma=idioma, activo=True).first()


class PlantillaOficioIdioma(models.Model):
    """Traducción de un formato a un idioma: una copia bilingüe completa (español + traducción).

    Se captura UNA vez (la pegan los agentes) y se usa en todos los oficios futuros de
    personas con ese idioma. Si no hay traducción, el oficio sale en español.
    Decisión del usuario (24/11): la base es el español; solo SuperUser y Aeropuerto la editan.
    """

    plantilla = models.ForeignKey(PlantillaOficio, on_delete=models.CASCADE, related_name='variantes')
    idioma = models.CharField(max_length=2, choices=[c for c in Idioma.choices if c[0] != Idioma.ESPANOL])
    titulo = models.CharField(
        max_length=300, blank=True, default='',
        help_text='Título bilingüe, ej. "CONSTANCIA … (Chino) / 使用电子翻译器的证明". Vacío: el de la plantilla.',
    )
    contenido_html = models.TextField(
        blank=True, default='',
        help_text='Texto bilingüe con las mismas {{variables}}. Vacío: el mismo texto en español de la plantilla.',
    )
    leyenda_firma_persona = models.CharField(
        max_length=150, blank=True, default='',
        help_text='Bajo la firma de la persona extranjera, ej. "NOMBRE Y FIRMA / 姓名和签名".',
    )
    activo = models.BooleanField(default=True)
    modificado_en = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        verbose_name = 'Traducción de plantilla'
        verbose_name_plural = 'Traducciones de plantillas'
        ordering = ['plantilla__numero', 'idioma']
        constraints = [
            models.UniqueConstraint(fields=['plantilla', 'idioma'], name='una_traduccion_por_idioma'),
        ]

    def __str__(self):
        return f'{self.plantilla.clave} · {self.get_idioma_display()}'


class PlantillaHistorial(models.Model):
    """Cada versión guardada de una plantilla (idioma 'es') o de una traducción."""

    plantilla = models.ForeignKey(PlantillaOficio, on_delete=models.CASCADE, related_name='historial')
    idioma = models.CharField(max_length=2, choices=Idioma.choices, default=Idioma.ESPANOL)
    titulo = models.CharField(max_length=300, blank=True, default='')
    contenido_html = models.TextField(blank=True, default='')
    leyenda_firma_persona = models.CharField(max_length=150, blank=True, default='')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Versión de plantilla'
        verbose_name_plural = 'Versiones de plantillas'
        ordering = ['-fecha_hora', '-pk']

    def __str__(self):
        return f'{self.plantilla.clave} · {self.get_idioma_display()} · {self.fecha_hora:%Y-%m-%d %H:%M}'


class Expediente(models.Model):
    """Expediente de una familia (o de una sola persona). Un firmante y 2 testigos para todos sus oficios."""

    class Resultado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        INTERNACION = 'INTERNACION', 'Internación'
        RECHAZO = 'RECHAZO', 'Rechazo'

    folio = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    fecha = models.DateField(default=timezone.localdate)
    resultado = models.CharField(max_length=12, choices=Resultado.choices, default=Resultado.PENDIENTE)
    firmante = models.ForeignKey(
        'empleados.Empleado', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    testigo_1 = models.ForeignKey(
        'empleados.Empleado', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    testigo_2 = models.ForeignKey(
        'empleados.Empleado', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Expediente'
        verbose_name_plural = 'Expedientes'
        ordering = ['-creado_en']

    def __str__(self):
        return self.folio or f'Expediente {self.pk}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.folio:
            # El id ya existe: folio corto, legible y sin carreras entre usuarios.
            self.folio = f'VJ-{self.fecha:%Y}-{self.pk:04d}'
            super().save(update_fields=['folio'])


class PersonaExpediente(models.Model):
    """Un extranjero del expediente. `registro` solo sirve para precargar: los datos aquí mandan."""

    class Sexo(models.TextChoices):
        MASCULINO = 'M', 'Masculino'
        FEMENINO = 'F', 'Femenino'

    expediente = models.ForeignKey(Expediente, on_delete=models.CASCADE, related_name='personas')
    registro = models.ForeignKey(
        'uploader.Registro', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    nombre = models.CharField(max_length=200)
    nacionalidad = models.CharField(max_length=100, blank=True, default='')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    documento = models.CharField('pasaporte o documento', max_length=100, blank=True, default='')
    sexo = models.CharField(max_length=1, choices=Sexo.choices, blank=True, default='')
    vuelo = models.CharField(max_length=50, blank=True, default='')
    fecha_arribo = models.DateField(null=True, blank=True)
    origen = models.CharField(max_length=100, blank=True, default='', help_text='Ej. PEKÍN, CHINA.')
    aerolinea = models.CharField(max_length=150, blank=True, default='')
    idioma = models.CharField(max_length=2, choices=Idioma.choices, default=Idioma.ESPANOL)
    numero_acta = models.CharField(max_length=60, blank=True, default='', help_text='Ej. ORBC/AIMMTJ/AR000316/2026.')
    sala_entrevista = models.CharField(max_length=20, blank=True, default='')
    motivo_rechazo = models.ForeignKey(MotivoRechazo, on_delete=models.PROTECT, null=True, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Persona del expediente'
        verbose_name_plural = 'Personas del expediente'
        ordering = ['orden', 'pk']

    def __str__(self):
        return self.nombre


class Evidencia(models.Model):
    """Una evidencia que presenta la persona para un formato (09: verificación de información; 05: médica).

    Sugerencia del usuario (25/11): de 1 a N evidencias, cada una con su espacio en el oficio.
    Va en la persona (no en el oficio) para poder capturarla antes de crear el borrador.
    """

    class Respuesta(models.TextChoices):
        SIN_DATO = '', 'Sin dato'
        SI = 'SI', 'Sí'
        NO = 'NO', 'No'

    persona = models.ForeignKey(PersonaExpediente, on_delete=models.CASCADE, related_name='evidencias')
    plantilla = models.ForeignKey(PlantillaOficio, on_delete=models.PROTECT, related_name='+')
    orden = models.PositiveSmallIntegerField(default=0)
    verificacion_a = models.CharField(
        'verificación realizada a', max_length=250, blank=True, default='',
        help_text='Persona que invita, empresa, hotel, aerolínea, sitio oficial…',
    )
    hora = models.CharField(max_length=10, blank=True, default='', help_text='HH:MM')
    respuesta = models.CharField('¿se recibió respuesta?', max_length=2, choices=Respuesta.choices, blank=True, default='')
    intentos = models.PositiveSmallIntegerField('número de intentos', null=True, blank=True)
    nota = models.TextField('observaciones', blank=True, default='')
    foto = models.ImageField(upload_to='oficios/evidencias/%Y/%m/', null=True, blank=True)
    foto_rechazo = models.ForeignKey(
        'camara.FotoRechazo', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        help_text='Foto de la app Cámara de la que se tomó.',
    )
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['orden', 'pk']

    def __str__(self):
        return f'{self.plantilla.clave} · {self.persona.nombre} · {self.verificacion_a or self.nota[:30] or "foto"}'


class OficioInstancia(models.Model):
    """El oficio de una plantilla para una persona: borrador editable que se congela al imprimir."""

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        IMPRESO = 'IMPRESO', 'Impreso'

    persona = models.ForeignKey(PersonaExpediente, on_delete=models.CASCADE, related_name='oficios')
    plantilla = models.ForeignKey(PlantillaOficio, on_delete=models.PROTECT, related_name='instancias')
    idioma = models.CharField(max_length=2, choices=Idioma.choices, default=Idioma.ESPANOL)
    contenido_html = models.TextField(blank=True, default='')
    testigo_1 = models.ForeignKey(
        'empleados.Empleado', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
        help_text='Solo si en este oficio cambia; si no, el del expediente.',
    )
    testigo_2 = models.ForeignKey(
        'empleados.Empleado', on_delete=models.PROTECT, null=True, blank=True, related_name='+',
        help_text='Solo si en este oficio cambia; si no, el del expediente.',
    )
    fecha_oficio = models.DateField(default=timezone.localdate)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    snap_contexto = models.JSONField(null=True, blank=True, help_text='Variables congeladas al imprimir.')
    snap_formato = models.JSONField(
        null=True, blank=True,
        help_text='Título, firmas y fecha de la plantilla al imprimir (por si después cambia la plantilla).',
    )
    docx_impreso = models.FileField(upload_to='oficios/impresos/%Y/%m/', null=True, blank=True)
    impreso_en = models.DateTimeField(null=True, blank=True)
    impreso_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Oficio'
        verbose_name_plural = 'Oficios'
        ordering = ['persona__orden', 'persona_id', 'plantilla__numero']
        constraints = [
            models.UniqueConstraint(fields=['persona', 'plantilla'], name='oficio_unico_por_persona'),
        ]

    def __str__(self):
        return f'{self.plantilla.clave} · {self.persona.nombre}'

    @property
    def editable(self):
        return self.estado == self.Estado.BORRADOR

    @property
    def expediente(self):
        return self.persona.expediente

    @property
    def testigos(self):
        """(testigo 1, testigo 2) de este oficio: el propio si se cambió, si no el del expediente."""
        exp = self.persona.expediente
        return (self.testigo_1 or exp.testigo_1, self.testigo_2 or exp.testigo_2)


class OficioHistorial(models.Model):
    class Accion(models.TextChoices):
        CREADO = 'CREADO', 'Creado'
        EDITADO = 'EDITADO', 'Editado'
        IMPRESO = 'IMPRESO', 'Marcado como impreso'
        REABIERTO = 'REABIERTO', 'Reabierto'

    instancia = models.ForeignKey(OficioInstancia, on_delete=models.CASCADE, related_name='historial')
    accion = models.CharField(max_length=10, choices=Accion.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Historial de oficio'
        verbose_name_plural = 'Historial de oficios'
        ordering = ['-fecha_hora', '-pk']

    def __str__(self):
        return f'{self.get_accion_display()} · {self.fecha_hora:%Y-%m-%d %H:%M}'
