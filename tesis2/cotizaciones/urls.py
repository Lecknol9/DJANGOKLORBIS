from django.urls import path
from . import views

app_name = 'cotizaciones'

urlpatterns = [
    # Dashboard y listados principales
    path('', views.dashboard_cotizaciones, name='dashboard'),
    path('lista/', views.lista_cotizaciones, name='lista'),
    
    # CRUD de cotizaciones
    path('crear/', views.crear_cotizacion, name='crear'),
    path('<int:pk>/', views.detalle_cotizacion, name='detalle'),
    path('<int:pk>/editar/', views.editar_cotizacion, name='editar'),
    path('<int:pk>/pdf/', views.generar_pdf_cotizacion, name='generar_pdf'),
    path('<int:pk>/estado/', views.cambiar_estado_cotizacion, name='cambiar_estado'),
    
    # Gestión de items de cotización (AJAX)
    path('<int:cotizacion_pk>/item-servicio/', views.agregar_item_servicio, name='agregar_item_servicio'),
    path('<int:cotizacion_pk>/item-material/', views.agregar_item_material, name='agregar_item_material'),
    path('<int:cotizacion_pk>/item-mano-obra/', views.agregar_item_mano_obra, name='agregar_item_mano_obra'),
    path('<int:cotizacion_pk>/gastos-traslado/', views.actualizar_gastos_traslado, name='actualizar_gastos_traslado'),
    
    # Eliminar items (AJAX)
    path('<int:cotizacion_pk>/item-servicio/<int:item_pk>/eliminar/', views.eliminar_item_servicio, name='eliminar_item_servicio'),
    path('<int:cotizacion_pk>/item-material/<int:item_pk>/eliminar/', views.eliminar_item_material, name='eliminar_item_material'),
    path('<int:cotizacion_pk>/item-mano-obra/<int:item_pk>/eliminar/', views.eliminar_item_mano_obra, name='eliminar_item_mano_obra'),
    
    # APIs para formularios dinámicos
    path('api/categoria/<int:categoria_id>/servicios/', views.obtener_servicios_categoria, name='servicios_categoria'),
    path('api/servicio/<int:servicio_id>/parametros/', views.obtener_parametros_servicio, name='parametros_servicio'),
    
    # Plantillas
    path('<int:cotizacion_pk>/plantilla/<int:plantilla_pk>/aplicar/', views.aplicar_plantilla, name='aplicar_plantilla'),
    
    # Gestión de catálogos
    path('clientes/', views.gestionar_clientes, name='gestionar_clientes'),
    path('servicios/', views.gestionar_servicios, name='gestionar_servicios'),
    path('materiales/', views.gestionar_materiales, name='gestionar_materiales'),

    #Crud Clientes
    path('cliente/crear/', views.crear_cliente, name='crear_cliente'),
    path('cliente/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('cliente/<int:cliente_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),  
    path('cliente/<int:cliente_id>/', views.obtener_cliente, name='obtener_cliente'),

    # Crud servicios
    path('servicio/crear/', views.crear_servicio, name='crear_servicio'),
    path('servicio/<int:servicio_id>/', views.obtener_servicio, name='obtener_servicio'),
    path('servicio/<int:servicio_id>/editar/', views.editar_servicio, name='editar_servicio'),
    path('servicio/<int:servicio_id>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),

    # Gestión de categorías
    path('categoria-servicio/crear/', views.crear_categoria_servicio, name='crear_categoria_servicio'),

    # Crud materiales
    path('material/crear/', views.crear_material, name='crear_material'),
    path('material/<int:material_id>/', views.obtener_material, name='obtener_material'),
    path('material/<int:material_id>/editar/', views.editar_material, name='editar_material'),
    path('material/<int:material_id>/eliminar/', views.eliminar_material, name='eliminar_material'),

    # Funciones adicionales de materiales
    path('material/validar-codigo/', views.validar_codigo_material, name='validar_codigo_material'),
    path('material/importar/', views.importar_materiales_csv, name='importar_materiales_csv'),
]

