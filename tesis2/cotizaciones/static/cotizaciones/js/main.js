// Obtener CSRF token
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Funciones para modales
function mostrarModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function cerrarModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
    limpiarFormularioModal(modalId);
}

function limpiarFormularioModal(modalId) {
    const modal = document.getElementById(modalId);
    const inputs = modal.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        if (input.type === 'checkbox') {
            input.checked = false;
        } else {
            input.value = '';
        }
    });
    
    // Limpiar contenedores dinámicos
    const parametrosContainer = modal.querySelector('.parametros-container');
    if (parametrosContainer) {
        parametrosContainer.classList.remove('show');
        parametrosContainer.innerHTML = '';
    }
}

// Cerrar modales al hacer clic fuera
window.onclick = function(event) {
    const modales = document.querySelectorAll('.modal');
    modales.forEach(modal => {
        if (event.target === modal) {
            modal.classList.remove('show');
        }
    });
}

// Función genérica para peticiones AJAX
async function hacerPeticionAjax(url, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        return await response.json();
    } catch (error) {
        console.error('Error en petición AJAX:', error);
        throw error;
    }
}

// Cargar servicios por categoría
async function cargarServicios() {
    const categoriaId = document.getElementById('categoria-servicio').value;
    const servicioSelect = document.getElementById('servicio-select');
    
    servicioSelect.innerHTML = '<option value="">Seleccionar servicio</option>';
    
    const parametrosContainer = document.getElementById('parametros-servicio');
    if (parametrosContainer) {
        parametrosContainer.classList.remove('show');
    }
    
    if (!categoriaId) return;
    
    try {
        const servicios = await hacerPeticionAjax(`/cotizaciones/api/categoria/${categoriaId}/servicios/`);
        
        servicios.forEach(servicio => {
            const option = document.createElement('option');
            option.value = servicio.id;
            option.textContent = servicio.nombre;
            option.dataset.precio = servicio.precio_base;
            option.dataset.parametrizable = servicio.es_parametrizable;
            servicioSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error cargando servicios:', error);
        alert('Error al cargar los servicios');
    }
}

// Cargar parámetros del servicio
async function cargarParametrosServicio() {
    const servicioSelect = document.getElementById('servicio-select');
    const servicioId = servicioSelect.value;
    const selectedOption = servicioSelect.selectedOptions[0];
    
    // Establecer precio base
    if (selectedOption) {
        const precioInput = document.getElementById('precio-servicio');
        if (precioInput) {
            precioInput.value = selectedOption.dataset.precio;
        }
    }
    
    const parametrosContainer = document.getElementById('parametros-servicio');
    if (!parametrosContainer) return;
    
    parametrosContainer.innerHTML = '';
    parametrosContainer.classList.remove('show');
    
    if (!servicioId || selectedOption.dataset.parametrizable === 'false') return;
    
    try {
        const parametros = await hacerPeticionAjax(`/cotizaciones/api/servicio/${servicioId}/parametros/`);
        
        if (parametros.length > 0) {
            parametrosContainer.innerHTML = '<h4 style="margin: 0 0 12px; color: var(--azul-700);">Parámetros del Servicio</h4>';
            
            parametros.forEach(param => {
                const formGroup = document.createElement('div');
                formGroup.className = 'form-group';
                
                let inputHtml = '';
                if (param.tipo === 'select') {
                    const opciones = param.opciones_list.map(opt => `<option value="${opt}">${opt}</option>`).join('');
                    inputHtml = `<select id="param-${param.id}">${opciones}</select>`;
                } else if (param.tipo === 'boolean') {
                    inputHtml = `<select id="param-${param.id}">
                        <option value="true">Sí</option>
                        <option value="false">No</option>
                    </select>`;
                } else {
                    const type = param.tipo === 'number' ? 'number' : 'text';
                    inputHtml = `<input type="${type}" id="param-${param.id}" value="${param.valor_por_defecto || ''}">`;
                }
                
                formGroup.innerHTML = `
                    <label for="param-${param.id}">${param.nombre}${param.requerido ? ' *' : ''}</label>
                    ${inputHtml}
                `;
                
                parametrosContainer.appendChild(formGroup);
            });
            
            parametrosContainer.classList.add('show');
        }
    } catch (error) {
        console.error('Error cargando parámetros:', error);
    }
}

// Cargar precio del material
function cargarPrecioMaterial() {
    const materialSelect = document.getElementById('material-select');
    const selectedOption = materialSelect.selectedOptions[0];
    
    if (selectedOption) {
        const precioInput = document.getElementById('precio-material');
        if (precioInput) {
            precioInput.value = selectedOption.dataset.precio;
        }
    }
}

// Agregar servicio
async function agregarServicio() {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) {
        alert('Error: No se encontró ID de cotización');
        return;
    }
    
    const servicioId = document.getElementById('servicio-select').value;
    const cantidad = document.getElementById('cantidad-servicio').value;
    const precioUnitario = document.getElementById('precio-servicio').value;
    const descripcionPersonalizada = document.getElementById('descripcion-servicio').value;
    
    if (!servicioId || !cantidad || !precioUnitario) {
        alert('Por favor completa todos los campos requeridos');
        return;
    }
    
    // Recopilar parámetros
    const parametros = {};
    const parametrosContainer = document.getElementById('parametros-servicio');
    if (parametrosContainer) {
        const inputs = parametrosContainer.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.id.startsWith('param-')) {
                const paramId = input.id.replace('param-', '');
                parametros[paramId] = input.value;
            }
        });
    }
    
    try {
        const result = await hacerPeticionAjax(`/cotizaciones/${cotizacionId}/item-servicio/`, 'POST', {
            servicio_id: servicioId,
            cantidad: cantidad,
            precio_unitario: precioUnitario,
            descripcion_personalizada: descripcionPersonalizada,
            parametros: parametros
        });
        
        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error agregando servicio:', error);
        alert('Error al agregar el servicio');
    }
}

