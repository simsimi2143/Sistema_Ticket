from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
import pytz
import os

# =====================
# Helpers de fecha
# =====================
def utc_now():
    """Fecha actual en UTC (naive, compatible con SQLAlchemy)"""
    return datetime.utcnow()

def to_local(dt):
    """Convierte una fecha UTC a la zona configurada"""
    if not dt:
        return None

    tz = pytz.timezone(current_app.config.get('TIMEZONE', 'UTC'))

    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    return dt.astimezone(tz)

# =====================
# MODELOS
# =====================

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id_rol = db.Column(db.Integer, primary_key=True)
    rol_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    status = db.Column(db.Boolean, default=True)

    perm_tickets = db.Column(db.Integer, default=1)
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

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
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
        raise AttributeError('password is not readable')

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
    
    ticket_id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), default='Abierto')
    detalles_fallo = db.Column(db.Text)

    image_filename = db.Column(db.String(255))
    image_path = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    user_asigned = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'))
    created_by = db.Column(db.String(100))

    comentarios = db.relationship(
        'Comentario',
        backref='ticket',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # ======== PROPIEDADES DE FECHA ========
    @property
    def created_at_local(self):
        return to_local(self.created_at)

    @property
    def updated_at_local(self):
        return to_local(self.updated_at)

    # ======== IMAGEN ========
    @property
    def image_url(self):
        return f"/uploads/{self.image_filename}" if self.image_filename else None

    @property
    def has_image(self):
        return bool(self.image_filename)

    def delete_image(self):
        if not self.image_filename:
            return
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, self.image_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar imagen: {e}")

    def __repr__(self):
        return f'<Ticket {self.ticket_id}: {self.name}>'


class Comentario(db.Model):
    __tablename__ = 'comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.ticket_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_user'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    usuario = db.relationship('Usuario', backref='comentarios')

    @property
    def created_at_local(self):
        return to_local(self.created_at)

    def __repr__(self):
        return f'<Comentario {self.id}>'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
