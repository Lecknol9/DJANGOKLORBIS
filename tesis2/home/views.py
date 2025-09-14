from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import requiere_admin, requiere_gerente_o_superior, requiere_cargo
from django.contrib import messages
from .models import PerfilEmpleado
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db import transaction
import json
from .models import *

import csv
from datetime import datetime, timedelta




def index(request):
    return render(request, 'home/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verificar que tenga perfil de empleado
            try:
                perfil = PerfilEmpleado.objects.get(user=user)
                if perfil.activo:
                    login(request, user)
                    return redirect('home:panel_empleados')
                else:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            except PerfilEmpleado.DoesNotExist:
                messages.error(request, 'No tienes permisos de empleado.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'home/login.html')

def logout_view(request):
    logout(request)
    return redirect('home:index')

@login_required
def panel_empleados(request):
    try:
        perfil = PerfilEmpleado.objects.get(user=request.user)
        
        # Definir funciones disponibles según el cargo
        funciones_disponibles = []
        
        if perfil.es_admin():
            funciones_disponibles = [
                {'nombre': 'Gestión de Usuarios', 'url': 'home:gestion_usuarios', 'icono': '👥'},
                {'nombre': 'Sistema de Cotizaciones', 'url': 'cotizaciones:dashboard', 'icono': '📊'},
                {'nombre': 'Gestión de Clientes', 'url': 'cotizaciones:gestionar_clientes', 'icono': '👤'},
                {'nombre': 'Catálogo de Servicios', 'url': 'cotizaciones:gestionar_servicios', 'icono': '🔧'},
                {'nombre': 'Catálogo de Materiales', 'url': 'cotizaciones:gestionar_materiales', 'icono': '📦'},
                {'nombre': 'Reportes Generales', 'url': 'home:reportes', 'icono': '📈'},
                {'nombre': 'Configuración', 'url': 'home:configuracion', 'icono': '⚙️'},
                {'nombre': 'Auditoría', 'url': 'home:auditoria', 'icono': '🔍'},
            ]
        elif perfil.es_gerente_o_superior():
            funciones_disponibles = [
                {'nombre': 'Sistema de Cotizaciones', 'url': 'cotizaciones:dashboard', 'icono': '📊'},
                {'nombre': 'Nueva Cotización', 'url': 'cotizaciones:crear', 'icono': '➕'},
                {'nombre': 'Lista de Cotizaciones', 'url': 'cotizaciones:lista', 'icono': '📄'},
                {'nombre': 'Gestión de Clientes', 'url': 'cotizaciones:gestionar_clientes', 'icono': '👤'},
                {'nombre': 'Gestión de Usuarios', 'url': 'home:gestion_usuarios', 'icono': '👥'},
                {'nombre': 'Reportes de Ventas', 'url': 'home:reportes_ventas', 'icono': '💰'},
                {'nombre': 'Gestión de Empleados', 'url': 'home:gestion_empleados', 'icono': '👨‍💼'},
                {'nombre': 'Estadísticas', 'url': 'home:estadisticas', 'icono': '📈'},
            ]
        elif perfil.es_supervisor_o_superior():
            funciones_disponibles = [
                {'nombre': 'Sistema de Cotizaciones', 'url': 'cotizaciones:dashboard', 'icono': '📊'},
                {'nombre': 'Nueva Cotización', 'url': 'cotizaciones:crear', 'icono': '➕'},
                {'nombre': 'Lista de Cotizaciones', 'url': 'cotizaciones:lista', 'icono': '📄'},
                {'nombre': 'Supervisión de Tareas', 'url': 'home:supervision_tareas', 'icono': '✅'},
                {'nombre': 'Reportes de Equipo', 'url': 'home:reportes_equipo', 'icono': '📋'},
                {'nombre': 'Asignación de Trabajos', 'url': 'home:asignacion_trabajos', 'icono': '📝'},
            ]
        else:
            funciones_disponibles = [
                {'nombre': 'Ver Cotizaciones', 'url': 'cotizaciones:lista', 'icono': '📄'},
                {'nombre': 'Mi Perfil', 'url': 'home:mi_perfil', 'icono': '👤'},
                {'nombre': 'Mis Tareas', 'url': 'home:mis_tareas', 'icono': '📌'},
                {'nombre': 'Registro de Tiempo', 'url': 'home:registro_tiempo', 'icono': '⏰'},
            ]
        
        context = {
            'perfil': perfil,
            'funciones_disponibles': funciones_disponibles,
        }
        return render(request, 'home/panel_empleados.html', context)
        
    except PerfilEmpleado.DoesNotExist:
        messages.error(request, 'No tienes permisos de empleado.')
        return redirect('index')

# Vistas para las diferentes funciones de Admin
@login_required
@requiere_gerente_o_superior
def gestion_usuarios(request):
    """Vista principal del panel de gestión de usuarios"""
    
    # Obtener parámetros de filtro
    query = request.GET.get('q', '')
    cargo_filter = request.GET.get('cargo', '')
    activo_filter = request.GET.get('activo', '')
    
    # Query base
    empleados = PerfilEmpleado.objects.select_related('user').all()
    
    # Aplicar filtros
    if query:
        empleados = empleados.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) 
        )
    
    if cargo_filter:
        empleados = empleados.filter(cargo=cargo_filter)
    
    if activo_filter in ['0', '1']:
        empleados = empleados.filter(activo=activo_filter == '1')
    
    
    # Ordenar
    empleados = empleados.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(empleados, 15)  # 15 empleados por página
    page = request.GET.get('page')
    empleados_page = paginator.get_page(page)
    
    # Estadísticas
    total_empleados = PerfilEmpleado.objects.count()
    empleados_activos = PerfilEmpleado.objects.filter(activo=True).count()
    empleados_inactivos = total_empleados - empleados_activos
    porcentaje_activos = round((empleados_activos / total_empleados * 100) if total_empleados > 0 else 0, 1)
    
    # Nuevos empleados en los últimos 30 días
    hace_30_dias = datetime.now() - timedelta(days=30)
    nuevos_mes = PerfilEmpleado.objects.filter(fecha_creacion__gte=hace_30_dias).count()
    
    # Opciones para filtros
    cargos_choices = PerfilEmpleado.CARGO_CHOICES
    
    # Construir parámetros URL para paginación
    url_params = ''
    if query:
        url_params += f'&q={query}'
    if cargo_filter:
        url_params += f'&cargo={cargo_filter}'
    if activo_filter:
        url_params += f'&activo={activo_filter}'
    
    context = {
        'empleados': empleados_page,
        'total_empleados': total_empleados,
        'empleados_activos': empleados_activos,
        'empleados_inactivos': empleados_inactivos,
        'porcentaje_activos': porcentaje_activos,
        'nuevos_mes': nuevos_mes,
        'cargos_choices': cargos_choices,
        'url_params': url_params,
    }
    
    return render(request, 'home/gestion_usuarios.html', context)