// Agregar material
async function agregarMaterial() {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) {
        alert('Error: No se encontró ID de cotización');
        return;
    }
    
    const materialId = document.getElementById('material-select').value;
    const cantidad = document.getElementById('cantidad-material').value;
    const precioUnitario = document.getElementById('precio-material').value;
    const descripcionPersonalizada = document.getElementById('descripcion-material').value;
    
    if (!materialId || !cantidad || !precioUnitario) {
        alert('Por favor completa todos los campos requeridos');
        return;
    }
    
    try {
        const result = await hacerPeticionAjax(`/cotizaciones/${cotizacionId}/item-material/`, 'POST', {
            material_id: materialId,
            cantidad: cantidad,
            precio_unitario: precioUnitario,
            descripcion_personalizada: descripcionPersonalizada
        });
        
        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error agregando material:', error);
        alert('Error al agregar el material');
    }
}

// Agregar mano de obra
async function agregarManoObra() {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) {
        alert('Error: No se encontró ID de cotización');
        return;
    }
    
    const descripcion = document.getElementById('descripcion-mano-obra').value;
    const horas = document.getElementById('horas-mano-obra').value;
    const precioHora = document.getElementById('precio-hora-mano-obra').value;
    
    if (!descripcion || !horas || !precioHora) {
        alert('Por favor completa todos los campos requeridos');
        return;
    }
    
    try {
        const result = await hacerPeticionAjax(`/cotizaciones/${cotizacionId}/item-mano-obra/`, 'POST', {
            descripcion: descripcion,
            horas: horas,
            precio_hora: precioHora
        });
        
        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error agregando mano de obra:', error);
        alert('Error al agregar la mano de obra');
    }
}

// Eliminar items
async function eliminarItem(tipo, itemId) {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) {
        alert('Error: No se encontró ID de cotización');
        return;
    }
    
    const tipoTexto = {
        'servicio': 'servicio',
        'material': 'material',
        'mano-obra': 'trabajo'
    };
    
    if (!confirm(`¿Estás seguro de eliminar este ${tipoTexto[tipo]}?`)) return;
    
    try {
        const result = await hacerPeticionAjax(
            `/cotizaciones/${cotizacionId}/item-${tipo}/${itemId}/eliminar/`, 
            'DELETE'
        );
        
        if (result.success) {
            location.reload();
        } else {
            alert(`Error al eliminar el ${tipoTexto[tipo]}`);
        }
    } catch (error) {
        console.error(`Error eliminando ${tipo}:`, error);
        alert(`Error al eliminar el ${tipoTexto[tipo]}`);
    }
}

function eliminarItemServicio(itemId) { eliminarItem('servicio', itemId); }
function eliminarItemMaterial(itemId) { eliminarItem('material', itemId); }
function eliminarItemManoObra(itemId) { eliminarItem('mano-obra', itemId); }

// Actualizar gastos de traslado
async function actualizarGastosTraslado() {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) return;
    
    const gastosTraslado = document.getElementById('gastos-traslado').value;
    
    try {
        const result = await hacerPeticionAjax(`/cotizaciones/${cotizacionId}/gastos-traslado/`, 'POST', {
            gastos_traslado: gastosTraslado
        });
        
        if (result.success) {
            // Actualizar totales en pantalla
            actualizarTotalesEnPantalla(result);
        }
    } catch (error) {
        console.error('Error actualizando gastos de traslado:', error);
    }
}

