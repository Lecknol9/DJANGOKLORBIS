from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PerfilEmpleado(models.Model):
    CARGO_CHOICES = [
        ('empleado', 'Empleado'),
        ('supervisor', 'Supervisor'),
        ('gerente', 'Gerente'),
        ('director', 'Director'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    cargo = models.CharField(
        max_length=20,
        choices=CARGO_CHOICES,
        default='empleado',
        verbose_name="Cargo"
    )
    fecha_ingreso = models.DateField(
        verbose_name="Fecha de Ingreso"
    )
    telefono = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    departamento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Departamento"
    )
    salario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Salario"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        verbose_name = "Perfil de Empleado"
        verbose_name_plural = "Perfiles de Empleados"
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_cargo_display()}"

    def clean(self):
        """Validaciones personalizadas"""
        if self.telefono and not self.telefono.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValidationError({'telefono': 'El teléfono debe contener solo números, espacios, guiones y el signo +'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    # Métodos para verificar jerarquía de cargos
    def es_admin(self):
        """Verifica si es administrador"""
        return self.cargo == 'admin'
    
    def es_director(self):
        """Verifica si es director"""
        return self.cargo == 'director'
    
    def es_gerente(self):
        """Verifica si es gerente"""
        return self.cargo == 'gerente'
    
    def es_supervisor(self):
        """Verifica si es supervisor"""
        return self.cargo == 'supervisor'
    
    def es_empleado(self):
        """Verifica si es empleado base"""
        return self.cargo == 'empleado'

    # Métodos para verificar permisos jerárquicos
    def es_director_o_superior(self):
        """Verifica si es director o administrador"""
        return self.cargo in ['director', 'admin']
    
    def es_gerente_o_superior(self):
        """Verifica si es gerente, director o administrador"""
        return self.cargo in ['gerente', 'director', 'admin']
    
    def es_supervisor_o_superior(self):
        """Verifica si es supervisor o superior"""
        return self.cargo in ['supervisor', 'gerente', 'director', 'admin']

    def puede_gestionar_usuario(self, otro_perfil):
        """Verifica si puede gestionar a otro usuario basado en la jerarquía"""
        jerarquia = {
            'empleado': 0,
            'supervisor': 1,
            'gerente': 2,
            'director': 3,
            'admin': 4
        }
        
        mi_nivel = jerarquia.get(self.cargo, 0)
        otro_nivel = jerarquia.get(otro_perfil.cargo, 0)
        
        return mi_nivel > otro_nivel

    @property
    def nivel_acceso(self):
        """Retorna el nivel de acceso numérico"""
        niveles = {
            'empleado': 1,
            'supervisor': 2,
            'gerente': 3,
            'director': 4,
            'admin': 5
        }
        return niveles.get(self.cargo, 1)

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username

    def get_permisos_disponibles(self):
        """Retorna una lista de permisos basados en el cargo"""
        permisos_base = ['ver_perfil', 'editar_perfil']
        
        if self.es_supervisor_o_superior():
            permisos_base.extend(['ver_empleados', 'asignar_tareas'])
        
        if self.es_gerente_o_superior():
            permisos_base.extend(['ver_reportes', 'gestionar_empleados'])
        
        if self.es_director_o_superior():
            permisos_base.extend(['ver_finanzas', 'aprobar_gastos'])
        
        if self.es_admin():
            permisos_base.extend(['gestionar_sistema', 'ver_logs', 'backup_db'])
        
        return permisos_base