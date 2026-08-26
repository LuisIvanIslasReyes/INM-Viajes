import os

from django.contrib.auth.models import User
from django.db import models


class ResolucionChoices(models.TextChoices):
    """Catálogo cerrado de resolución (mismo concepto que en Directorio)."""
    INTERNACION = 'INTERNACION', 'Internación'
    RECHAZO = 'RECHAZO', 'Rechazo'


class TipoContenidoChoices(models.TextChoices):
    """Origen del contenido de la redacción: archivo subido o texto pegado."""
    ARCHIVO = 'ARCHIVO', 'Archivo'
    TEXTO = 'TEXTO', 'Texto pegado'


TEXTO_CRUDO_MAX_CARACTERES = 300_000  # tope defensivo; la validación real vive en el form


class Pais(models.Model):
    """Catálogo de países (sembrado desde context/paises.json)."""
    codigo = models.CharField(max_length=3, unique=True)  # ISO alfa-3
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Redaccion(models.Model):
    """
    Documento reutilizable (acta, oficio, etc.) de la biblioteca compartida.

    El campo `tema` es texto libre por ahora (se normaliza a mayúsculas para facilitar
    una futura migración a un catálogo `Tema`). Para la vista previa se conserva un
    render PDF en `archivo_pdf`; si el documento ya es PDF, se usa el propio archivo.
    """
    titulo = models.CharField(max_length=200, verbose_name='Título')
    resolucion = models.CharField(
        max_length=12, choices=ResolucionChoices.choices, verbose_name='Resolución',
    )
    tema = models.CharField(max_length=160, verbose_name='Tema')
    pais = models.ForeignKey(
        Pais, on_delete=models.PROTECT, related_name='redacciones', verbose_name='País',
    )
    tipo_contenido = models.CharField(
        max_length=10, choices=TipoContenidoChoices.choices,
        default=TipoContenidoChoices.ARCHIVO, verbose_name='Tipo de contenido',
    )
    archivo = models.FileField(upload_to='redacciones/%Y/%m/', blank=True, verbose_name='Documento')
    archivo_pdf = models.FileField(
        upload_to='redacciones/pdf/%Y/%m/', null=True, blank=True,
        verbose_name='PDF para vista previa',
    )
    subido_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='redacciones',
    )
    texto_contenido = models.TextField(
        blank=True, default='', editable=False,
        verbose_name='Texto extraído del documento',
        help_text='Texto plano extraído del PDF para el buscador de palabras.',
    )
    texto_crudo = models.TextField(
        blank=True, verbose_name='Texto pegado',
        help_text='Contenido de la redacción pegado directamente (sin archivo).',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Redacción'
        verbose_name_plural = 'Redacciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['resolucion', 'pais']),
            models.Index(fields=['tema']),
        ]

    def __str__(self):
        return self.titulo

    @property
    def es_archivo(self):
        return self.tipo_contenido == TipoContenidoChoices.ARCHIVO

    @property
    def es_texto(self):
        return self.tipo_contenido == TipoContenidoChoices.TEXTO

    @property
    def extension(self):
        return os.path.splitext(self.archivo.name)[1].lower().lstrip('.') if self.archivo else ''

    @property
    def es_pdf(self):
        return self.extension == 'pdf'

    @property
    def preview_url(self):
        """URL del PDF para vista previa, o None si no hay preview disponible."""
        if self.es_texto:
            return None
        if self.es_pdf and self.archivo:
            return self.archivo.url
        if self.archivo_pdf:
            return self.archivo_pdf.url
        return None

    def save(self, *args, **kwargs):
        # Normaliza el tema (trim + colapsa espacios + mayúsculas) de cara al
        # futuro catálogo y para consistencia en los filtros.
        self.tema = ' '.join((self.tema or '').split()).upper()
        if self.tipo_contenido == TipoContenidoChoices.TEXTO:
            # El texto pegado ES el documento: se sincroniza como el campo de
            # búsqueda para que el buscador de palabras funcione igual que con
            # el texto extraído de un PDF, sin tocar la lógica de búsqueda.
            self.texto_contenido = ' '.join((self.texto_crudo or '').split())[:TEXTO_CRUDO_MAX_CARACTERES]
        super().save(*args, **kwargs)