// Actualizar totales en pantalla
function actualizarTotalesEnPantalla(data) {
    const elementos = {
        'display-gastos-traslado': data.gastos_traslado || 0,
        'valor-neto': data.valor_neto || 0,
        'valor-iva': data.valor_iva || 0,
        'valor-total': data.valor_total || 0
    };
    
    Object.keys(elementos).forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.textContent = `$${parseInt(elementos[id]).toLocaleString()}`;
        }
    });
}

// Cambiar estado de cotización
async function cambiarEstado(nuevoEstado) {
    const cotizacionId = window.cotizacionId;
    if (!cotizacionId) return;
    
    if (!confirm('¿Estás seguro de cambiar el estado de la cotización?')) {
        return;
    }

    try {
        const result = await hacerPeticionAjax(`/cotizaciones/${cotizacionId}/estado/`, 'POST', {
            estado: nuevoEstado
        });

        if (result.success) {
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error cambiando estado:', error);
        alert('Error al cambiar el estado');
    }

    // Cerrar menú de estado
    const menu = document.getElementById('estado-menu');
    if (menu) {
        menu.style.display = 'none';
    }
}

// Toggle menú de estado
function toggleEstadoMenu() {
    const menu = document.getElementById('estado-menu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

// Cerrar menú de estado al hacer clic fuera
document.addEventListener('click', function(event) {
    const menu = document.getElementById('estado-menu');
    const button = event.target.closest('button');
    
    if (menu && (!button || !button.onclick || button.onclick.toString().indexOf('toggleEstadoMenu') === -1)) {
        menu.style.display = 'none';
    }
});

// Función para guardar cotización (modo editar)
function guardarCotizacion() {
    const form = document.getElementById('cotizacion-form');
    if (form) {
        form.submit();
    }
}

// Funciones para gestión de entidades (clientes, servicios, materiales)
function mostrarModalCliente() {
    mostrarModal('modal-cliente');
}

function mostrarModalServicioBase() {
    mostrarModal('modal-servicio-base');
}

function mostrarModalMaterialBase() {
    mostrarModal('modal-material-base');
}

// Función genérica para eliminar entidades
async function eliminarEntidad(tipo, id, nombre = '') {
    const tipos = {
        cliente: 'cliente',
        servicio: 'servicio', 
        material: 'material'
    };
    
    const mensaje = nombre ? 
        `¿Estás seguro de eliminar ${tipos[tipo]} "${nombre}"?` : 
        `¿Estás seguro de eliminar este ${tipos[tipo]}?`;
    
    if (!confirm(mensaje)) return;
    
    try {
        const response = await fetch(`/cotizaciones/${tipo}/${id}/eliminar/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            location.reload();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error(`Error eliminando ${tipo}:`, error);
        alert(`Error al eliminar el ${tipos[tipo]}`);
    }
}

// Funciones específicas para cada tipo
function eliminarCliente(id, nombre) {
    eliminarEntidad('cliente', id, nombre);
}

function eliminarServicio(id, nombre) {
    eliminarEntidad('servicio', id, nombre);
}

function eliminarMaterial(id, nombre) {
    eliminarEntidad('material', id, nombre);
}

// Función para filtrar tablas en tiempo real
function filtrarTabla(inputId, tablaId) {
    const input = document.getElementById(inputId);
    const tabla = document.getElementById(tablaId);
    
    if (!input || !tabla) return;
    
    input.addEventListener('keyup', function() {
        const filtro = this.value.toLowerCase();
        const filas = tabla.getElementsByTagName('tr');
        
        for (let i = 1; i < filas.length; i++) { // Saltar header
            const fila = filas[i];
            const texto = fila.textContent.toLowerCase();
            
            if (texto.includes(filtro)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        }
    });
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Configurar filtros de tabla si existen
    filtrarTabla('busqueda-clientes', 'tabla-clientes');
    filtrarTabla('busqueda-servicios', 'tabla-servicios');
    filtrarTabla('busqueda-materiales', 'tabla-materiales');
    
    // Configurar eventos de formularios modales
    const formsModal = document.querySelectorAll('.modal form');
    formsModal.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            // Aquí puedes agregar lógica AJAX para envío de formularios
            console.log('Formulario modal enviado');
        });
    });
});

// Función para formatear números como moneda
function formatearMoneda(numero) {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0
    }).format(numero);
}

// Función para validar formularios
function validarFormulario(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requeridos = form.querySelectorAll('[required]');
    let valido = true;
    
    requeridos.forEach(campo => {
        if (!campo.value.trim()) {
            campo.style.borderColor = 'var(--rojo-600)';
            valido = false;
        } else {
            campo.style.borderColor = 'var(--gris-300)';
        }
    });
    
    return valido;
}