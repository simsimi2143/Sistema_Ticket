#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
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

from app.models import Usuario, Rol, Departamento, Ticket
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Crear tablas
        db.create_all()
        
        # Verificar si ya hay datos
        if Rol.query.first():
            print("La base de datos ya tiene datos. No se inicializará de nuevo.")
            return
        
        print("Creando roles por defecto...")
        # Crear roles por defecto
        roles = [
            Rol(
                rol_name='Administrador',
                description='Acceso completo al sistema',
                perm_tickets=2,
                perm_users=2,
                perm_departments=2,
                perm_admin=2
            ),
            Rol(
                rol_name='Técnico',
                description='Puede gestionar tickets y usuarios',
                perm_tickets=2,
                perm_users=1,
                perm_departments=1,
                perm_admin=0
            ),
            Rol(
                rol_name='Usuario',
                description='Usuario normal del sistema',
                perm_tickets=2,
                perm_users=0,
                perm_departments=0,
                perm_admin=0
            ),
            Rol(
                rol_name='Solo Lectura',
                description='Solo puede ver información',
                perm_tickets=1,
                perm_users=1,
                perm_departments=1,
                perm_admin=0
            )
        ]
        
        for rol in roles:
            db.session.add(rol)
        
        db.session.commit()
        print(f"Roles creados: {len(roles)}")
        
        # Crear departamentos
        print("Creando departamentos por defecto...")
        departamentos = [
            Departamento(
                depth_name='Soporte Técnico',
                description='Departamento de soporte técnico',
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Desarrollo',
                description='Departamento de desarrollo de software',
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Infraestructura',
                description='Departamento de infraestructura IT',
                created_by='Sistema'
            ),
            Departamento(
                depth_name='Administración',
                description='Departamento administrativo',
                created_by='Sistema'
            )
        ]
        
        for depto in departamentos:
            db.session.add(depto)
        
        db.session.commit()
        print(f"Departamentos creados: {len(departamentos)}")
        
        # Crear usuario administrador
        print("Creando usuario administrador...")
        admin_role = Rol.query.filter_by(rol_name='Administrador').first()
        admin_depto = Departamento.query.filter_by(depth_name='Administración').first()
        
        admin_user = Usuario(
            name='Administrador Principal',
            email='admin@tickets.com',
            password_hash=generate_password_hash('admin123'),
            id_rol=admin_role.id_rol,
            depth_id=admin_depto.depth_id if admin_depto else None
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("\n" + "="*50)
        print("Base de datos inicializada exitosamente!")
        print("="*50)
        print("\nUsuario administrador creado:")
        print("  Email: admin@tickets.com")
        print("  Contraseña: admin123")
        print("\nRoles creados:")
        for rol in Rol.query.all():
            print(f"  - {rol.rol_name} (ID: {rol.id_rol})")
        print("\nDepartamentos creados:")
        for depto in Departamento.query.all():
            print(f"  - {depto.depth_name} (ID: {depto.depth_id})")
        print("\n" + "="*50)
        
        # Opcional: Crear algunos tickets de prueba
        crear_tickets_prueba = input("\n¿Desea crear tickets de prueba? (s/n): ").lower()
        if crear_tickets_prueba == 's':
            from datetime import datetime, timedelta
            
            tickets = [
                Ticket(
                    name='Error en sistema de login',
                    description='Los usuarios no pueden iniciar sesión desde dispositivos móviles',
                    detalles_fallo='Se recibe error 500 al intentar login desde iOS',
                    estado='Abierto',
                    id_user=admin_user.id_user,
                    created_by=admin_user.name,
                    created_at=datetime.utcnow() - timedelta(days=2)
                ),
                Ticket(
                    name='Actualización de servidor',
                    description='Necesitamos actualizar el servidor de producción',
                    detalles_fallo='El servidor actual tiene vulnerabilidades de seguridad',
                    estado='En Progreso',
                    id_user=admin_user.id_user,
                    created_by=admin_user.name,
                    created_at=datetime.utcnow() - timedelta(days=1)
                ),
                Ticket(
                    name='Nueva funcionalidad: Reportes',
                    description='Solicitud de nueva funcionalidad para generar reportes',
                    detalles_fallo='Los usuarios necesitan reportes de tickets mensuales',
                    estado='Resuelto',
                    id_user=admin_user.id_user,
                    created_by=admin_user.name,
                    created_at=datetime.utcnow() - timedelta(days=5)
                )
            ]
            
            for ticket in tickets:
                db.session.add(ticket)
            
            db.session.commit()
            print(f"\n{len(tickets)} tickets de prueba creados.")

if __name__ == '__main__':
    init_database()