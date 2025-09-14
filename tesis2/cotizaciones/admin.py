from django.contrib import admin
from .models import *

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'atencion', 'rut', 'telefono', 'email', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'rut', 'email', 'telefono')
    ordering = ('nombre',)

@admin.register(TipoTrabajo)
class TipoTrabajoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(CategoriaServicio)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activo')
    list_filter = ('activo',)
    ordering = ('orden', 'nombre')

class ParametroServicioInline(admin.TabularInline):
    model = ParametroServicio
    extra = 1

@admin.register(ServicioBase)
class ServicioBaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'unidad', 'es_parametrizable', 'activo')
    list_filter = ('categoria', 'es_parametrizable', 'activo')
    search_fields = ('nombre', 'descripcion')
    inlines = [ParametroServicioInline]

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'precio_unitario', 'unidad', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('categoria', 'nombre')

class ItemServicioInline(admin.TabularInline):
    model = ItemServicio
    extra = 0

class ItemMaterialInline(admin.TabularInline):
    model = ItemMaterial
    extra = 0

class ItemManoObraInline(admin.TabularInline):
    model = ItemManoObra
    extra = 0

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'tipo_trabajo', 'estado', 'valor_total', 'fecha_creacion', 'creado_por')
    list_filter = ('estado', 'tipo_trabajo', 'fecha_creacion', 'creado_por')
    search_fields = ('numero', 'cliente__nombre', 'referencia')
    readonly_fields = ('numero', 'subtotal_servicios', 'subtotal_materiales', 'subtotal_mano_obra', 
                      'valor_neto', 'valor_iva', 'valor_total', 'fecha_creacion')
    inlines = [ItemServicioInline, ItemMaterialInline, ItemManoObraInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(PlantillaCotizacion)
class PlantillaCotizacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_trabajo', 'activa')
    list_filter = ('tipo_trabajo', 'activa')

@admin.register(ConfiguracionEmpresa)
class ConfiguracionEmpresaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not ConfiguracionEmpresa.objects.exists()