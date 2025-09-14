from django import forms
from django.core.exceptions import ValidationError
from .models import *

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'atencion', 'rut', 'direccion', 'telefono', 'email', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'atencion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Persona de contacto'
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'cliente@email.com'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'referencia', 'lugar', 'tipo_trabajo', 'fecha_vencimiento', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'referencia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la referencia del trabajo',
                'required': True
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación del trabajo',
                'required': True
            }),
            'tipo_trabajo': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones adicionales (opcional)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True).order_by('nombre')
        self.fields['tipo_trabajo'].queryset = TipoTrabajo.objects.filter(activo=True).order_by('nombre')

class ServicioBaseForm(forms.ModelForm):
    class Meta:
        model = ServicioBase
        fields = ['categoria', 'nombre', 'descripcion', 'precio_base', 'unidad', 'es_parametrizable', 'activo']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del servicio'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del servicio'
            }),
            'precio_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UND, MT, KG, etc.'
            }),
            'es_parametrizable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class ParametroServicioForm(forms.ModelForm):
    class Meta:
        model = ParametroServicio
        fields = ['nombre', 'tipo', 'requerido', 'opciones', 'valor_por_defecto', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del parámetro'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'requerido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Para tipo select: opción1,opción2,opción3'
            }),
            'valor_por_defecto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valor por defecto (opcional)'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['codigo', 'nombre', 'descripcion', 'precio_unitario', 'unidad', 'categoria', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del material'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del material'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UND, MT, KG, etc.'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Categoría del material'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class TipoTrabajoForm(forms.ModelForm):
    class Meta:
        model = TipoTrabajo
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del tipo de trabajo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del tipo de trabajo'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class CategoriaServicioForm(forms.ModelForm):
    class Meta:
        model = CategoriaServicio
        fields = ['nombre', 'descripcion', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class PlantillaCotizacionForm(forms.ModelForm):
    class Meta:
        model = PlantillaCotizacion
        fields = ['nombre', 'tipo_trabajo', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la plantilla'
            }),
            'tipo_trabajo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la plantilla'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class ConfiguracionEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = ['nombre', 'descripcion', 'direccion', 'telefono', 'email', 'logo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de servicios'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@empresa.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

# Formsets para manejar múltiples items
from django.forms import inlineformset_factory

ParametroServicioFormSet = inlineformset_factory(
    ServicioBase,
    ParametroServicio,
    form=ParametroServicioForm,
    extra=1,
    can_delete=True,
    fields=['nombre', 'tipo', 'requerido', 'opciones', 'valor_por_defecto', 'orden']
)

ItemPlantillaServicioFormSet = inlineformset_factory(
    PlantillaCotizacion,
    ItemPlantillaServicio,
    fields=['servicio', 'cantidad_default', 'orden'],
    extra=1,
    can_delete=True,
    widgets={
        'servicio': forms.Select(attrs={'class': 'form-control'}),
        'cantidad_default': forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        'orden': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        })
    }
)