# cotizaciones/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.template.loader import get_template
from django.utils import timezone
import json
from decimal import Decimal
from .models import *
from .forms import *



@login_required
def dashboard_cotizaciones(request):
    """Dashboard principal de cotizaciones"""
    # Estadísticas generales
    total_cotizaciones = Cotizacion.objects.count()
    cotizaciones_mes = Cotizacion.objects.filter(
        fecha_creacion__month=timezone.now().month,
        fecha_creacion__year=timezone.now().year
    ).count()
    
    cotizaciones_pendientes = Cotizacion.objects.filter(estado='enviada').count()
    valor_total_mes = Cotizacion.objects.filter(
        fecha_creacion__month=timezone.now().month,
        fecha_creacion__year=timezone.now().year
    ).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    
    # Últimas cotizaciones
    ultimas_cotizaciones = Cotizacion.objects.select_related('cliente').order_by('-fecha_creacion')[:5]
    
    # Estados de cotizaciones
    estados_stats = Cotizacion.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('-total')
    
    context = {
        'total_cotizaciones': total_cotizaciones,
        'cotizaciones_mes': cotizaciones_mes,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'valor_total_mes': valor_total_mes,
        'ultimas_cotizaciones': ultimas_cotizaciones,
        'estados_stats': estados_stats,
    }
    
    return render(request, 'cotizaciones/dashboard.html', context)

@login_required
def lista_cotizaciones(request):
    """Lista de cotizaciones con filtros"""
    cotizaciones = Cotizacion.objects.select_related('cliente', 'tipo_trabajo').order_by('-fecha_creacion')
    
    # Filtros
    busqueda = request.GET.get('busqueda', '')
    estado = request.GET.get('estado', '')
    cliente_id = request.GET.get('cliente', '')
    
    # Inicializar cliente_nombre
    cliente_nombre = None
    
    if busqueda:
        cotizaciones = cotizaciones.filter(
            Q(numero__icontains=busqueda) |
            Q(cliente__nombre__icontains=busqueda) |
            Q(referencia__icontains=busqueda)
        )
    
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
        
    if cliente_id:
        cotizaciones = cotizaciones.filter(cliente_id=cliente_id)
        try:
            cliente_nombre = Cliente.objects.get(id=cliente_id).nombre
        except Cliente.DoesNotExist:
            cliente_nombre = None

    # Paginación
    paginator = Paginator(cotizaciones, 20)
    page = request.GET.get('page')
    cotizaciones = paginator.get_page(page)
    
    # Para los filtros
    clientes = Cliente.objects.filter(activo=True).order_by('nombre')
    estados = Cotizacion.ESTADO_CHOICES
    
    context = {
        'cotizaciones': cotizaciones,
        'clientes': clientes,
        'estados': estados,
        'busqueda': busqueda,
        'estado_filtro': estado,
        'cliente_filtro': cliente_id,
        'cliente_nombre': cliente_nombre,
    }
    
    return render(request, 'cotizaciones/lista.html', context)

@login_required
def crear_cotizacion(request):
    """Crear nueva cotización"""
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            cotizacion = form.save(commit=False)
            cotizacion.creado_por = request.user
            cotizacion.save()  # Guardar primero para establecer fecha_creacion
            cotizacion.generar_numero()  # Luego generar número
            cotizacion.save()  # Guardar nuevamente con el número
            
            messages.success(request, f'Cotización {cotizacion.numero} creada exitosamente.')
            return redirect('cotizaciones:editar', pk=cotizacion.pk)
    else:
        form = CotizacionForm()
    
    return render(request, 'cotizaciones/crear.html', {'form': form})

