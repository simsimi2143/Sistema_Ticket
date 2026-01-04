# config.py - VERSIÓN MEJORADA
import os
import sys
from datetime import timedelta

def base_path():
    """Ruta base compatible con exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.dirname(__file__))

BASE_DIR = base_path()
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-por-favor-cambiar-en-produccion'

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'ticket_system.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    TIMEZONE = 'America/Santiago'
    ITEMS_PER_PAGE = 10

    # Configuración de correo - CON VALORES POR DEFECTO ROBUSTOS
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # REMITENTE POR DEFECTO - ESTO ES CRÍTICO
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    if not mail_default_sender:
        # Si no hay MAIL_DEFAULT_SENDER, usar MAIL_USERNAME
        mail_default_sender = MAIL_USERNAME or 'noreply@ticketsystem.com'
    
    MAIL_DEFAULT_SENDER = mail_default_sender
    
    APP_URL = os.environ.get('APP_URL', 'http://127.0.0.1:5000')
    
    # Método para debuggear la configuración de email
    @property
    def mail_config_summary(self):
        return {
            'server': self.MAIL_SERVER,
            'port': self.MAIL_PORT,
            'username': self.MAIL_USERNAME,
            'sender': self.MAIL_DEFAULT_SENDER,
            'has_password': bool(self.MAIL_PASSWORD)
        }