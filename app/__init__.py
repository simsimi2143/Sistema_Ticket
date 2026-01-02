# app/__init__.py
import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
import pytz

def resource_path(relative_path):
    """Obtiene la ruta correcta tanto en exe como en desarrollo"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_path, relative_path)



db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()  # Agregar esto

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=resource_path('templates'),
        static_folder=resource_path('static')
    )

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    app.timezone = pytz.timezone(app.config['TIMEZONE'])

    @app.context_processor
    def inject_now():
        return {'chile_now': datetime.now(app.timezone)}

    return app
