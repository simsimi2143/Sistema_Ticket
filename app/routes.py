from flask import render_template, redirect, url_for, flash, request, jsonify, Blueprint, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Usuario, Ticket, Departamento, Rol, Comentario
from app.forms import TicketForm, UserForm, DepartmentForm
from app.decorators import permission_required, admin_required
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.forms import RoleForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Crear el Blueprint aquí
bp = Blueprint('main', __name__)

def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    )


def save_uploaded_file(file):
    if not file or file.filename == '':
        print("DEBUG - No hay archivo para guardar")
        return None, None

    if not allowed_file(file.filename):
        print(f"DEBUG - Archivo no permitido: {file.filename}")
        flash(
            'Formato de archivo no permitido. Solo se permiten imágenes (JPG, JPEG, PNG, GIF)',
            'danger'
        )
        return None, None

    # Obtener extensión
    file_ext = os.path.splitext(file.filename)[1].lower()

    from datetime import datetime
    import uuid

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]

    base_name = secure_filename(os.path.splitext(file.filename)[0])
    base_name = base_name.replace(' ', '_')[:50]

    filename = f"{timestamp}_{unique_id}_{base_name}{file_ext}"

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    if not os.path.isabs(upload_folder):
        upload_folder = os.path.join(current_app.root_path, upload_folder)

    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)

    try:
        file.save(file_path)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"DEBUG - Archivo guardado exitosamente: {filename}")
            return filename, file_path
        else:
            flash('Error al guardar la imagen', 'danger')
            return None, None

    except Exception as e:
        print(f"DEBUG - ERROR al guardar archivo: {e}")
        flash(f'Error al guardar la imagen: {str(e)}', 'danger')
        return None, None


@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory, abort
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)
    except FileNotFoundError:
        abort(404)
        
        
@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    # Estadísticas para el dashboard
    if current_user.rol.perm_tickets >= 1:
        total_tickets = Ticket.query.count()
        tickets_abiertos = Ticket.query.filter_by(estado='Abierto').count()
        tickets_en_progreso = Ticket.query.filter_by(estado='En Progreso').count()
        
        # Tickets del usuario
        mis_tickets = Ticket.query.filter_by(id_user=current_user.id_user).count()
        tickets_asignados = Ticket.query.filter_by(user_asigned=current_user.id_user).count()
        
        # Obtener tickets recientes (5 más recientes)
        recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(5).all()
    else:
        total_tickets = tickets_abiertos = tickets_en_progreso = 0
        mis_tickets = tickets_asignados = 0
        recent_tickets = []
    
    return render_template('dashboard.html',
                         total_tickets=total_tickets,
                         tickets_abiertos=tickets_abiertos,
                         tickets_en_progreso=tickets_en_progreso,
                         mis_tickets=mis_tickets,
                         tickets_asignados=tickets_asignados,
                         recent_tickets=recent_tickets)
# ... resto del código de routes.py (las demás funciones permanecen igual)