# Vistas para gestión de catálogos
@login_required
def gestionar_clientes(request):
    """Gestión de clientes"""
    clientes = Cliente.objects.all().order_by('nombre')
    
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) |
            Q(rut__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    paginator = Paginator(clientes, 20)
    page = request.GET.get('page')
    clientes = paginator.get_page(page)
    
    return render(request, 'cotizaciones/gestionar_clientes.html', {
        'clientes': clientes,
        'busqueda': busqueda
    })

@login_required
def gestionar_servicios(request):
    """Gestión de servicios base"""
    servicios = ServicioBase.objects.select_related('categoria').order_by('categoria__nombre', 'nombre')
    categorias = CategoriaServicio.objects.filter(activo=True)
    
    categoria_filtro = request.GET.get('categoria', '')
    if categoria_filtro:
        servicios = servicios.filter(categoria_id=categoria_filtro)
    
    # Estadísticas adicionales
    servicios_parametrizables = servicios.filter(es_parametrizable=True).count()
    servicios_activos = servicios.filter(activo=True).count()
    
    return render(request, 'cotizaciones/gestionar_servicios.html', {
        'servicios': servicios,
        'categorias': categorias,
        'categoria_filtro': categoria_filtro,
        'servicios_parametrizables': servicios_parametrizables,
        'servicios_activos': servicios_activos,
    })

@login_required
def gestionar_materiales(request):
    """Gestión de materiales"""
    materiales = Material.objects.all().order_by('categoria', 'nombre')
    
    busqueda = request.GET.get('busqueda', '')
    categoria_filtro = request.GET.get('categoria', '')
    
    if busqueda:
        materiales = materiales.filter(
            Q(nombre__icontains=busqueda) |
            Q(codigo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    if categoria_filtro:
        materiales = materiales.filter(categoria=categoria_filtro)
    
    categorias = Material.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    categorias = [cat for cat in categorias if cat]  # Filtrar valores vacíos
    
    # Estadísticas
    materiales_activos = materiales.filter(activo=True).count()
    precio_promedio = materiales.aggregate(promedio=models.Avg('precio_unitario'))['promedio'] or 0
    
    paginator = Paginator(materiales, 20)
    page = request.GET.get('page')
    materiales = paginator.get_page(page)
    
    return render(request, 'cotizaciones/gestionar_materiales.html', {
        'materiales': materiales,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_filtro': categoria_filtro,
        'materiales_activos': materiales_activos,
        'precio_promedio': precio_promedio,
    })

@login_required
def aplicar_plantilla(request, cotizacion_pk, plantilla_pk):
    """Aplicar plantilla a cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    plantilla = get_object_or_404(PlantillaCotizacion, pk=plantilla_pk)
    
    try:
        with transaction.atomic():
            # Agregar servicios de la plantilla
            for item_plantilla in plantilla.servicios.all():
                ItemServicio.objects.create(
                    cotizacion=cotizacion,
                    servicio=item_plantilla.servicio,
                    cantidad=item_plantilla.cantidad_default,
                    precio_unitario=item_plantilla.servicio.precio_base,
                    orden=item_plantilla.orden
                )
            
            # Recalcular totales
            cotizacion.calcular_totales()
            
        messages.success(request, f'Plantilla "{plantilla.nombre}" aplicada exitosamente.')
        
    except Exception as e:
        messages.error(request, f'Error al aplicar plantilla: {str(e)}')
    
    return redirect('cotizaciones:editar_cotizacion', pk=cotizacion_pk)

@login_required
def editar_cotizacion(request, pk):
    """Editar cotización existente"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    if request.method == 'POST':
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cotización actualizada exitosamente.')
            return redirect('cotizaciones:detalle', pk=cotizacion.pk)
    else:
        form = CotizacionForm(instance=cotizacion)
    
    # Obtener todos los items
    items_servicio = cotizacion.items_servicio.all().order_by('orden')
    items_material = cotizacion.items_material.all()
    items_mano_obra = cotizacion.items_mano_obra.all()
    
    # Para agregar nuevos items
    categorias_servicio = CategoriaServicio.objects.filter(activo=True)
    materiales = Material.objects.filter(activo=True)
    
    context = {
        'cotizacion': cotizacion,
        'form': form,
        'items_servicio': items_servicio,
        'items_material': items_material,
        'items_mano_obra': items_mano_obra,
        'categorias_servicio': categorias_servicio,
        'materiales': materiales,
    }
    
    return render(request, 'cotizaciones/editar.html', context)

@login_required
def detalle_cotizacion(request, pk):
    """Ver detalle de cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    items_servicio = cotizacion.items_servicio.all().order_by('orden')
    items_material = cotizacion.items_material.all()
    items_mano_obra = cotizacion.items_mano_obra.all()
    
    context = {
        'cotizacion': cotizacion,
        'items_servicio': items_servicio,
        'items_material': items_material,
        'items_mano_obra': items_mano_obra,
        'config_empresa': ConfiguracionEmpresa.get_config(),
    }
    
    return render(request, 'cotizaciones/detalle.html', context)

@login_required
@require_http_methods(["POST"])
def agregar_item_servicio(request, cotizacion_pk):
    """Agregar item de servicio vía AJAX"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    
    try:
        data = json.loads(request.body)
        servicio_id = data.get('servicio_id')
        cantidad = Decimal(str(data.get('cantidad', 1)))
        precio_unitario = Decimal(str(data.get('precio_unitario', 0)))
        descripcion_personalizada = data.get('descripcion_personalizada', '')
        parametros = data.get('parametros', {})
        
        servicio = get_object_or_404(ServicioBase, pk=servicio_id)
        
        with transaction.atomic():
            # Crear item de servicio
            item = ItemServicio.objects.create(
                cotizacion=cotizacion,
                servicio=servicio,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descripcion_personalizada=descripcion_personalizada,
                orden=cotizacion.items_servicio.count()
            )
            
            # Agregar parámetros si existen
            for param_id, valor in parametros.items():
                if valor:
                    ParametroItemServicio.objects.create(
                        item_servicio=item,
                        parametro_id=param_id,
                        valor=valor
                    )
            
            # Recalcular totales
            cotizacion.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'subtotal': float(item.subtotal),
            'valor_total': float(cotizacion.valor_total)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def agregar_item_material(request, cotizacion_pk):
    """Agregar item de material vía AJAX"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    
    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')
        cantidad = Decimal(str(data.get('cantidad', 1)))
        precio_unitario = Decimal(str(data.get('precio_unitario', 0)))
        descripcion_personalizada = data.get('descripcion_personalizada', '')
        
        material = get_object_or_404(Material, pk=material_id)
        
        with transaction.atomic():
            item = ItemMaterial.objects.create(
                cotizacion=cotizacion,
                material=material,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descripcion_personalizada=descripcion_personalizada
            )
            
            # Recalcular totales
            cotizacion.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'subtotal': float(item.subtotal),
            'valor_total': float(cotizacion.valor_total)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def agregar_item_mano_obra(request, cotizacion_pk):
    """Agregar item de mano de obra vía AJAX"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    
    try:
        data = json.loads(request.body)
        descripcion = data.get('descripcion')
        horas = Decimal(str(data.get('horas', 0)))
        precio_hora = Decimal(str(data.get('precio_hora', 0)))
        
        with transaction.atomic():
            item = ItemManoObra.objects.create(
                cotizacion=cotizacion,
                descripcion=descripcion,
                horas=horas,
                precio_hora=precio_hora
            )
            
            # Recalcular totales
            cotizacion.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'subtotal': float(item.subtotal),
            'valor_total': float(cotizacion.valor_total)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["DELETE"])
def eliminar_item_servicio(request, cotizacion_pk, item_pk):
    """Eliminar item de servicio"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    item = get_object_or_404(ItemServicio, pk=item_pk, cotizacion=cotizacion)
    
    item.delete()
    cotizacion.calcular_totales()
    
    return JsonResponse({
        'success': True,
        'valor_total': float(cotizacion.valor_total)
    })

@login_required
@require_http_methods(["DELETE"])
def eliminar_item_material(request, cotizacion_pk, item_pk):
    """Eliminar item de material"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    item = get_object_or_404(ItemMaterial, pk=item_pk, cotizacion=cotizacion)
    
    item.delete()
    cotizacion.calcular_totales()
    
    return JsonResponse({
        'success': True,
        'valor_total': float(cotizacion.valor_total)
    })

@login_required
@require_http_methods(["DELETE"])
def eliminar_item_mano_obra(request, cotizacion_pk, item_pk):
    """Eliminar item de mano de obra"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    item = get_object_or_404(ItemManoObra, pk=item_pk, cotizacion=cotizacion)
    
    item.delete()
    cotizacion.calcular_totales()
    
    return JsonResponse({
        'success': True,
        'valor_total': float(cotizacion.valor_total)
    })

@login_required
def obtener_servicios_categoria(request, categoria_id):
    """Obtener servicios de una categoría vía AJAX"""
    servicios = ServicioBase.objects.filter(
        categoria_id=categoria_id, 
        activo=True
    ).values('id', 'nombre', 'precio_base', 'unidad', 'es_parametrizable')
    
    return JsonResponse(list(servicios), safe=False)

@login_required
def obtener_parametros_servicio(request, servicio_id):
    """Obtener parámetros de un servicio vía AJAX"""
    parametros = ParametroServicio.objects.filter(
        servicio_id=servicio_id
    ).values('id', 'nombre', 'tipo', 'requerido', 'opciones', 'valor_por_defecto')
    
    for param in parametros:
        if param['tipo'] == 'select' and param['opciones']:
            param['opciones_list'] = [opt.strip() for opt in param['opciones'].split(',')]
    
    return JsonResponse(list(parametros), safe=False)

@login_required
@require_http_methods(["POST"])
def actualizar_gastos_traslado(request, cotizacion_pk):
    """Actualizar gastos de traslado"""
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_pk)
    
    try:
        data = json.loads(request.body)
        gastos_traslado = Decimal(str(data.get('gastos_traslado', 0)))
        
        cotizacion.gastos_traslado = gastos_traslado
        cotizacion.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'valor_total': float(cotizacion.valor_total),
            'valor_neto': float(cotizacion.valor_neto),
            'valor_iva': float(cotizacion.valor_iva)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def generar_pdf_cotizacion(request, pk):
    """Generar PDF de la cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    context = {
        'cotizacion': cotizacion,
        'config_empresa': ConfiguracionEmpresa.get_config(),
        'items_servicio': cotizacion.items_servicio.all().order_by('orden'),
        'items_material': cotizacion.items_material.all(),
        'items_mano_obra': cotizacion.items_mano_obra.all(),
    }
    
    # Usar el template detalle.html existente en lugar de pdf_cotizacion.html
    template = get_template('cotizaciones/detalle.html')
    html = template.render(context)
    
    response = HttpResponse(html, content_type='text/html')
    return response

@login_required
@require_http_methods(["POST"])
def cambiar_estado_cotizacion(request, pk):
    """Cambiar estado de la cotización"""
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        if nuevo_estado in dict(Cotizacion.ESTADO_CHOICES):
            cotizacion.estado = nuevo_estado
            cotizacion.save()
            
            messages.success(request, f'Estado de la cotización actualizado a {cotizacion.get_estado_display()}')
            
            return JsonResponse({
                'success': True,
                'nuevo_estado': nuevo_estado,
                'estado_display': cotizacion.get_estado_display()
            })
        else:
            return JsonResponse({'success': False, 'error': 'Estado inválido'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


#Crud Clientes
@login_required
@require_http_methods(["POST"])
def crear_cliente(request):
    """Crear nuevo cliente vía AJAX"""
    try:
        data = json.loads(request.body)
        
        cliente = Cliente.objects.create(
            nombre=data.get('nombre'),
            atencion=data.get('atencion', ''),
            rut=data.get('rut', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            direccion=data.get('direccion', ''),
            activo=data.get('activo', True)
        )
        
        return JsonResponse({
            'success': True,
            'cliente_id': cliente.id,
            'message': 'Cliente creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["PUT"])
def editar_cliente(request, cliente_id):
    """Editar cliente existente vía AJAX"""
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        data = json.loads(request.body)
        
        cliente.nombre = data.get('nombre', cliente.nombre)
        cliente.atencion = data.get('atencion', cliente.atencion)
        cliente.rut = data.get('rut', cliente.rut)
        cliente.telefono = data.get('telefono', cliente.telefono)
        cliente.email = data.get('email', cliente.email)
        cliente.direccion = data.get('direccion', cliente.direccion)
        cliente.activo = data.get('activo', cliente.activo)
        cliente.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cliente actualizado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
@require_http_methods(["DELETE"])
def eliminar_cliente(request, cliente_id):
    """Eliminar cliente vía AJAX"""
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        nombre_cliente = cliente.nombre
        cliente.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Cliente {nombre_cliente} eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
@require_http_methods(["GET"])
def obtener_cliente(request, cliente_id):
    """Obtener datos de un cliente vía AJAX"""
    try:
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'atencion': cliente.atencion or '',
                'rut': cliente.rut or '',
                'telefono': cliente.telefono or '',
                'email': cliente.email or '',
                'direccion': cliente.direccion or '',
                'activo': cliente.activo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


#Crud Servicios
@login_required
@require_http_methods(["POST"])
def crear_servicio(request):
    """Crear nuevo servicio vía AJAX"""
    try:
        data = json.loads(request.body)
        
        # Obtener la categoría
        categoria = get_object_or_404(CategoriaServicio, pk=data.get('categoria_id'))
        
        servicio = ServicioBase.objects.create(
            categoria=categoria,
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion'),
            precio_base=data.get('precio_base'),
            unidad=data.get('unidad', 'UND'),
            es_parametrizable=data.get('es_parametrizable', False),
            activo=data.get('activo', True)
        )
        
        return JsonResponse({
            'success': True,
            'servicio_id': servicio.id,
            'message': 'Servicio creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["GET"])
def obtener_servicio(request, servicio_id):
    """Obtener datos de un servicio vía AJAX"""
    try:
        servicio = get_object_or_404(ServicioBase, pk=servicio_id)
        
        return JsonResponse({
            'success': True,
            'servicio': {
                'id': servicio.id,
                'categoria_id': servicio.categoria.id,
                'nombre': servicio.nombre,
                'descripcion': servicio.descripcion,
                'precio_base': float(servicio.precio_base),
                'unidad': servicio.unidad,
                'es_parametrizable': servicio.es_parametrizable,
                'activo': servicio.activo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["PUT"])
def editar_servicio(request, servicio_id):
    """Editar servicio existente vía AJAX"""
    try:
        servicio = get_object_or_404(ServicioBase, pk=servicio_id)
        data = json.loads(request.body)
        
        # Actualizar categoría si se proporciona
        if data.get('categoria_id'):
            categoria = get_object_or_404(CategoriaServicio, pk=data.get('categoria_id'))
            servicio.categoria = categoria
        
        servicio.nombre = data.get('nombre', servicio.nombre)
        servicio.descripcion = data.get('descripcion', servicio.descripcion)
        servicio.precio_base = data.get('precio_base', servicio.precio_base)
        servicio.unidad = data.get('unidad', servicio.unidad)
        servicio.es_parametrizable = data.get('es_parametrizable', servicio.es_parametrizable)
        servicio.activo = data.get('activo', servicio.activo)
        servicio.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Servicio actualizado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["DELETE"])
def eliminar_servicio(request, servicio_id):
    """Eliminar servicio vía AJAX"""
    try:
        servicio = get_object_or_404(ServicioBase, pk=servicio_id)
        nombre_servicio = servicio.nombre
        servicio.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Servicio {nombre_servicio} eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# También crear una función para categorías
@login_required
@require_http_methods(["POST"])
def crear_categoria_servicio(request):
    """Crear nueva categoría de servicio vía AJAX"""
    try:
        data = json.loads(request.body)
        
        categoria = CategoriaServicio.objects.create(
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion', ''),
            orden=data.get('orden', 0),
            activo=True
        )
        
        return JsonResponse({
            'success': True,
            'categoria_id': categoria.id,
            'message': 'Categoría creada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
#Crud Materiales
@login_required
@require_http_methods(["POST"])
def crear_material(request):
    """Crear nuevo material vía AJAX"""
    try:
        data = json.loads(request.body)
        
        material = Material.objects.create(
            codigo=data.get('codigo'),
            nombre=data.get('nombre'),
            descripcion=data.get('descripcion', ''),
            precio_unitario=data.get('precio_unitario'),
            unidad=data.get('unidad', 'UND'),
            categoria=data.get('categoria', ''),
            activo=data.get('activo', True)
        )
        
        return JsonResponse({
            'success': True,
            'material_id': material.id,
            'message': 'Material creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["GET"])
def obtener_material(request, material_id):
    """Obtener datos de un material vía AJAX"""
    try:
        material = get_object_or_404(Material, pk=material_id)
        
        return JsonResponse({
            'success': True,
            'material': {
                'id': material.id,
                'codigo': material.codigo,
                'nombre': material.nombre,
                'descripcion': material.descripcion or '',
                'precio_unitario': float(material.precio_unitario),
                'unidad': material.unidad,
                'categoria': material.categoria or '',
                'activo': material.activo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["PUT"])
def editar_material(request, material_id):
    """Editar material existente vía AJAX"""
    try:
        material = get_object_or_404(Material, pk=material_id)
        data = json.loads(request.body)
        
        material.codigo = data.get('codigo', material.codigo)
        material.nombre = data.get('nombre', material.nombre)
        material.descripcion = data.get('descripcion', material.descripcion)
        material.precio_unitario = data.get('precio_unitario', material.precio_unitario)
        material.unidad = data.get('unidad', material.unidad)
        material.categoria = data.get('categoria', material.categoria)
        material.activo = data.get('activo', material.activo)
        material.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Material actualizado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["DELETE"])
def eliminar_material(request, material_id):
    """Eliminar material vía AJAX"""
    try:
        material = get_object_or_404(Material, pk=material_id)
        nombre_material = material.nombre
        material.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Material {nombre_material} eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
def validar_codigo_material(request):
    """Validar si un código de material está disponible"""
    codigo = request.GET.get('codigo', '')
    existe = Material.objects.filter(codigo=codigo).exists()
    
    return JsonResponse({
        'disponible': not existe,
        'codigo': codigo
    })

@login_required
@require_http_methods(["POST"])
def importar_materiales_csv(request):
    """Importar materiales desde archivo CSV"""
    try:
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se encontró archivo'})
        
        archivo = request.FILES['archivo']
        actualizar_existentes = request.POST.get('actualizar_existentes') == 'true'
        
        # Leer archivo CSV
        contenido = archivo.read().decode('utf-8')
        lineas = contenido.strip().split('\n')
        
        if len(lineas) < 2:
            return JsonResponse({'success': False, 'error': 'Archivo CSV vacío o sin datos'})
        
        # Procesar header
        headers = [h.strip().lower() for h in lineas[0].split(',')]
        required_fields = ['codigo', 'nombre', 'precio_unitario']
        
        for field in required_fields:
            if field not in headers:
                return JsonResponse({'success': False, 'error': f'Campo requerido faltante: {field}'})
        
        materiales_creados = 0
        materiales_actualizados = 0
        
        # Procesar datos
        for i, linea in enumerate(lineas[1:], 2):
            try:
                valores = [v.strip().strip('"') for v in linea.split(',')]
                if len(valores) != len(headers):
                    continue
                
                data = dict(zip(headers, valores))
                
                # Validar datos requeridos
                if not data.get('codigo') or not data.get('nombre'):
                    continue
                
                material_data = {
                    'codigo': data['codigo'],
                    'nombre': data['nombre'],
                    'categoria': data.get('categoria', ''),
                    'precio_unitario': float(data['precio_unitario']),
                    'unidad': data.get('unidad', 'UND'),
                    'descripcion': data.get('descripcion', ''),
                    'activo': True
                }
                
                # Verificar si existe
                material_existente = Material.objects.filter(codigo=data['codigo']).first()
                
                if material_existente:
                    if actualizar_existentes:
                        for key, value in material_data.items():
                            setattr(material_existente, key, value)
                        material_existente.save()
                        materiales_actualizados += 1
                else:
                    Material.objects.create(**material_data)
                    materiales_creados += 1
                    
            except (ValueError, IndexError) as e:
                continue  # Saltar líneas con errores
        
        mensaje = f'Importación completada: {materiales_creados} creados'
        if materiales_actualizados:
            mensaje += f', {materiales_actualizados} actualizados'
        
        return JsonResponse({
            'success': True,
            'materiales_creados': materiales_creados,
            'materiales_actualizados': materiales_actualizados,
            'message': mensaje
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })