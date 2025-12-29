//funcion para controlar el cerrar sesion con onclick
document.addEventListener('DOMContentLoaded', function() {
    // Referencias al DOM
    const menuButton = document.getElementById('user-menu-button');
    const dropdownMenu = document.getElementById('user-dropdown');

    // Verificar que los elementos existen (para evitar errores en login/registro)
    if (menuButton && dropdownMenu) {
        
        // 1. Evento Click en el botón
        menuButton.addEventListener('click', function(event) {
            // Detenemos la propagación para que no se active el evento de cerrar del document inmediatamente
            event.stopPropagation();
            
            // Alternar la clase 'hidden' de Tailwind
            dropdownMenu.classList.toggle('hidden');
        });

        // 2. Evento Click dentro del menú (para que no se cierre si seleccionas algo)
        dropdownMenu.addEventListener('click', function(event) {
            event.stopPropagation();
        });

        // 3. Evento Click en cualquier parte de la ventana (para cerrar si haces clic fuera)
        document.addEventListener('click', function(event) {
            // Si el menú NO tiene la clase hidden (está visible)
            if (!dropdownMenu.classList.contains('hidden')) {
                // Añadir la clase hidden para cerrarlo
                dropdownMenu.classList.add('hidden');
            }
        });
    }
});

// Funcionalidades JavaScript para el sistema de tickets

document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializar tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltip = document.createElement('div');
            tooltip.className = 'fixed bg-gray-800 text-white text-sm px-2 py-1 rounded shadow-lg z-50';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - 30) + 'px';
            tooltip.style.left = (rect.left + rect.width/2 - tooltip.offsetWidth/2) + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                document.body.removeChild(this._tooltip);
                this._tooltip = null;
            }
        });
    });
    
    // Confirmación para acciones críticas
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || '¿Está seguro de realizar esta acción?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
    
    /* Auto-ocultar mensajes flash después de 5 segundos
    const flashMessages = document.querySelectorAll('.bg-blue-100, .bg-green-100, .bg-red-100, .bg-yellow-100');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s';
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 500);
        }, 5000);
    });*/
    
    // Funcionalidad para agregar comentarios
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const content = this.querySelector('textarea[name="content"]').value;
            const ticketId = this.querySelector('input[name="ticket_id"]').value;
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            if (!content.trim()) {
                alert('Por favor ingrese un comentario');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';
            
            try {
                const response = await fetch(`/api/tickets/${ticketId}/comment`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Agregar el comentario a la lista
                    const commentsList = document.getElementById('comments-list');
                    const commentHTML = `
                        <div class="comment-bubble fade-in">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <strong class="text-gray-800">${data.comment.user_name}</strong>
                                    <span class="text-gray-500 text-sm ml-2">${data.comment.created_at}</span>
                                </div>
                            </div>
                            <p class="text-gray-700">${data.comment.content}</p>
                        </div>
                    `;
                    
                    commentsList.insertAdjacentHTML('afterbegin', commentHTML);
                    
                    // Limpiar el textarea
                    this.querySelector('textarea[name="content"]').value = '';
                    
                    // Mostrar mensaje de éxito
                    const successMsg = document.createElement('div');
                    successMsg.className = 'bg-green-100 text-green-700 p-3 rounded mb-4';
                    successMsg.textContent = 'Comentario agregado exitosamente';
                    this.parentNode.insertBefore(successMsg, this);
                    
                    setTimeout(() => {
                        successMsg.remove();
                    }, 3000);
                } else {
                    throw new Error(data.error || 'Error al agregar comentario');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
    
    // Filtro de búsqueda en tablas
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.getAttribute('data-search');
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        });
    });
    
    // Cambio de estado de tickets
    const statusSelects = document.querySelectorAll('[data-status-update]');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const ticketId = this.getAttribute('data-ticket-id');
            const newStatus = this.value;
            
            fetch(`/api/tickets/${ticketId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Actualizar visualmente el estado
                    const statusBadge = document.querySelector(`[data-status-badge="${ticketId}"]`);
                    if (statusBadge) {
                        statusBadge.textContent = newStatus;
                        statusBadge.className = `px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${getStatusClass(newStatus)}`;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    function getStatusClass(status) {
        switch(status) {
            case 'Abierto':
                return 'bg-yellow-100 text-yellow-800';
            case 'En Progreso':
                return 'bg-blue-100 text-blue-800';
            case 'Resuelto':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }
});

// main.js - Al final del archivo, dentro del DOMContentLoaded

// Calcular tiempo de resolución del ticket
function calculateResolutionTime() {
    const resolutionTimeElement = document.getElementById('tiempo-resolucion');
    if (!resolutionTimeElement) return;
    
    // Buscar el estado del ticket - varias formas posibles
    let estado = '';
    
    // 1. Intentar obtener del badge principal en el header
    const estadoBadge = document.querySelector('.px-3.py-1.rounded-full.text-sm.font-semibold');
    if (estadoBadge) {
        estado = estadoBadge.textContent.trim();
    }
    
    // 2. Si no se encuentra, buscar en el panel lateral
    if (!estado) {
        const estadoLabels = document.querySelectorAll('h3.text-sm.font-medium.text-gray-500');
        estadoLabels.forEach(label => {
            if (label.textContent.includes('Estado Actual')) {
                const estadoSpan = label.nextElementSibling.querySelector('span');
                if (estadoSpan) {
                    estado = estadoSpan.textContent.trim();
                }
            }
        });
    }
    
    // 3. Si aún no se encuentra, buscar en el select del formulario
    if (!estado) {
        const estadoSelect = document.querySelector('select[name="estado"]');
        if (estadoSelect) {
            estado = estadoSelect.value;
        }
    }
    
    console.log('Estado encontrado:', estado); // Para depuración
    
    if (!estado) {
        resolutionTimeElement.textContent = 'Estado no disponible';
        return;
    }
    
    // Solo calcular si el estado es Resuelto o Cerrado
    if (estado !== 'Resuelto' && estado !== 'Cerrado') {
        resolutionTimeElement.textContent = 'No aplica';
        return;
    }
    
    // Buscar fechas
    const labels = document.querySelectorAll('h3.text-sm.font-medium.text-gray-500');
    let creationDateText = '';
    let updateDateText = '';
    
    labels.forEach(label => {
        if (label.textContent.includes('Fecha de creación')) {
            const dateElement = label.nextElementSibling;
            if (dateElement && dateElement.tagName === 'P') {
                creationDateText = dateElement.textContent.trim();
            }
        }
        if (label.textContent.includes('Última actualización')) {
            const dateElement = label.nextElementSibling;
            if (dateElement && dateElement.tagName === 'P') {
                updateDateText = dateElement.textContent.trim();
            }
        }
    });
    
    console.log('Fecha creación:', creationDateText); // Para depuración
    console.log('Fecha actualización:', updateDateText); // Para depuración
    
    if (!creationDateText || !updateDateText) {
        resolutionTimeElement.textContent = 'Fechas no disponibles';
        return;
    }
    
    // Parsear fechas del formato dd/mm/yyyy HH:MM
    const parseDate = (dateStr) => {
        const [datePart, timePart] = dateStr.split(' ');
        const [day, month, year] = datePart.split('/');
        const [hour, minute] = timePart.split(':');
        return new Date(year, month - 1, day, hour, minute);
    };
    
    try {
        const createdDate = parseDate(creationDateText);
        const resolvedDate = parseDate(updateDateText);
        
        // Calcular diferencia
        const diffMs = resolvedDate - createdDate;
        
        if (diffMs <= 0) {
            resolutionTimeElement.textContent = 'No disponible';
            return;
        }
        
        // Convertir a días, horas, minutos
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        // Formatear el resultado
        let result = '';
        
        if (diffDays > 0) {
            result += `${diffDays} día${diffDays !== 1 ? 's' : ''}`;
            if (diffHours > 0 || diffMinutes > 0) result += ', ';
        }
        
        if (diffHours > 0) {
            result += `${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
            if (diffMinutes > 0) result += ' y ';
        }
        
        if (diffMinutes > 0 || (diffDays === 0 && diffHours === 0)) {
            result += `${diffMinutes} minuto${diffMinutes !== 1 ? 's' : ''}`;
        }
        
        resolutionTimeElement.textContent = result;
    } catch (error) {
        console.error('Error al parsear fechas:', error);
        resolutionTimeElement.textContent = 'Error en cálculo';
    }
}

// Ejecutar cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    // Tu código existente...
    
    // Agregar la llamada a la función de cálculo de tiempo
    calculateResolutionTime();
    
    // También recalcular si cambia el estado dinámicamente
    const statusSelect = document.querySelector('select[name="estado"]');
    if (statusSelect) {
        statusSelect.addEventListener('change', calculateResolutionTime);
    }
});