@bp.route('/tickets')
@login_required
def tickets():
    # Verificar que el usuario tenga rol
    if not current_user.rol:
        flash('Usuario sin rol asignado. Contacte al administrador.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Continuar con el código existente...
    page = request.args.get('page', 1, type=int)
    estado = request.args.get('estado', 'todos')
    
    # Construir query basado en permisos y filtros
    if current_user.rol.perm_tickets >= 2:  # Puede ver todos los tickets
        query = Ticket.query
    else:
        query = Ticket.query.filter(
            (Ticket.id_user == current_user.id_user) | 
            (Ticket.user_asigned == current_user.id_user)
        )
    
    # Aplicar filtro de estado
    if estado != 'todos':
        query = query.filter_by(estado=estado)
    
    tickets_paginados = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('tickets/list.html', 
                         tickets=tickets_paginados,
                         estado_actual=estado)

@bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
@permission_required('tickets', 2)
def create_ticket():
    form = TicketForm()
    
    # Obtener usuarios para asignación (solo si tiene permiso)
    if current_user.rol.perm_tickets >= 2:
        usuarios = Usuario.query.filter_by(status=True).all()
        form.user_asigned.choices = [(0, 'Sin asignar')] + [(u.id_user, u.name) for u in usuarios]
    else:
        form.user_asigned.choices = [(0, 'Sin asignar')]
    
    if form.validate_on_submit():
        # Manejar la subida de imagen
        image_filename = None
        image_path = None
        
        if form.image.data:
            image_filename, image_path = save_uploaded_file(form.image.data)
        
        ticket = Ticket(
            name=form.name.data,
            description=form.description.data,
            detalles_fallo=form.detalles_fallo.data,
            estado='Abierto',
            id_user=current_user.id_user,
            user_asigned=form.user_asigned.data if form.user_asigned.data != 0 else None,
            created_by=current_user.name,
            image_filename=image_filename,
            image_path=image_path
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        flash('Ticket creado exitosamente', 'success')
        return redirect(url_for('main.ticket_detail', ticket_id=ticket.ticket_id))
    
    return render_template('tickets/create.html', form=form)

@bp.route('/tickets/<int:ticket_id>')
@login_required
@permission_required('tickets', 1)
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Verificar permisos para ver este ticket específico
    if not (current_user.rol.perm_tickets >= 2 or 
            ticket.id_user == current_user.id_user or 
            ticket.user_asigned == current_user.id_user):
        flash('No tiene permisos para ver este ticket', 'danger')
        return redirect(url_for('main.tickets'))
    
    return render_template('tickets/detail.html', ticket=ticket)


@bp.route('/tickets/<int:ticket_id>/update_status', methods=['POST'])
@login_required
@permission_required('tickets', 2)
def update_ticket_status(ticket_id):
    """Actualizar el estado de un ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    estado = request.form.get('estado')
    
    if estado:
        ticket.estado = estado
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Estado del ticket actualizado exitosamente', 'success')
    
    return redirect(url_for('main.ticket_detail', ticket_id=ticket.ticket_id))

@bp.route('/tickets/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('tickets', 2)
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketForm(obj=ticket)
    
    # Obtener usuarios para asignación
    usuarios = Usuario.query.filter_by(status=True).all()
    form.user_asigned.choices = [(0, 'Sin asignar')] + [(u.id_user, u.name) for u in usuarios]
    
    if form.validate_on_submit():
        # Manejar la subida de nueva imagen
        if form.image.data:
            # Eliminar imagen anterior si existe
            if ticket.image_filename:
                ticket.delete_image()  # Esto ahora debería funcionar
                ticket.image_filename = None
                ticket.image_path = None
            
            # Guardar nueva imagen
            image_filename = save_uploaded_file(form.image.data)
            if image_filename:
                ticket.image_filename = image_filename
                ticket.image_path = f"uploads/{image_filename}"
        
        # Actualizar otros campos
        ticket.name = form.name.data
        ticket.description = form.description.data
        ticket.detalles_fallo = form.detalles_fallo.data
        ticket.estado = form.estado.data
        ticket.user_asigned = form.user_asigned.data if form.user_asigned.data != 0 else None
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Ticket actualizado exitosamente', 'success')
        return redirect(url_for('main.ticket_detail', ticket_id=ticket.ticket_id))
    
    return render_template('tickets/edit.html', form=form, ticket=ticket)

# Agregar ruta para eliminar imagen de ticket
@bp.route('/tickets/<int:ticket_id>/delete_image', methods=['POST'])
@login_required
@permission_required('tickets', 2)
def delete_ticket_image(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.image_filename:
        # Usar el método delete_image que ahora existe
        ticket.delete_image()
        ticket.image_filename = None
        ticket.image_path = None
        db.session.commit()
        flash('Imagen eliminada exitosamente', 'success')
    else:
        flash('No hay imagen para eliminar', 'warning')
    
    return redirect(url_for('main.edit_ticket', ticket_id=ticket.ticket_id))

@bp.route('/admin/users')
@login_required
@permission_required('users', 1)
def admin_users():
    users = Usuario.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/admin/departments')
@login_required
@permission_required('departments', 1)
def admin_departments():
    departments = Departamento.query.all()
    return render_template('admin/departments.html', departments=departments)

@bp.route('/admin/roles')
@login_required
@admin_required
def admin_roles():
    roles = Rol.query.all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/api/tickets/<int:ticket_id>/comment', methods=['POST'])
@login_required
@permission_required('tickets', 1)
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'Contenido requerido'}), 400
    
    comentario = Comentario(
        ticket_id=ticket_id,
        user_id=current_user.id_user,
        contenido=data['content']
    )
    
    db.session.add(comentario)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comentario.id,
            'content': comentario.contenido,
            'user_name': current_user.name,
            'created_at': comentario.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })
    
# ========== ADMIN: USUARIOS ==========

@bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@permission_required('users', 2)
def create_user():
    form = UserForm()
    
    # Obtener roles y departamentos para los select
    roles = Rol.query.filter_by(status=True).all()
    departamentos = Departamento.query.filter_by(status=True).all()
    
    form.id_rol.choices = [(r.id_rol, r.rol_name) for r in roles]
    form.depth_id.choices = [(0, 'Sin departamento')] + [(d.depth_id, d.depth_name) for d in departamentos]
    
    if form.validate_on_submit():
        try:
            user = Usuario(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data if form.password.data else None,
                id_rol=form.id_rol.data,
                depth_id=form.depth_id.data if form.depth_id.data != 0 else None,
                status=form.status.data
            )
            
            # Si no se proporcionó contraseña, generar una aleatoria
            if not form.password.data:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(8))
                user.password = password
                # En producción, aquí enviarías un email con la contraseña
            
            db.session.add(user)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('main.admin_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return render_template('admin/create_user.html', form=form, title='Nuevo Usuario')

@bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('users', 2)
def edit_user(user_id):
    user = Usuario.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.user_id = user_id  # Para validación de email único
    
    # No requerir contraseña en edición
    form.password.validators = [Optional(), Length(min=6)]
    form.confirm_password.validators = [EqualTo('password', message='Las contraseñas deben coincidir')]
    
    # Obtener roles y departamentos para los select
    roles = Rol.query.filter_by(status=True).all()
    departamentos = Departamento.query.filter_by(status=True).all()
    
    form.id_rol.choices = [(r.id_rol, r.rol_name) for r in roles]
    form.depth_id.choices = [(0, 'Sin departamento')] + [(d.depth_id, d.depth_name) for d in departamentos]
    
    if form.validate_on_submit():
        try:
            user.name = form.name.data
            user.email = form.email.data
            user.id_rol = form.id_rol.data
            user.depth_id = form.depth_id.data if form.depth_id.data != 0 else None
            user.status = form.status.data
            
            # Actualizar contraseña solo si se proporcionó una nueva
            if form.password.data:
                user.password = form.password.data
            
            db.session.commit()
            
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('main.admin_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
    
    return render_template('admin/create_user.html', form=form, user=user, title='Editar Usuario')

@bp.route('/admin/users/<int:user_id>/toggle_status')
@login_required
@permission_required('users', 2)
def toggle_user_status(user_id):
    user = Usuario.query.get_or_404(user_id)
    
    # No permitir desactivarse a sí mismo
    if user.id_user == current_user.id_user:
        flash('No puede desactivar su propia cuenta', 'danger')
        return redirect(url_for('main.admin_users'))
    
    user.status = not user.status
    db.session.commit()
    
    status = 'activado' if user.status else 'desactivado'
    flash(f'Usuario {status} exitosamente', 'success')
    return redirect(url_for('main.admin_users'))

# ========== ADMIN: DEPARTAMENTOS ==========

@bp.route('/admin/departments/create', methods=['GET', 'POST'])
@login_required
@permission_required('departments', 2)
def create_department():
    form = DepartmentForm()
    
    if form.validate_on_submit():
        try:
            department = Departamento(
                depth_name=form.depth_name.data,
                description=form.description.data,
                status=form.status.data,
                created_by=current_user.name
            )
            
            db.session.add(department)
            db.session.commit()
            
            flash('Departamento creado exitosamente', 'success')
            return redirect(url_for('main.admin_departments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear departamento: {str(e)}', 'danger')
    
    return render_template('admin/create_department.html', form=form, title='Nuevo Departamento')

@bp.route('/admin/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('departments', 2)
def edit_department(dept_id):
    department = Departamento.query.get_or_404(dept_id)
    form = DepartmentForm(obj=department)
    
    if form.validate_on_submit():
        try:
            department.depth_name = form.depth_name.data
            department.description = form.description.data
            department.status = form.status.data
            department.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Departamento actualizado exitosamente', 'success')
            return redirect(url_for('main.admin_departments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar departamento: {str(e)}', 'danger')
    
    return render_template('admin/create_department.html', form=form, department=department, title='Editar Departamento')

@bp.route('/admin/departments/<int:dept_id>/toggle_status')
@login_required
@permission_required('departments', 2)
def toggle_department_status(dept_id):
    department = Departamento.query.get_or_404(dept_id)
    department.status = not department.status
    db.session.commit()
    
    status = 'activado' if department.status else 'desactivado'
    flash(f'Departamento {status} exitosamente', 'success')
    return redirect(url_for('main.admin_departments'))

# ========== ADMIN: ROLES ==========

@bp.route('/admin/roles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_role():
    form = RoleForm()
    
    if form.validate_on_submit():
        try:
            role = Rol(
                rol_name=form.rol_name.data,
                description=form.description.data,
                perm_tickets=form.perm_tickets.data,
                perm_users=form.perm_users.data,
                perm_departments=form.perm_departments.data,
                perm_admin=form.perm_admin.data,
                status=form.status.data
            )
            
            db.session.add(role)
            db.session.commit()
            
            flash('Rol creado exitosamente', 'success')
            return redirect(url_for('main.admin_roles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear rol: {str(e)}', 'danger')
    
    return render_template('admin/create_role.html', form=form, title='Nuevo Rol')

@bp.route('/admin/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Rol.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    
    if form.validate_on_submit():
        try:
            role.rol_name = form.rol_name.data
            role.description = form.description.data
            role.perm_tickets = form.perm_tickets.data
            role.perm_users = form.perm_users.data
            role.perm_departments = form.perm_departments.data
            role.perm_admin = form.perm_admin.data
            role.status = form.status.data
            
            db.session.commit()
            
            flash('Rol actualizado exitosamente', 'success')
            return redirect(url_for('main.admin_roles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar rol: {str(e)}', 'danger')
    
    return render_template('admin/create_role.html', form=form, role=role, title='Editar Rol')

@bp.route('/admin/roles/<int:role_id>/toggle_status')
@login_required
@admin_required
def toggle_role_status(role_id):
    role = Rol.query.get_or_404(role_id)
    role.status = not role.status
    db.session.commit()
    
    status = 'activado' if role.status else 'desactivado'
    flash(f'Rol {status} exitosamente', 'success')
    return redirect(url_for('main.admin_roles'))    