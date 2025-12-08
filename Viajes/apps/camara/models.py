from django.db import models
from django.contrib.auth.models import User


class FotoRechazo(models.Model):
    """Foto de pasajero rechazado"""
    # Relación con el registro rechazado
    registro = models.ForeignKey(
        'uploader.Registro', 
        on_delete=models.CASCADE, 
        related_name='fotos_rechazo'
    )
    
    # Archivo de imagen
    foto = models.ImageField(
        upload_to='rechazos/%Y/%m/%d/',
        help_text='Foto del documento o pasajero rechazado'
    )
    
    # Metadata
    fecha_captura = models.DateTimeField(auto_now_add=True)
    usuario_captura = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Usuario que subió la foto'
    )
    
    # Notas opcionales
    notas = models.TextField(
        blank=True, 
        null=True,
        help_text='Notas adicionales sobre la foto'
    )
    
    class Meta:
        verbose_name = 'Foto de Rechazo'
        verbose_name_plural = 'Fotos de Rechazos'
        ordering = ['-fecha_captura']
        indexes = [
            models.Index(fields=['registro', '-fecha_captura']),
        ]
    
    def __str__(self):
        return f"Foto de {self.registro.nombre_pasajero} - {self.fecha_captura.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def nombre_archivo(self):
        """Obtener solo el nombre del archivo sin la ruta"""
        import os
        return os.path.basename(self.foto.name)