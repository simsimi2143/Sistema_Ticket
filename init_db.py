#!/usr/bin/env python3
"""
Script V2 para inicializar la base de datos con la nueva estructura completa
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config

# Crear una aplicación Flask mínima para el contexto
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la base de datos
from app import db
db.init_app(app)

from app.models import Usuario, Rol, Departamento, Ticket, Comentario
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def init_database_v2():
    """Inicializa la base de datos con la estructura completa V2"""
    with app.app_context():
        print("="*60)
        print("INICIALIZACIÓN V2 - SISTEMA DE TICKETS CON IMÁGENES")
        print("="*60)
        
        # Crear tablas
        print("\n[1/4] Creando tablas...")
        db.create_all()
        print("✓ Tablas creadas")
        
        # Verificar si ya hay datos
        if Rol.query.first():
            print("\n⚠ La base de datos ya tiene datos.")
            respuesta = input("¿Desea recrear la base de datos? (Se perderán los datos) (s/n): ").lower()
            if respuesta != 's':
                print("Operación cancelada.")
                return
            else:
                print("Eliminando datos existentes...")
                db.drop_all()
                db.create_all()
                print("✓ Base de datos recreada")
        
        # Crear roles
        print("\n[2/4] Creando roles...")
        roles = [
            Rol(
                rol_name='Administrador',
                description='Acceso completo al sistema',
                perm_tickets=2,
                perm_users=2,
                perm_departments=2,
                perm_admin=2,
                status=True
            ),
            Rol(
                rol_name='Técnico',
                description='Puede gestionar tickets y usuarios',
                perm_tickets=2,
                perm_users=1,
                perm_departments=1,
                perm_admin=0,
                status=True
            ),
            Rol(
                rol_name='Usuario',
                description='Usuario normal del sistema',
                perm_tickets=2,
                perm_users=0,
                perm_departments=0,
                perm_admin=0,
                status=True
            ),
            Rol(
                rol_name='Solo Lectura',
                description='Solo puede ver información',
                perm_tickets=1,
                perm_users=1,
                perm_departments=1,
                perm_admin=0,
                status=True
            )
        ]
        
        for rol in roles:
            db.session.add(rol)
        db.session.commit()
        print(f"✓ {len(roles)} roles creados")
        
        # Crear departamentos
        print("\n[3/4] Creando departamentos...")
        departamentos = [
            Departamento(
                depth_name='Soporte Técnico',
                description='Departamento de soporte técnico y helpdesk',
                status=True,
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Desarrollo',
                description='Departamento de desarrollo de software',
                status=True,
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Infraestructura',
                description='Departamento de infraestructura IT',
                status=True,
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Administración',
                description='Departamento administrativo',
                status=True,
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Redes',
                description='Departamento de redes y comunicaciones',
                status=True,
                created_by='Sistema'
            )
        ]
        
        for depto in departamentos:
            db.session.add(depto)
        db.session.commit()
        print(f"✓ {len(departamentos)} departamentos creados")
        
        # Crear usuarios
        print("\n[4/4] Creando usuarios...")
        
        # Obtener roles y departamentos
        admin_role = Rol.query.filter_by(rol_name='Administrador').first()
        tecnico_role = Rol.query.filter_by(rol_name='Técnico').first()
        usuario_role = Rol.query.filter_by(rol_name='Usuario').first()
        
        soporte_depto = Departamento.query.filter_by(depth_name='Soporte Técnico').first()
        desarrollo_depto = Departamento.query.filter_by(depth_name='Desarrollo').first()
        
        # Lista de usuarios a crear
        usuarios = [
            {
                'name': 'Administrador Principal',
                'email': 'admin@tickets.com',
                'password': 'admin123',
                'rol': admin_role,
                'departamento': None,
                'status': True
            },
            {
                'name': 'Juan Pérez',
                'email': 'juan@tickets.com',
                'password': 'tecnico123',
                'rol': tecnico_role,
                'departamento': soporte_depto,
                'status': True
            },
            {
                'name': 'María González',
                'email': 'maria@tickets.com',
                'password': 'usuario123',
                'rol': usuario_role,
                'departamento': desarrollo_depto,
                'status': True
            },
            {
                'name': 'Carlos Rodríguez',
                'email': 'carlos@tickets.com',
                'password': 'usuario456',
                'rol': usuario_role,
                'departamento': soporte_depto,
                'status': True
            },
            {
                'name': 'Ana Martínez',
                'email': 'ana@tickets.com',
                'password': 'tecnico456',
                'rol': tecnico_role,
                'departamento': desarrollo_depto,
                'status': True
            }
        ]
        
        for user_data in usuarios:
            user = Usuario(
                name=user_data['name'],
                email=user_data['email'],
                password=user_data['password'],
                id_rol=user_data['rol'].id_rol,
                depth_id=user_data['departamento'].depth_id if user_data['departamento'] else None,
                status=user_data['status']
            )
            db.session.add(user)
        
        db.session.commit()
        print(f"✓ {len(usuarios)} usuarios creados")
        
        # Crear carpeta de uploads
        uploads_dir = os.path.join('app', 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        print(f"\n✓ Carpeta de uploads creada: {uploads_dir}")
        
        # Crear tickets de ejemplo
        print("\nCreando tickets de ejemplo con imágenes...")
        
        # Obtener usuarios para asignar tickets
        admin_user = Usuario.query.filter_by(email='admin@tickets.com').first()
        juan_user = Usuario.query.filter_by(email='juan@tickets.com').first()
        maria_user = Usuario.query.filter_by(email='maria@tickets.com').first()
        
        tickets = [
            Ticket(
                name='Error crítico en servidor de producción',
                description='El servidor principal presenta caídas intermitentes durante las horas pico',
                detalles_fallo='CPU al 100%, memoria agotada. Logs muestran error OutOfMemoryException',
                estado='Abierto',
                id_user=admin_user.id_user,
                user_asigned=juan_user.id_user,
                created_by=admin_user.name,
                image_filename='server_error.jpg',
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Ticket(
                name='Problema con base de datos',
                description='Las consultas a la base de datos son extremadamente lentas',
                detalles_fallo='Timeout en consultas que antes tomaban menos de 1 segundo',
                estado='En Progreso',
                id_user=maria_user.id_user,
                user_asigned=admin_user.id_user,
                created_by=maria_user.name,
                image_filename='database_issue.jpg',
                created_at=datetime.utcnow() - timedelta(days=3)
            ),
            Ticket(
                name='Actualización de seguridad requerida',
                description='Necesitamos aplicar parches de seguridad críticos',
                detalles_fallo='Vulnerabilidad CVE-2024-1234 detectada en servidores web',
                estado='Resuelto',
                id_user=juan_user.id_user,
                user_asigned=juan_user.id_user,
                created_by=juan_user.name,
                image_filename='security_update.jpg',
                created_at=datetime.utcnow() - timedelta(days=7)
            ),
            Ticket(
                name='Solicitud de nuevo equipo',
                description='Necesito una laptop nueva para desarrollo',
                detalles_fallo='Equipo actual no cumple con requisitos para desarrollo móvil',
                estado='Abierto',
                id_user=maria_user.id_user,
                created_by=maria_user.name,
                image_filename='new_equipment.jpg',
                created_at=datetime.utcnow() - timedelta(hours=12)
            ),
            Ticket(
                name='Error en aplicación móvil',
                description='La app móvil se cierra inesperadamente en iOS 17',
                detalles_fallo='Crash report: EXC_BAD_ACCESS en módulo de geolocalización',
                estado='En Progreso',
                id_user=admin_user.id_user,
                user_asigned=juan_user.id_user,
                created_by=admin_user.name,
                image_filename='mobile_app.jpg',
                created_at=datetime.utcnow() - timedelta(days=2)
            )
        ]
        
        for ticket in tickets:
            db.session.add(ticket)
        
        db.session.commit()
        print(f"✓ {len(tickets)} tickets de ejemplo creados")
        
        # Crear algunos comentarios
        print("\nCreando comentarios de ejemplo...")
        
        comentarios = [
            Comentario(
                ticket_id=tickets[0].ticket_id,
                user_id=juan_user.id_user,
                contenido='He revisado los logs y confirmo el problema de memoria. Necesitamos aumentar la RAM del servidor.',
                created_at=datetime.utcnow() - timedelta(hours=6)
            ),
            Comentario(
                ticket_id=tickets[0].ticket_id,
                user_id=admin_user.id_user,
                contenido='¿Cuánta RAM adicional se necesita? Por favor proporciona especificaciones.',
                created_at=datetime.utcnow() - timedelta(hours=4)
            ),
            Comentario(
                ticket_id=tickets[1].ticket_id,
                user_id=admin_user.id_user,
                contenido='He optimizado las consultas y creado índices nuevos. La velocidad debería mejorar en un 80%.',
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        
        for comentario in comentarios:
            db.session.add(comentario)
        
        db.session.commit()
        print(f"✓ {len(comentarios)} comentarios creados")
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\nRESUMEN:")
        print(f"  • Roles creados: {len(roles)}")
        print(f"  • Departamentos creados: {len(departamentos)}")
        print(f"  • Usuarios creados: {len(usuarios)}")
        print(f"  • Tickets creados: {len(tickets)}")
        print(f"  • Comentarios creados: {len(comentarios)}")
        
        print("\nCREDENCIALES DE ACCESO:")
        print("  Administrador:")
        print(f"    Email: admin@tickets.com")
        print(f"    Contraseña: admin123")
        print("\n  Técnico:")
        print(f"    Email: juan@tickets.com")
        print(f"    Contraseña: tecnico123")
        print("\n  Usuario:")
        print(f"    Email: maria@tickets.com")
        print(f"    Contraseña: usuario123")
        
        print("\nCARPETA DE UPLOADS:")
        print(f"  Ruta: {uploads_dir}")
        print(f"  URL de imágenes: /static/uploads/[nombre_archivo]")
        
        print("\n" + "="*60)
        print("¡SISTEMA LISTO PARA USAR!")
        print("="*60)
        print("\nEjecuta: python run.py")
        print("Accede a: http://localhost:5000")
        print("\nNota: Las imágenes son placeholders. Sube imágenes reales desde el formulario.")

if __name__ == '__main__':
    init_database_v2()