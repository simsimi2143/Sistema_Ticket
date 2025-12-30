# app/email.py
from flask_mail import Mail, Message
from flask import current_app, render_template
from threading import Thread
from app import mail
from datetime import datetime

def send_async_email(app, msg):
    """Envía el correo en un hilo separado para no bloquear la aplicación"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Error enviando correo: {e}")

def send_email(subject, recipients, text_body, html_body=None, sender=None):
    """Función general para enviar correos"""
    app = current_app._get_current_object()
    
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ticketsystem.com')
    
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=sender
    )
    msg.body = text_body
    
    if html_body:
        msg.html = html_body
    
    # Enviar en hilo separado
    Thread(target=send_async_email, args=(app, msg)).start()

def send_ticket_assigned_email(ticket, assigned_user, created_by_user):
    """Envía correo cuando se asigna un ticket"""
    
    # Correo para el usuario asignado
    if assigned_user.email:
        subject = f"[Ticket #{ticket.ticket_id}] Se te ha asignado un nuevo ticket"
        
        text_body = f"""
        Hola {assigned_user.name},
        
        Se te ha asignado el ticket #{ticket.ticket_id}: "{ticket.name}"
        
        Creado por: {created_by_user.name}
        Descripción: {ticket.description[:100]}...
        Estado: {ticket.estado}
        
        Puedes ver el ticket aquí: {current_app.config.get('APP_URL', '')}/tickets/{ticket.ticket_id}
        
        Saludos,
        Sistema de Tickets
        """
        
        html_body = render_template(
            'email/ticket_assigned.html',
            ticket=ticket,
            assigned_user=assigned_user,
            created_by_user=created_by_user
        )
        
        send_email(subject, [assigned_user.email], text_body, html_body)
        current_app.logger.info(f"Correo de asignación enviado a {assigned_user.email}")
    
    # Correo para el creador del ticket (si es diferente al asignado)
    if created_by_user.email and created_by_user.id_user != assigned_user.id_user:
        subject = f"[Ticket #{ticket.ticket_id}] Tu ticket ha sido asignado"
        
        text_body = f"""
        Hola {created_by_user.name},
        
        Tu ticket #{ticket.ticket_id}: "{ticket.name}" ha sido asignado a {assigned_user.name}.
        
        Descripción: {ticket.description[:100]}...
        Estado: {ticket.estado}
        
        Puedes ver el ticket aquí: {current_app.config.get('APP_URL', '')}/tickets/{ticket.ticket_id}
        
        Saludos,
        Sistema de Tickets
        """
        
        html_body = render_template(
            'email/ticket_assigned_creator.html',
            ticket=ticket,
            assigned_user=assigned_user,
            created_by_user=created_by_user
        )
        
        send_email(subject, [created_by_user.email], text_body, html_body)
        current_app.logger.info(f"Correo de asignación enviado al creador {created_by_user.email}")

def send_ticket_status_email(ticket, old_status, new_status, changed_by_user):
    """Envía correo cuando cambia el estado de un ticket"""
    
    # Solo enviar al creador si no es el mismo que cambió el estado
    if ticket.creador.email and ticket.creador.id_user != changed_by_user.id_user:
        subject = f"[Ticket #{ticket.ticket_id}] Estado actualizado: {old_status} → {new_status}"
        
        text_body = f"""
        Hola {ticket.creador.name},
        
        El estado de tu ticket #{ticket.ticket_id}: "{ticket.name}" ha sido actualizado.
        
        Estado anterior: {old_status}
        Nuevo estado: {new_status}
        Cambiado por: {changed_by_user.name}
        
        Descripción: {ticket.description[:100]}...
        
        Puedes ver el ticket aquí: {current_app.config.get('APP_URL', '')}/tickets/{ticket.ticket_id}
        
        Saludos,
        Sistema de Tickets
        """
        
        html_body = render_template(
            'email/ticket_status_changed.html',
            ticket=ticket,
            old_status=old_status,
            new_status=new_status,
            changed_by_user=changed_by_user
        )
        
        send_email(subject, [ticket.creador.email], text_body, html_body)
        current_app.logger.info(f"Correo de cambio de estado enviado a {ticket.creador.email}")

def send_ticket_created_email(ticket):
    """Envía correo cuando se crea un ticket (opcional)"""
    
    if ticket.creador.email:
        subject = f"[Ticket #{ticket.ticket_id}] Tu ticket ha sido creado"
        
        text_body = f"""
        Hola {ticket.creador.name},
        
        Tu ticket #{ticket.ticket_id}: "{ticket.name}" ha sido creado exitosamente.
        
        Descripción: {ticket.description[:100]}...
        Estado: {ticket.estado}
        
        Puedes ver el ticket aquí: {current_app.config.get('APP_URL', '')}/tickets/{ticket.ticket_id}
        
        Saludos,
        Sistema de Tickets
        """
        
        html_body = render_template(
            'email/ticket_created.html',
            ticket=ticket
        )
        
        send_email(subject, [ticket.creador.email], text_body, html_body)
        current_app.logger.info(f"Correo de creación enviado a {ticket.creador.email}")

def send_new_comment_email(ticket, comment, comment_author):
    """Envía correo cuando se agrega un comentario al ticket"""
    
    recipients = set()
    
    # Incluir al creador del ticket
    if ticket.creador.email:
        recipients.add(ticket.creador.email)
    
    # Incluir al usuario asignado (si existe)
    if ticket.asignado_a and ticket.asignado_a.email:
        recipients.add(ticket.asignado_a.email)
    
    # Incluir a todos los que han comentado (excepto al autor actual)
    for c in ticket.comentarios:
        if c.usuario.email and c.usuario.id_user != comment_author.id_user:
            recipients.add(c.usuario.email)
    
    # Remover al autor del comentario actual
    if comment_author.email in recipients:
        recipients.remove(comment_author.email)
    
    if recipients:
        subject = f"[Ticket #{ticket.ticket_id}] Nuevo comentario"
        
        text_body = f"""
        Se ha agregado un nuevo comentario al ticket #{ticket.ticket_id}: "{ticket.name}"
        
        Autor: {comment_author.name}
        Comentario: {comment.contenido[:200]}...
        
        Puedes ver el ticket aquí: {current_app.config.get('APP_URL', '')}/tickets/{ticket.ticket_id}
        
        Saludos,
        Sistema de Tickets
        """
        
        html_body = render_template(
            'email/new_comment.html',
            ticket=ticket,
            comment=comment,
            comment_author=comment_author
        )
        
        send_email(subject, list(recipients), text_body, html_body)
        current_app.logger.info(f"Correo de comentario enviado a {len(recipients)} destinatarios")

def send_admin_alert_unassigned(ticket):
    """Notifica a todos los admins cuando se crea un ticket sin asignar"""
    from app.models import Usuario, Rol
    # Filtramos por perm_admin > 0
    admins = Usuario.query.join(Rol).filter(Rol.perm_admin > 0).all()
    # Asegúrate de que esto sea una lista limpia de strings
    recipients = [str(admin.email) for admin in admins if admin.email]
    
    if recipients:
        subject = f"⚠️ NUEVO TICKET SIN ASIGNAR: #{ticket.ticket_id}"
        text_body = f"Se ha creado un nuevo ticket que requiere atención.\n\n" \
                    f"Ticket: {ticket.name}\n" \
                    f"Prioridad: {ticket.prioridad}\n" \
                    f"Creado por: {ticket.created_by}"
        
        # Intentamos enviar (puedes quitar el Thread temporalmente para probar si llega)
        send_email(subject, recipients, text_body)
    else:
        current_app.logger.warning("No se encontraron administradores con correo electrónico configurado.")       