from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def permission_required(permission_type, level=1):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Obtener el rol del usuario
            user_role = current_user.rol
            
            # Verificar permiso basado en el tipo
            if permission_type == 'tickets':
                if user_role.perm_tickets < level:
                    flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                    return redirect(url_for('main.dashboard'))
            elif permission_type == 'users':
                if user_role.perm_users < level:
                    flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                    return redirect(url_for('main.dashboard'))
            elif permission_type == 'departments':
                if user_role.perm_departments < level:
                    flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                    return redirect(url_for('main.dashboard'))
            elif permission_type == 'admin':
                if user_role.perm_admin < level:
                    flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                    return redirect(url_for('main.dashboard'))
            else:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required('admin', 1)(f)