@login_required
@requiere_admin
@require_http_methods(["POST"])
def crear_usuario_api(request):
    """API para crear nuevo usuario"""
    try:
        with transaction.atomic():
            # Validar datos requeridos
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            password = request.POST.get('password', '').strip()
            cargo = request.POST.get('cargo')
            fecha_ingreso = request.POST.get('fecha_ingreso')
            
            if not all([username, email, first_name, last_name, password, cargo, fecha_ingreso]):
                return JsonResponse({
                    'success': False, 
                    'message': 'Todos los campos obligatorios deben ser completados'
                })
            
            # Verificar que el username no exista
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'El nombre de usuario ya existe'
                })
            
            # Verificar que el email no exista
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'El email ya está registrado'
                })
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Crear perfil
            perfil = PerfilEmpleado.objects.create(
                user=user,
                cargo=cargo,
                fecha_ingreso=fecha_ingreso,
                telefono=request.POST.get('telefono', '').strip() or None,
                salario=request.POST.get('salario') or None,
                activo=request.POST.get('activo') == 'on'
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'Usuario {user.get_full_name()} creado exitosamente'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al crear usuario: {str(e)}'
        })

@login_required
@requiere_admin
def obtener_usuario_api(request, user_id):
    """API para obtener datos de un usuario"""
    try:
        perfil = get_object_or_404(PerfilEmpleado, id=user_id)
        
        return JsonResponse({
            'success': True,
            'user': {
                'username': perfil.user.username,
                'email': perfil.user.email,
                'first_name': perfil.user.first_name,
                'last_name': perfil.user.last_name,
            },
            'perfil': {
                'cargo': perfil.cargo,
                'fecha_ingreso': perfil.fecha_ingreso.strftime('%Y-%m-%d'),
                'telefono': perfil.telefono,
                'salario': float(perfil.salario) if perfil.salario else None,
                'activo': perfil.activo,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al obtener usuario: {str(e)}'
        })

@login_required
@requiere_admin
@require_http_methods(["POST"])
def actualizar_usuario_api(request, user_id):
    """API para actualizar usuario"""
    try:
        with transaction.atomic():
            perfil = get_object_or_404(PerfilEmpleado, id=user_id)
            user = perfil.user
            
            # Actualizar datos del usuario
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Verificar username único (excluyendo el usuario actual)
            if username != user.username and User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'El nombre de usuario ya existe'
                })
            
            # Verificar email único (excluyendo el usuario actual)
            if email != user.email and User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False, 
                    'message': 'El email ya está registrado'
                })
            
            # Actualizar usuario
            user.username = username
            user.email = email
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            
            # Cambiar contraseña si se proporcionó
            password = request.POST.get('password', '').strip()
            if password:
                user.set_password(password)
            
            user.save()
            
            # Actualizar perfil
            perfil.cargo = request.POST.get('cargo')
            perfil.fecha_ingreso = request.POST.get('fecha_ingreso')
            perfil.telefono = request.POST.get('telefono', '').strip() or None
            salario = request.POST.get('salario')
            perfil.salario = salario if salario else None
            perfil.activo = request.POST.get('activo') == 'on'
            perfil.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Usuario {user.get_full_name()} actualizado exitosamente'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al actualizar usuario: {str(e)}'
        })

