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
    """Obtiene estadísticas de tickets por usuario, separando creados vs asignados"""
    
    # Primero obtener todos los usuarios activos
    usuarios = Usuario.query.filter(Usuario.status == True).all()
    data = []

    for usuario in usuarios:
        # Tickets creados por el usuario
        tickets_creados = Ticket.query.filter_by(id_user=usuario.id_user).count()
        
        # Tickets asignados al usuario
        tickets_asignados = Ticket.query.filter_by(user_asigned=usuario.id_user).count()
        
        total_general = tickets_creados + tickets_asignados
        
        # Solo incluir usuarios que tengan al menos un ticket creado o asignado
        if total_general > 0:
            data.append({
                "usuario": usuario,  # ← CAMBIADO: objeto Usuario directamente
                "total_creados": tickets_creados,
                "total_asignados": tickets_asignados,
                "total_general": total_general
            })

    # Ordenar por total general (descendente)
    data.sort(key=lambda x: x['total_general'], reverse=True)
    
    return data

# ======================================================
# REPORTE 2: TICKETS POR DEPARTAMENTO
# ======================================================

def obtener_tickets_por_departamento():
    # Opción 1: Tickets creados por usuarios del departamento
    resultados_creados = (
        db.session.query(
            Departamento.depth_name.label('departamento'),
            func.count(Ticket.ticket_id).label('cantidad')
        )
        .join(Usuario, Usuario.depth_id == Departamento.depth_id)
        .join(Ticket, Ticket.id_user == Usuario.id_user)
        .group_by(Departamento.depth_name)
        .all()
    )
    
    # Opción 2: Tickets asignados a usuarios del departamento
    resultados_asignados = (
        db.session.query(
            Departamento.depth_name.label('departamento'),
            func.count(Ticket.ticket_id).label('cantidad')
        )
        .join(Usuario, Usuario.depth_id == Departamento.depth_id)
        .join(Ticket, Ticket.user_asigned == Usuario.id_user)
        .group_by(Departamento.depth_name)
        .all()
    )
    
    # Opción 3: Tickets de usuarios sin departamento
    tickets_sin_depto = Ticket.query.join(
        Usuario, Ticket.id_user == Usuario.id_user
    ).filter(
        Usuario.depth_id == None
    ).count()
    
    # Combinar resultados
    # (Esto depende de cómo quieres contar: creados, asignados, o ambos)
    
    # Para reporte simple: solo tickets creados por departamento
    resultados = [[dept, cantidad] for dept, cantidad in resultados_creados]
    
    # Agregar "Sin Departamento" si hay tickets
    if tickets_sin_depto > 0:
        resultados.append(['Sin Departamento', tickets_sin_depto])
    
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
    """Genera gráfico de barras apiladas para tickets por usuario (creados vs asignados)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Tomar top 10 usuarios
    data_sorted = data[:10]
    
    # Acceder al objeto Usuario directamente
    nombres = [d['usuario'].name[:15] + "..." if len(d['usuario'].name) > 15 else d['usuario'].name 
               for d in data_sorted]
    creados = [d['total_creados'] for d in data_sorted]
    asignados = [d['total_asignados'] for d in data_sorted]
    
    # Crear gráfico de barras apiladas
    p1 = ax.barh(nombres, creados, color='#1f3c88', label='Creados')
    p2 = ax.barh(nombres, asignados, left=creados, color='#10b981', label='Asignados')
    
    ax.set_xlabel('Cantidad de Tickets', fontweight='bold')
    ax.set_title('Top 10 Usuarios - Tickets Creados vs Asignados', fontweight='bold', pad=20)
    ax.invert_yaxis()
    
    # Agregar leyenda
    ax.legend(loc='upper right')
    
    # Agregar valores en las barras
    for i, (creado, asignado) in enumerate(zip(creados, asignados)):
        total = creado + asignado
        if total > 0:
            # Mostrar total
            ax.text(total + 0.5, i, str(total), va='center', fontweight='bold')
            # Mostrar valores individuales si hay espacio
            if creado > 0:
                ax.text(creado/2, i, str(creado), ha='center', va='center', color='white', fontweight='bold')
            if asignado > 0 and creado > 0:
                ax.text(creado + asignado/2, i, str(asignado), ha='center', va='center', color='white', fontweight='bold')
    
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

    # GRÁFICO DE USUARIOS (BARRAS APILADAS)
    if len(data) > 0:
        c.showPage()
        encabezado_pdf(c, "Reporte de Tickets por Usuario")
        y = A4[1] - 110
        
        grafico_usuarios = generar_grafico_barras_usuarios(data)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Top 10 Usuarios - Creados vs Asignados")
        y -= 150
        insertar_grafico(c, grafico_usuarios, 2*cm, y, 14*cm, 10*cm)
        y -= 20

    # DETALLES POR USUARIO (CON COLUMNAS SEPARADAS)
    c.showPage()
    encabezado_pdf(c, "Reporte de Tickets por Usuario - Detalle")
    y = A4[1] - 110

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, f"Total de usuarios con tickets: {len(data)}")
    y -= 25
    
    # Encabezado de la tabla
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1f3c88"))
    c.drawString(2 * cm, y, "Usuario")
    c.drawString(6 * cm, y, "Departamento")
    c.drawString(10 * cm, y, "Creados")
    c.drawString(12 * cm, y, "Asignados")
    c.drawString(14 * cm, y, "Total")
    y -= 15
    
    c.setStrokeColor(colors.gray)
    c.setLineWidth(0.5)
    c.line(2 * cm, y, 16 * cm, y)
    y -= 10

    for bloque in data:
        usuario = bloque["usuario"]  # Esto ahora es un objeto Usuario
        total_creados = bloque["total_creados"]
        total_asignados = bloque["total_asignados"]
        total_general = bloque["total_general"]

        if y < 120:
            c.showPage()
            encabezado_pdf(c, "Reporte de Tickets por Usuario - Detalle")
            y = A4[1] - 110
            
            # Redibujar encabezado de tabla
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.HexColor("#1f3c88"))
            c.drawString(2 * cm, y, "Usuario")
            c.drawString(6 * cm, y, "Departamento")
            c.drawString(10 * cm, y, "Creados")
            c.drawString(12 * cm, y, "Asignados")
            c.drawString(14 * cm, y, "Total")
            y -= 15
            c.line(2 * cm, y, 16 * cm, y)
            y -= 10

        # Acceder a los atributos del objeto Usuario
        depto = usuario.departamento.depth_name if usuario.departamento else "Sin departamento"
        
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        
        # Usuario
        c.drawString(2 * cm, y, usuario.name[:20])
        
        # Departamento
        c.drawString(6 * cm, y, depto[:15])
        
        # Tickets creados (azul)
        c.setFillColor(colors.HexColor("#1f3c88"))
        c.drawString(10 * cm, y, str(total_creados))
        
        # Tickets asignados (verde)
        c.setFillColor(colors.HexColor("#10b981"))
        c.drawString(12 * cm, y, str(total_asignados))
        
        # Total (púrpura)
        c.setFillColor(colors.HexColor("#8b5cf6"))
        c.drawString(14 * cm, y, str(total_general))
        
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