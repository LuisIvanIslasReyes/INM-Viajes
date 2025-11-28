from django.db import models
from django.contrib.auth.models import User


class UploadBatch(models.Model):
    """Batch de carga de archivo Excel"""
    archivo = models.FileField(upload_to='uploads/')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Lote de Carga'
        verbose_name_plural = 'Lotes de Carga'
        ordering = ['-fecha_carga']
    
    def __str__(self):
        return f"Carga {self.id} - {self.usuario.username} - {self.fecha_carga.strftime('%Y-%m-%d %H:%M')}"


class Registro(models.Model):
    """Registro individual de pasajero desde Excel"""
    # Relación con el batch de carga
    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name='registros')
    
    # Campos del Excel (20 campos)
    vuelo_numero = models.CharField(max_length=50, verbose_name='航班号')
    vuelo_fecha = models.DateTimeField(verbose_name='航班日期', null=True, blank=True)
    aeropuerto_salida = models.CharField(max_length=50, verbose_name='起飞机场')
    aeropuerto_llegada = models.CharField(max_length=50, verbose_name='落地机场')
    salida_planificada = models.CharField(max_length=50, verbose_name='计划离港', blank=True, null=True)
    nombre_pasajero = models.CharField(max_length=200, verbose_name='旅客姓名')
    numero_documento = models.CharField(max_length=100, verbose_name='证件号')
    numero_asiento = models.CharField(max_length=20, verbose_name='座位号')
    numero_equipaje = models.TextField(verbose_name='行李号', blank=True, null=True)
    piezas = models.IntegerField(verbose_name='件数', default=0)
    peso = models.IntegerField(verbose_name='重量', default=0)
    estado_checkin = models.CharField(max_length=50, verbose_name='值机状态')
    informacion_contacto = models.TextField(verbose_name='联系信息', blank=True, null=True)
    contacto_reserva = models.CharField(max_length=100, verbose_name='预订人联系方式', blank=True, null=True)
    contacto_pasajero = models.CharField(max_length=100, verbose_name='乘机人联系方式', blank=True, null=True)
    numero_ticket = models.CharField(max_length=100, verbose_name='票号')
    fecha_nacimiento = models.DateField(verbose_name='旅客生日', blank=True, null=True)
    genero = models.CharField(max_length=10, verbose_name='性别')
    codigo_pais_emision = models.CharField(max_length=10, verbose_name='签发国编码')
    pais_emision = models.CharField(max_length=100, verbose_name='签发国')
    
    # Campos administrativos (4 campos)
    segunda_revision = models.BooleanField(default=False, verbose_name='Segunda Revisión (SR)')
    rechazado = models.BooleanField(default=False, verbose_name='Rechazo (R)')
    internacion = models.BooleanField(default=False, verbose_name='Punto de Internación (PI)')
    comentario = models.TextField(blank=True, null=True, verbose_name='Comentario')
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Registro de Pasajero'
        verbose_name_plural = 'Registros de Pasajeros'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre_pasajero} - {self.vuelo_numero} - {self.numero_documento}"


class CasoEspecial(models.Model):
    """Casos especiales de registros con documentos duplicados que requieren validación"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('aceptado', 'Aceptado por Admin'),
        ('editado', 'Documento Editado'),
        ('inadmitido', 'Marcado como Inadmitido'),
        ('eliminado', 'Eliminado'),
    ]
    
    RAZON_CHOICES = [
        ('documento_duplicado', 'Número de Documento Duplicado'),
        ('mismo_vuelo_fecha', 'Mismo Vuelo y Fecha'),
        ('datos_sospechosos', 'Datos Sospechosos'),
    ]
    
    # Registro afectado
    registro = models.OneToOneField(
        Registro, 
        on_delete=models.CASCADE, 
        related_name='caso_especial',
        verbose_name='Registro'
    )
    
    # Motivo del caso especial
    razon = models.CharField(
        max_length=50, 
        choices=RAZON_CHOICES, 
        default='documento_duplicado',
        verbose_name='Razón'
    )
    
    # Estado actual
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente',
        verbose_name='Estado'
    )
    
    # Registro(s) conflictivo(s) - IDs de los registros que tienen el mismo documento
    registros_conflictivos_ids = models.JSONField(
        default=list,
        verbose_name='IDs de Registros Conflictivos',
        help_text='Lista de IDs de registros con el mismo documento'
    )
    
    # Información adicional
    documento_original = models.CharField(
        max_length=100, 
        verbose_name='Documento Original',
        help_text='Número de documento que causó el conflicto'
    )
    
    documento_nuevo = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Documento Nuevo',
        help_text='Nuevo número de documento si fue editado'
    )
    
    # Notas administrativas
    notas_admin = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Notas del Administrador'
    )
    
    # Usuario que resolvió el caso
    resuelto_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='casos_resueltos',
        verbose_name='Resuelto Por'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Resolución')
    
    class Meta:
        verbose_name = 'Caso Especial'
        verbose_name_plural = 'Casos Especiales'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['documento_original']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Caso #{self.id} - {self.registro.nombre_pasajero} ({self.get_estado_display()})"
    
    @property
    def registros_conflictivos(self):
        """Obtener los registros conflictivos reales"""
        if self.registros_conflictivos_ids:
            return Registro.objects.filter(id__in=self.registros_conflictivos_ids)
        return Registro.objects.none()
    
    @property
    def es_pendiente(self):
        return self.estado == 'pendiente'
    
    @property
    def esta_resuelto(self):
        return self.estado in ['aceptado', 'editado', 'inadmitido', 'eliminado']