@login_required
@requiere_admin
@require_http_methods(["POST"])
def cambiar_estado_usuario_api(request, user_id):
    """API para activar/desactivar usuario"""
    try:
        perfil = get_object_or_404(PerfilEmpleado, id=user_id)
        
        # No permitir que el admin se desactive a sí mismo
        if perfil.user == request.user:
            return JsonResponse({
                'success': False, 
                'message': 'No puedes desactivar tu propia cuenta'
            })
        
        data = json.loads(request.body)
        nuevo_estado = data.get('activo', True)
        
        perfil.activo = nuevo_estado
        perfil.save()
        
        estado_texto = "activado" if nuevo_estado else "desactivado"
        
        return JsonResponse({
            'success': True, 
            'message': f'Usuario {perfil.nombre_completo} {estado_texto} exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al cambiar estado: {str(e)}'
        })

@login_required
@requiere_admin
@require_http_methods(["DELETE"])
def eliminar_usuario_api(request, user_id):
    """API para eliminar usuario"""
    try:
        perfil = get_object_or_404(PerfilEmpleado, id=user_id)
        
        # No permitir que el admin se elimine a sí mismo
        if perfil.user == request.user:
            return JsonResponse({
                'success': False, 
                'message': 'No puedes eliminar tu propia cuenta'
            })
        
        nombre_completo = perfil.nombre_completo
        perfil.user.delete()  # Esto también eliminará el perfil por CASCADE
        
        return JsonResponse({
            'success': True, 
            'message': f'Usuario {nombre_completo} eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error al eliminar usuario: {str(e)}'
        })

@login_required
@requiere_gerente_o_superior
def export_usuarios_csv(request):
    """Exportar usuarios a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="empleados.csv"'
    response.write('\ufeff')  # BOM para UTF-8
    
    writer = csv.writer(response)
    writer.writerow([
        'Usuario', 'Nombre', 'Apellido', 'Email', 'Cargo',
        'Fecha Ingreso', 'Teléfono', 'Salario', 'Estado', 'Fecha Creación'
    ])
    
    empleados = PerfilEmpleado.objects.select_related('user').all()
    
    for perfil in empleados:
        writer.writerow([
            perfil.user.username,
            perfil.user.first_name,
            perfil.user.last_name,
            perfil.user.email,
            perfil.get_cargo_display(),
            perfil.fecha_ingreso.strftime('%d/%m/%Y'),
            perfil.telefono or '',
            perfil.salario or '',
            'Activo' if perfil.activo else 'Inactivo',
            perfil.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        ])
    
    return response

"""                                                                                        
,------.                        ,--.                                             ,--.          
|  .--. ',--.--. ,---.,--.  ,--.`--',--,--,--. ,--,--.,--,--,--. ,---. ,--,--, ,-'  '-. ,---.  
|  '--' ||  .--'| .-. |\  `'  / ,--.|        |' ,-.  ||        || .-. :|      \'-.  .-'| .-. : 
|  | --' |  |   ' '-' '/  /.  \ |  ||  |  |  |\ '-'  ||  |  |  |\   --.|  ||  |  |  |  \   --. 
`--'     `--'    `---''--'  '--'`--'`--`--`--' `--`--'`--`--`--' `----'`--''--'  `--'   `----' 
                                                                                               
"""


@login_required
@requiere_admin
def reportes_generales(request):
    perfil = PerfilEmpleado.objects.get(user=request.user)
    if not perfil.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('panel_empleados')
    
    return HttpResponseForbidden("Proximamente")

@login_required
@requiere_admin
def configuracion(request):
    perfil = PerfilEmpleado.objects.get(user=request.user)
    if not perfil.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('panel_empleados')
    return HttpResponseForbidden("Proximamente")

@login_required
@requiere_admin
def auditoria(request):
    perfil = PerfilEmpleado.objects.get(user=request.user)
    if not perfil.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('panel_empleados')
    return HttpResponseForbidden("Proximamente")

@login_required
@requiere_admin
def gestion_servicios(request):
    perfil = PerfilEmpleado.objects.get(user=request.user)
    if not perfil.es_admin():
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('panel_empleados')
    return HttpResponseForbidden("Proximamente")

#Por Hacer:
@login_required
@requiere_admin
def reportes_ventas(request):
    perfil = PerfilEmpleado.objects.get(user=request.user)
    if not perfil.es_gerente_o_superior():
        messages.error(request, 'No tienes permisos para acceder a esta función.')
        return redirect('panel_empleados')
    
    # Aquí iría la lógica para reportes de ventas
    return HttpResponseForbidden("Proximamente")

@login_required
def mis_tareas(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def gestion_empleados(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def estadisticas(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def supervision_tareas(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def reportes_equipo(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def asignacion_trabajos(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def mi_perfil(request):
    return HttpResponseForbidden("Proximamente")

@login_required
def registro_tiempo(request):
    return HttpResponseForbidden("Proximamente")