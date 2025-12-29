import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-por-favor-cambiar-en-produccion'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ticket_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración para subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración de zona horaria
    TIMEZONE = 'America/Santiago'
    
    # Configuración de paginación
    ITEMS_PER_PAGE = 10

    # Configuración de correo (CORREGIDO)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'jeanpachecotesista@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'rzfd zmjb asji edol')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'jeanpachecotesista@gmail.com')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    
    @staticmethod
    def init_app(app):
        # Crear carpeta de uploads si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)