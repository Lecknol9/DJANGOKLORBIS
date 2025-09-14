from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import PerfilEmpleado

def requiere_cargo(cargos_permitidos):
    """
    Decorador que verifica que el usuario tenga uno de los cargos permitidos
    Verifica en tiempo real contra la base de datos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                # Verificación en tiempo real desde la BD
                perfil = PerfilEmpleado.objects.get(user=request.user)
                
                # Verificar que el perfil esté activo
                if not perfil.activo:
                    messages.error(request, 'Tu cuenta ha sido desactivada.')
                    return redirect('login')
                
                # Verificar cargo
                if perfil.cargo not in cargos_permitidos:
                    messages.error(request, 'No tienes permisos para acceder a esta función.')
                    return redirect('panel_empleados')
                
                return view_func(request, *args, **kwargs)
                
            except PerfilEmpleado.DoesNotExist:
                messages.error(request, 'Perfil de empleado no encontrado.')
                return redirect('login')
                
        return wrapper
    return decorator

def requiere_admin(view_func):
    """Decorador específico para funciones de administrador"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            perfil = PerfilEmpleado.objects.get(user=request.user)
            if not perfil.es_admin() or not perfil.activo:
                return render(request, 'home/error.html')
            return view_func(request, *args, **kwargs)
        except PerfilEmpleado.DoesNotExist:
            return render(request, 'home/error.html')
    return wrapper

def requiere_gerente_o_superior(view_func):
    """Decorador para gerentes y superiores"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            perfil = PerfilEmpleado.objects.get(user=request.user)
            if not perfil.es_gerente_o_superior() or not perfil.activo:
                return render(request, 'home/error.html')
            return view_func(request, *args, **kwargs)
        except PerfilEmpleado.DoesNotExist:
            return render(request, 'home/error.html')
    return wrapper