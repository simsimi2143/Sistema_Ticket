from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pytz
import os

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id_rol = db.Column(db.Integer, primary_key=True)
    rol_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    status = db.Column(db.Boolean, default=True)
    
    # Permisos específicos
    perm_tickets = db.Column(db.Integer, default=1)  # 0:no access, 1:read, 2:write
    perm_users = db.Column(db.Integer, default=0)
    perm_departments = db.Column(db.Integer, default=0)
    perm_admin = db.Column(db.Integer, default=0)
    
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)
    
    def __repr__(self):
        return f'<Rol {self.rol_name}>'

class Departamento(db.Model):
    __tablename__ = 'departamentos'
    
    depth_id = db.Column(db.Integer, primary_key=True)
    depth_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    
    usuarios = db.relationship('Usuario', backref='departamento', lazy=True)
    
    def __repr__(self):
        return f'<Departamento {self.depth_name}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id_user = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    depth_id = db.Column(db.Integer, db.ForeignKey('departamentos.depth_id'))
    status = db.Column(db.Boolean, default=True)
    
    tickets_creados = db.relationship('Ticket', foreign_keys='Ticket.id_user', backref='creador', lazy=True)
    tickets_asignados = db.relationship('Ticket', foreign_keys='Ticket.user_asigned', backref='asignado_a', lazy=True)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.id_user
    
    def __repr__(self):
        return f'<Usuario {self.name}>'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    def get_local_time():
        from flask import current_app
        tz = pytz.timezone(current_app.config.get('TIMEZONE', 'UTC'))
        return datetime.now(tz)

    ticket_id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), default='Abierto')  # Abierto, En Progreso, Cerrado, Resuelto
    detalles_fallo = db.Column(db.Text)
    
    # Nuevo campo para imagen
    image_filename = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('America/Santiago')))
    user_asigned = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('America/Santiago')), 
                          onupdate=lambda: datetime.now(pytz.timezone('America/Santiago')))
    created_by = db.Column(db.String(100))
    
    # Relaciones
    comentarios = db.relationship('Comentario', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Ticket {self.ticket_id}: {self.name}>'
    
    
    
    @property
    def image_url(self):
        if self.image_filename:
            # Usar la ruta relativa almacenada o construirla
            if self.image_path:
                # Si es una ruta relativa, convertir a URL
                if not self.image_path.startswith('http'):
                    # Asegurar que comience con /
                    if not self.image_path.startswith('/'):
                        return f"/uploads/{self.image_path.split('uploads/')[-1] if 'uploads/' in self.image_path else self.image_path}"
                    return self.image_path
                return self.image_path
            else:
                # Para compatibilidad con versiones anteriores
                return f"/uploads/{self.image_filename}"
        return None
    
    @property
    def physical_image_path(self):
        if self.image_path:
            # Si es una ruta relativa, hacerla absoluta
            if not os.path.isabs(self.image_path):
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                if not os.path.isabs(upload_folder):
                    upload_folder = os.path.join(current_app.root_path, upload_folder)
                return os.path.join(upload_folder, os.path.basename(self.image_path))
            return self.image_path
        return None
    # Propiedad para verificar si tiene imagen
    @property
    def has_image(self):
        return bool(self.image_filename)
    
    # Método para eliminar la imagen física
    def delete_image(self):
        physical_path = self.physical_image_path
        if physical_path and os.path.exists(physical_path):
            try:
                os.remove(physical_path)
                print(f"DEBUG - Imagen eliminada: {physical_path}")
            except Exception as e:
               print(f"DEBUG - Error al eliminar imagen: {e}")
    
    @property
    def created_at_local(self):
        if self.created_at:
            if self.created_at.tzinfo:
                return self.created_at.astimezone(pytz.timezone('America/Santiago'))
            utc_naive = self.created_at.replace(tzinfo=pytz.utc)
            return utc_naive.astimezone(pytz.timezone('America/Santiago'))
        return None
    
    @property
    def updated_at_local(self):
        if self.updated_at:
            if self.updated_at.tzinfo:
                return self.updated_at.astimezone(pytz.timezone('America/Santiago'))
            utc_naive = self.updated_at.replace(tzinfo=pytz.utc)
            return utc_naive.astimezone(pytz.timezone('America/Santiago'))
        return None

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.ticket_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='comentarios')
    
    def __repr__(self):
        return f'<Comentario {self.id}>'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))