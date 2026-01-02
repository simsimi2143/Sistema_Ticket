# app/reportes.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
from io import BytesIO
import os
import tempfile

from app import db
from app.models import Ticket, Usuario, Departamento
from sqlalchemy import func, or_

# ======================================================
# MÉTRICAS GLOBALES
# ======================================================

def obtener_metricas_globales():
    total = Ticket.query.count()
    abiertos = Ticket.query.filter(Ticket.estado != 'Cerrado').count()
    cerrados = Ticket.query.filter(Ticket.estado == 'Cerrado').count()

    por_estado = (
        db.session.query(
            Ticket.estado,
            func.count(Ticket.ticket_id)
        )
        .group_by(Ticket.estado)
        .all()
    )
    
    # Convertir objetos Row a listas simples
    por_estado = [[estado, cantidad] for estado, cantidad in por_estado]

    return {
        "total": total,
        "abiertos": abiertos,
        "cerrados": cerrados,
        "por_estado": por_estado
    }

# ======================================================
# REPORTE 1: TICKETS POR USUARIO
# ======================================================

def obtener_tickets_por_usuario():
    usuarios = Usuario.query.filter(Usuario.status == True).all()
    data = []

    for usuario in usuarios:
        tickets = Ticket.query.filter(
            or_(
                Ticket.id_user == usuario.id_user,
                Ticket.user_asigned == usuario.id_user
            )
        ).all()

        if tickets:
            data.append({
                "usuario": usuario,
                "tickets": tickets,
                "total": len(tickets)
            })

    return data

# ======================================================
# REPORTE 2: TICKETS POR DEPARTAMENTO
# ======================================================

def obtener_tickets_por_departamento():
    resultados = (
        db.session.query(
            Departamento.depth_name,
            func.count(Ticket.ticket_id).label('cantidad')
        )
        .join(Usuario, Usuario.depth_id == Departamento.depth_id)
        .join(Ticket, Ticket.id_user == Usuario.id_user)
        .group_by(Departamento.depth_name)
        .order_by(func.count(Ticket.ticket_id).desc())
        .all()
    )
    
    # Convertir objetos Row a listas simples
    resultados = [[dept, cantidad] for dept, cantidad in resultados]
    
    return resultados

# ======================================================
# GENERACIÓN DE GRÁFICOS
# ======================================================

def generar_grafico_estados(metricas):
    """Genera gráfico de torta para estados de tickets"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    estados = [estado for estado, _ in metricas['por_estado']]
    cantidades = [cantidad for _, cantidad in metricas['por_estado']]
    
    colores_estados = {
        'Abierto': '#FCD34D',
        'En Progreso': '#60A5FA',
        'Resuelto': '#34D399',
        'Cerrado': '#9CA3AF'
    }
    
    colores = [colores_estados.get(estado, '#CBD5E1') for estado in estados]
    
    ax.pie(cantidades, labels=estados, autopct='%1.1f%%', 
           colors=colores, startangle=90)
    ax.set_title('Distribución de Tickets por Estado', fontweight='bold')
    
    # Guardar en buffer
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def generar_grafico_barras_usuarios(data):
    """Genera gráfico de barras para tickets por usuario"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Tomar top 10 usuarios
    data_sorted = sorted(data, key=lambda x: x['total'], reverse=True)[:10]
    
    nombres = [d['usuario'].name[:20] for d in data_sorted]
    totales = [d['total'] for d in data_sorted]
    
    ax.barh(nombres, totales, color='#1f3c88')
    ax.set_xlabel('Cantidad de Tickets', fontweight='bold')
    ax.set_title('Top 10 Usuarios con más Tickets', fontweight='bold')
    ax.invert_yaxis()
    
    # Agregar valores en las barras
    for i, v in enumerate(totales):
        ax.text(v + 0.5, i, str(v), va='center')
    
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

