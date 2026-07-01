import re

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


class ResolucionChoices(models.TextChoices):
    """Catálogo cerrado de tentativa de resolución (compartido conceptualmente
    con el módulo Redacciones)."""
    INTERNACION = 'INTERNACION', 'Internación'
    RECHAZO = 'RECHAZO', 'Rechazo'


class EstadoMexico(models.Model):
    """Catálogo cerrado de los 32 estados de México (sembrado por migración)."""
    clave = models.CharField(max_length=5, unique=True)
    nombre = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


telefono_validator = RegexValidator(
    regex=r'^[0-9+()\s\-]{7,20}$',
    message='Teléfono inválido. Usa dígitos y, opcionalmente, + ( ) - y espacios.',
)


class EmpresaDirectorio(models.Model):
    """
    Registro histórico de una empresa que ha participado en procesos migratorios.

    La empresa NO es única: puede repetirse mientras exista una diferencia relevante
    (encargado o teléfono distintos). Una restricción de unicidad sobre la terna
    (empresa, firma_encargado, teléfono) evita duplicados exactos; la vista de alta
    complementa con una búsqueda previa de coincidencias.
    """
    empresa = models.CharField(max_length=200, verbose_name='Empresa')
    domicilio = models.CharField(max_length=255, blank=True, verbose_name='Domicilio')
    estado = models.ForeignKey(
        EstadoMexico, on_delete=models.PROTECT, null=True, blank=True,
        related_name='empresas', verbose_name='Estado',
    )
    ciudad = models.CharField(max_length=120, blank=True, verbose_name='Ciudad')
    firma_encargado = models.CharField(max_length=150, verbose_name='Firma del Encargado')
    telefono = models.CharField(
        max_length=20, blank=True, validators=[telefono_validator], verbose_name='Teléfono',
    )
    tentativa_resolucion = models.CharField(
        max_length=12, choices=ResolucionChoices.choices, blank=True,
        verbose_name='Tentativa de Resolución',
        help_text='Opcional. Puede definirse más adelante.',
    )
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='empresas_directorio',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa (Directorio)'
        verbose_name_plural = 'Directorio de Empresas'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['empresa']),
            models.Index(fields=['empresa', 'tentativa_resolucion']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'firma_encargado', 'telefono'],
                name='uniq_empresa_encargado_tel',
            ),
        ]

    def __str__(self):
        return f'{self.empresa} — {self.firma_encargado} ({self.get_tentativa_resolucion_display()})'

    @staticmethod
    def _normaliza(texto):
        """Recorta y colapsa espacios para que la unicidad sea significativa."""
        return re.sub(r'\s+', ' ', (texto or '').strip())

    def save(self, *args, **kwargs):
        self.empresa = self._normaliza(self.empresa)
        self.firma_encargado = self._normaliza(self.firma_encargado)
        self.telefono = self._normaliza(self.telefono)
        self.ciudad = self._normaliza(self.ciudad)
        self.domicilio = self._normaliza(self.domicilio)
        super().save(*args, **kwargs)
