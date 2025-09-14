from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    atencion = models.CharField(max_length=200, blank=True, null=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class TipoTrabajo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class CategoriaServicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

class ServicioBase(models.Model):
    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unidad = models.CharField(max_length=50, default='UND')
    es_parametrizable = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.categoria.nombre} - {self.nombre}"

class ParametroServicio(models.Model):
    TIPO_CHOICES = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('select', 'Selección'),
        ('boolean', 'Sí/No'),
    ]
    
    servicio = models.ForeignKey(ServicioBase, on_delete=models.CASCADE, related_name='parametros')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    requerido = models.BooleanField(default=True)
    opciones = models.TextField(blank=True, null=True, help_text="Para tipo select: opcion1,opcion2,opcion3")
    valor_por_defecto = models.CharField(max_length=200, blank=True, null=True)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['orden', 'nombre']

    def __str__(self):
        return f"{self.servicio.nombre} - {self.nombre}"

    def get_opciones_list(self):
        if self.opciones:
            return [opt.strip() for opt in self.opciones.split(',')]
        return []

class Material(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unidad = models.CharField(max_length=50, default='UND')
    categoria = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    referencia = models.TextField()
    lugar = models.CharField(max_length=200)
    tipo_trabajo = models.ForeignKey(TipoTrabajo, on_delete=models.CASCADE)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    
    # Valores calculados
    subtotal_servicios = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_materiales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_mano_obra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gastos_traslado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    observaciones = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Cotización {self.numero} - {self.cliente.nombre}"

    def calcular_totales(self):
        # Calcular subtotales de servicios
        self.subtotal_servicios = sum(
            item.subtotal for item in self.items_servicio.all()
        )
        
        # Calcular subtotales de materiales
        self.subtotal_materiales = sum(
            item.subtotal for item in self.items_material.all()
        )
        
        # Calcular subtotales de mano de obra
        self.subtotal_mano_obra = sum(
            item.subtotal for item in self.items_mano_obra.all()
        )
        
        # Calcular valor neto
        self.valor_neto = (
            self.subtotal_servicios + 
            self.subtotal_materiales + 
            self.subtotal_mano_obra + 
            self.gastos_traslado
        )
        
        # Calcular IVA (19%)
        self.valor_iva = self.valor_neto * Decimal('0.19')
        
        # Calcular total
        self.valor_total = self.valor_neto + self.valor_iva
        
        self.save()

    def generar_numero(self):
        if not self.numero:
            ultimo_numero = Cotizacion.objects.filter(
                numero__startswith=f"{self.fecha_creacion.year}"
            ).order_by('-numero').first()
            
            if ultimo_numero:
                ultimo_num = int(ultimo_numero.numero.split('-')[-1])
                nuevo_num = ultimo_num + 1
            else:
                nuevo_num = 1
                
            self.numero = f"{self.fecha_creacion.year}-{nuevo_num:04d}"

class ItemServicio(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items_servicio')
    servicio = models.ForeignKey(ServicioBase, on_delete=models.CASCADE)
    descripcion_personalizada = models.TextField(blank=True, null=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

class ParametroItemServicio(models.Model):
    item_servicio = models.ForeignKey(ItemServicio, on_delete=models.CASCADE, related_name='parametros')
    parametro = models.ForeignKey(ParametroServicio, on_delete=models.CASCADE)
    valor = models.TextField()

class ItemMaterial(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items_material')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    descripcion_personalizada = models.TextField(blank=True, null=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['material__categoria', 'material__nombre']

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

class ItemManoObra(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items_mano_obra')
    descripcion = models.TextField()
    horas = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    precio_hora = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.horas * self.precio_hora
        super().save(*args, **kwargs)

class PlantillaCotizacion(models.Model):
    nombre = models.CharField(max_length=200)
    tipo_trabajo = models.ForeignKey(TipoTrabajo, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class ItemPlantillaServicio(models.Model):
    plantilla = models.ForeignKey(PlantillaCotizacion, on_delete=models.CASCADE, related_name='servicios')
    servicio = models.ForeignKey(ServicioBase, on_delete=models.CASCADE)
    cantidad_default = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['orden']

class ConfiguracionEmpresa(models.Model):
    nombre = models.CharField(max_length=200, default="JOSE E. ALVARADO N.")
    descripcion = models.TextField(default="SERVISIOS ELECTROMECANICOS\nINSTALACIÓN, MANTENCIÓN Y REPARACIÓN DE BOMBAS DE AGUA.\nSUPERFICIE Y SUMERGIBLES")
    direccion = models.CharField(max_length=200, default="PJE. SANTA ELISA 2437 OSORNO")
    telefono = models.CharField(max_length=100, default="9-76193683")
    email = models.EmailField(default="J_ALVARADO33@HOTMAIL.COM")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuración de Empresa"
    
    def save(self, *args, **kwargs):
        # Asegurar que solo exista una instancia
        if not self.pk and ConfiguracionEmpresa.objects.exists():
            raise ValidationError('Solo puede existir una configuración de empresa')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config