def generar_grafico_barras_departamentos(data):
    """Genera gráfico de barras para tickets por departamento"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    departamentos = [dept[:20] for dept, _ in data]
    cantidades = [cant for _, cant in data]
    
    ax.barh(departamentos, cantidades, color='#10b981')
    ax.set_xlabel('Cantidad de Tickets', fontweight='bold')
    ax.set_title('Tickets por Departamento', fontweight='bold')
    ax.invert_yaxis()
    
    for i, v in enumerate(cantidades):
        ax.text(v + 0.5, i, str(v), va='center')
    
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

# ======================================================
# PDF BASE CORPORATIVO
# ======================================================

def encabezado_pdf(c, titulo):
    c.setFillColor(colors.HexColor("#1f3c88"))
    c.rect(0, A4[1] - 80, A4[0], 80, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, A4[1] - 45, titulo)

    c.setFont("Helvetica", 9)
    c.drawRightString(
        A4[0] - 2 * cm,
        A4[1] - 55,
        f"Fecha: {datetime.now().strftime('%d-%m-%Y %H:%M')}"
    )

def pie_pdf(c):
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(
        A4[0] / 2,
        1.5 * cm,
        "Generado por Sistema de Gestión de Tickets"
    )

def dibujar_metricas(c, metricas, y):
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Métricas Globales")
    y -= 15

    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, y, f"Total tickets: {metricas['total']}")
    y -= 12
    c.drawString(2 * cm, y, f"Abiertos: {metricas['abiertos']}")
    y -= 12
    c.drawString(2 * cm, y, f"Cerrados: {metricas['cerrados']}")

    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Cantidad por estado:")
    y -= 12

    c.setFont("Helvetica", 9)
    for estado, cantidad in metricas["por_estado"]:
        c.drawString(2.5 * cm, y, f"- {estado}: {cantidad}")
        y -= 12

    return y - 10

def insertar_grafico(c, buffer, x, y, width, height):
    """Inserta un gráfico en el PDF"""
    img = ImageReader(buffer)
    c.drawImage(img, x, y, width=width, height=height, preserveAspectRatio=True)

# ======================================================
# PDF REPORTE POR USUARIO CON GRÁFICOS
# ======================================================

def generar_reporte_usuarios(path_pdf):
    metricas = obtener_metricas_globales()
    data = obtener_tickets_por_usuario()

    c = canvas.Canvas(path_pdf, pagesize=A4)
    encabezado_pdf(c, "Reporte de Tickets por Usuario")

    y = A4[1] - 110
    y = dibujar_metricas(c, metricas, y)
    
    y -= 20

    if not data:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.red)
        c.drawString(2 * cm, y, "No hay tickets registrados en el sistema")
        pie_pdf(c)
        c.save()
        return

    # GRÁFICO DE ESTADOS
    if metricas['por_estado']:
        grafico_estados = generar_grafico_estados(metricas)
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(2 * cm, y, "Distribución por Estado")
        y -= 150
        insertar_grafico(c, grafico_estados, 2*cm, y, 12*cm, 8*cm)
        y -= 20

    # GRÁFICO DE USUARIOS
    if len(data) > 0:
        c.showPage()
        encabezado_pdf(c, "Reporte de Tickets por Usuario")
        y = A4[1] - 110
        
        grafico_usuarios = generar_grafico_barras_usuarios(data)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Top 10 Usuarios")
        y -= 150
        insertar_grafico(c, grafico_usuarios, 2*cm, y, 14*cm, 10*cm)
        y -= 20

    # DETALLES POR USUARIO
    c.showPage()
    encabezado_pdf(c, "Reporte de Tickets por Usuario - Detalle")
    y = A4[1] - 110

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, f"Total de usuarios con tickets: {len(data)}")
    y -= 25

    for bloque in data:
        usuario = bloque["usuario"]
        tickets = bloque["tickets"]
        total_tickets = bloque["total"]

        if y < 120:
            c.showPage()
            encabezado_pdf(c, "Reporte de Tickets por Usuario - Detalle")
            y = A4[1] - 110

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#1f3c88"))
        c.drawString(2 * cm, y, f"Usuario: {usuario.name}")
        y -= 12

        depto = usuario.departamento.depth_name if usuario.departamento else "Sin departamento"
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(2 * cm, y, f"Departamento: {depto} | Total tickets: {total_tickets}")
        y -= 18

        for i, ticket in enumerate(tickets, 1):
            if y < 80:
                c.showPage()
                encabezado_pdf(c, "Reporte de Tickets por Usuario - Detalle")
                y = A4[1] - 110

            if ticket.estado == 'Cerrado':
                c.setFillColor(colors.green)
            elif ticket.estado == 'Resuelto':
                c.setFillColor(colors.blue)
            elif ticket.estado == 'En Progreso':
                c.setFillColor(colors.orange)
            else:
                c.setFillColor(colors.red)

            c.setFont("Helvetica", 8)
            texto = (f"{i}. #{ticket.ticket_id} | {ticket.name[:50]} | "
                    f"{ticket.estado} | Prioridad: {ticket.prioridad}")
            c.drawString(2.5 * cm, y, texto)
            c.setFillColor(colors.black)
            y -= 12

        y -= 15

    pie_pdf(c)
    c.save()

# ======================================================
# PDF REPORTE POR DEPARTAMENTO CON GRÁFICOS
# ======================================================

def generar_reporte_departamentos(path_pdf):
    metricas = obtener_metricas_globales()
    data = obtener_tickets_por_departamento()

    c = canvas.Canvas(path_pdf, pagesize=A4)
    encabezado_pdf(c, "Reporte de Tickets por Departamento")

    y = A4[1] - 110
    y = dibujar_metricas(c, metricas, y)
    
    y -= 20

    if not data:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.red)
        c.drawString(2 * cm, y, "No hay tickets por departamento registrados")
        pie_pdf(c)
        c.save()
        return

    # GRÁFICO DE ESTADOS
    if metricas['por_estado']:
        grafico_estados = generar_grafico_estados(metricas)
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(2 * cm, y, "Distribución por Estado")
        y -= 150
        insertar_grafico(c, grafico_estados, 2*cm, y, 12*cm, 8*cm)
        y -= 20

    # GRÁFICO DE DEPARTAMENTOS
    c.showPage()
    encabezado_pdf(c, "Reporte de Tickets por Departamento")
    y = A4[1] - 110
    
    grafico_deptos = generar_grafico_barras_departamentos(data)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Distribución por Departamento")
    y -= 150
    insertar_grafico(c, grafico_deptos, 2*cm, y, 14*cm, 10*cm)

    # DETALLES
    c.showPage()
    encabezado_pdf(c, "Reporte de Tickets por Departamento - Detalle")
    y = A4[1] - 110

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1f3c88"))
    c.drawString(2 * cm, y, "Distribución de Tickets por Departamento")
    y -= 20

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    
    total_tickets = sum(cantidad for _, cantidad in data)
    
    for i, (departamento, cantidad) in enumerate(data, 1):
        if y < 80:
            c.showPage()
            encabezado_pdf(c, "Reporte de Tickets por Departamento - Detalle")
            y = A4[1] - 110

        porcentaje = (cantidad / total_tickets * 100) if total_tickets > 0 else 0
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, f"{i}. {departamento}")
        y -= 12
        
        c.setFont("Helvetica", 9)
        c.drawString(3 * cm, y, f"Tickets: {cantidad} ({porcentaje:.1f}%)")
        y -= 18

    pie_pdf(c)
    c.save()