from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('panel-empleados/', views.panel_empleados, name='panel_empleados'),
    
    # URLs para diferentes funciones según cargo
    path('reportes-ventas/', views.reportes_ventas, name='reportes_ventas'),
    path('mis-tareas/', views.mis_tareas, name='mis_tareas'),
    path('reportes/', views.reportes_generales, name='reportes'),
    
    # URLs para gestión de usuarios
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/export-csv/', views.export_usuarios_csv, name='export_usuarios_csv'),
    
    # APIs para CRUD de usuarios
    path('usuarios/api/create/', views.crear_usuario_api, name='crear_usuario_api'),
    path('usuarios/api/get/<int:user_id>/', views.obtener_usuario_api, name='obtener_usuario_api'),
    path('usuarios/api/update/<int:user_id>/', views.actualizar_usuario_api, name='actualizar_usuario_api'),
    path('usuarios/api/toggle-status/<int:user_id>/', views.cambiar_estado_usuario_api, name='cambiar_estado_usuario_api'),
    path('usuarios/api/delete/<int:user_id>/', views.eliminar_usuario_api, name='eliminar_usuario_api'),


    path('configuracion/', views.configuracion, name='configuracion'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('gestion-servicios/', views.gestion_servicios, name='gestion_servicios'),
    path('gestion-empleados/', views.gestion_empleados, name='gestion_empleados'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('supervision-tareas/', views.supervision_tareas, name='supervision_tareas'),
    path('reportes-equipo/', views.reportes_equipo, name='reportes_equipo'),
    path('asignacion-trabajos/', views.asignacion_trabajos, name='asignacion_trabajos'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('registro-tiempo/', views.registro_tiempo, name='registro_tiempo'),
]