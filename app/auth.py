from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import Usuario, Rol
from app.forms import LoginForm, RegistrationForm

# Mover la creación del Blueprint aquí
bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            if user.status:  # Check if user is active
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(next_page or url_for('main.dashboard'))
            else:
                flash('Cuenta desactivada. Contacte al administrador.', 'danger')
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Asignar rol por defecto (Usuario normal)
        default_role = Rol.query.filter_by(rol_name='Usuario').first()
        if not default_role:
            # Crear rol por defecto si no existe
            default_role = Rol(
                rol_name='Usuario',
                description='Usuario normal del sistema',
                perm_tickets=2,  # Puede crear y ver tickets
                perm_users=0,
                perm_departments=0,
                perm_admin=0
            )
            db.session.add(default_role)
            db.session.commit()
        
        user = Usuario(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            id_rol=default_role.id_rol
        )
        
        db.session.add(user)
        db.session.commit()
        flash('¡Registro exitoso! Ya puede iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ha cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))