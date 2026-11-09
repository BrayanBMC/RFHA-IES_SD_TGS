"""Módulo de generación de reportes PDF para el Administrador de RFHA-IES.

HU-Admin-Reports: produce reportes especializados o ejecutivos de la red en memoria (sin tocar disco).
Tipos soportados:
  - general: Reporte Ejecutivo Completo (Red, Consultas, Resiliencia y Auditoría)
  - auditoria: Bitácora Forense de Seguridad y Trazabilidad de Consultas
  - resiliencia: Análisis de Disponibilidad, Tolerancia a Fallos y Failover (HU-08)
  - nodos: Catálogo y Estado de Universidades Federadas (HU-01, HU-02)
"""
import io
from typing import Literal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# ---------------------------------------------------------------------------
# Paleta de colores institucional
# ---------------------------------------------------------------------------
COLOR_PRIMARY = colors.HexColor("#1a4f8a")   # azul institucional
COLOR_ACCENT = colors.HexColor("#2e7d32")    # verde éxito
COLOR_DENIED = colors.HexColor("#c62828")    # rojo denegado
COLOR_WARN = colors.HexColor("#f57f17")      # naranja error/warn
COLOR_LIGHT_BG = colors.HexColor("#f0f4f8")  # fondo secciones
COLOR_WHITE = colors.white


# ---------------------------------------------------------------------------
# Estilos de párrafo
# ---------------------------------------------------------------------------
def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=16,
            textColor=COLOR_PRIMARY,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            parent=base["Heading2"],
            fontSize=11,
            textColor=COLOR_PRIMARY,
            spaceBefore=12,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "normal": ParagraphStyle(
            "BodyNormal",
            parent=base["Normal"],
            fontSize=9,
            spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "FooterText",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#888888"),
            alignment=1,  # center
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontSize=7,
            textColor=colors.HexColor("#aaaaaa"),
            alignment=1,
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Helpers de tabla
# ---------------------------------------------------------------------------
_HEADER_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
    ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])


def _stat_table(data: list[list], col_widths: list[float]) -> Table:
    t = Table(data, colWidths=col_widths)
    t.setStyle(_HEADER_STYLE)
    return t


def _pct(n: int, total: int) -> str:
    return f"{n / total * 100:.1f}%" if total else "0.0%"


# ---------------------------------------------------------------------------
# Función generadora modular
# ---------------------------------------------------------------------------
def generate_network_report(
    nodes: list[dict],
    audit_logs: list[dict],
    generated_at: str,
    report_type: str = "general",
) -> bytes:
    """Genera el PDF en memoria según el tipo de reporte solicitado.

    Tipos:
      - 'general': consolidado ejecutivo
      - 'auditoria': auditoría y seguridad
      - 'resiliencia': tolerancia a fallos y réplicas
      - 'nodos': catálogo institucional y estado de nodos
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title="RFHA-IES — Reportes Especializados",
        author="Sistema RFHA-IES",
    )

    styles = _build_styles()
    story = []

    titles_map = {
        "general": "Reporte Ejecutivo Global de la Red Federada",
        "auditoria": "Reporte Forense y Bitácora de Auditoría",
        "resiliencia": "Reporte de Resiliencia y Tolerancia a Fallos (HU-08)",
        "nodos": "Reporte de Directorio y Estado de Nodos Federados",
    }
    report_title = titles_map.get(report_type, titles_map["general"])

    # ---- Encabezado --------------------------------------------------------
    story.append(Paragraph(f"RFHA-IES — {report_title}", styles["title"]))
    story.append(Paragraph(f"Generado: {generated_at} · Tipo: {report_type.upper()}", styles["subtitle"]))
    story.append(Paragraph(
        "Universidad Distrital Francisco José de Caldas · Sistemas Distribuidos y Teoría General de Sistemas",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceAfter=10))

    total_nodes = len(nodes)
    active_nodes = sum(1 for n in nodes if n.get("status") == "ACTIVO")
    pending_nodes = sum(1 for n in nodes if n.get("status") == "PENDIENTE_APROBACION")

    total_logs = len(audit_logs)
    success = sum(1 for l in audit_logs if l.get("outcome") == "SUCCESS")
    denied = sum(1 for l in audit_logs if l.get("outcome") == "DENIED")
    error = sum(1 for l in audit_logs if l.get("outcome") == "ERROR")

    primary_hits = sum(1 for l in audit_logs if l.get("data_source") == "Primary")
    replica_hits = sum(1 for l in audit_logs if l.get("data_source") == "Replica")

    # =========================================================================
    # REPORTE TIPO: NODOS
    # =========================================================================
    if report_type == "nodos":
        story.append(Paragraph("1. Resumen de Instituciones", styles["section"]))
        s_data = [
            ["Métrica", "Cantidad"],
            ["Total de nodos registrados", str(total_nodes)],
            ["Nodos Activos (Aprobados)", str(active_nodes)],
            ["Nodos Pendientes de Aprobación", str(pending_nodes)],
        ]
        story.append(_stat_table(s_data, [10 * cm, 6 * cm]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("2. Directorio Detallado de Nodos", styles["section"]))
        n_header = ["ID Nodo", "Institución", "NIT", "Dominio", "Estado"]
        n_rows = []
        for n in nodes:
            n_rows.append([
                str(n.get("node_id", ""))[:12],
                str(n.get("name", ""))[:28],
                str(n.get("nit", ""))[:14],
                str(n.get("domain", ""))[:18],
                str(n.get("status", "")),
            ])
        if not n_rows:
            n_rows = [["Sin nodos registrados", "", "", "", ""]]
        n_table = Table([n_header] + n_rows, colWidths=[3.2 * cm, 5.5 * cm, 2.8 * cm, 3.5 * cm, 2.5 * cm])
        n_table.setStyle(_HEADER_STYLE)
        story.append(n_table)

    # =========================================================================
    # REPORTE TIPO: RESILIENCIA (HU-08)
    # =========================================================================
    elif report_type == "resiliencia":
        story.append(Paragraph("1. Diagnóstico de Disponibilidad y Tolerancia a Fallos", styles["section"]))
        r_data = [
            ["Métrica de Resiliencia", "Valor", "Porcentaje"],
            ["Total de consultas federadas atendidas", str(total_logs), "100%"],
            ["Consultas atendidas por Nodo Primario", str(primary_hits), _pct(primary_hits, total_logs)],
            ["Conmutaciones a Réplica (Failover HU-08)", str(replica_hits), _pct(replica_hits, total_logs)],
            ["Consultas sin entrega de datos", str(total_logs - primary_hits - replica_hits), _pct(total_logs - primary_hits - replica_hits, total_logs)],
        ]
        story.append(_stat_table(r_data, [8.5 * cm, 4 * cm, 4.5 * cm]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("2. Eventos de Conmutación / Réplica Registrados", styles["section"]))
        replica_logs = [l for l in audit_logs if l.get("data_source") == "Replica"][:25]
        rl_header = ["Timestamp", "Nodo Consultante", "Estudiante", "Motivo / Causa"]
        rl_rows = []
        for l in replica_logs:
            rl_rows.append([
                str(l.get("timestamp", ""))[:19],
                str(l.get("consulting_node_id", ""))[:16],
                str(l.get("target_student_id", ""))[:16],
                str(l.get("reason", "Failover a réplica"))[:30],
            ])
        if not rl_rows:
            rl_rows = [["No se han presentado caídas o no hay consultas en réplica", "", "", ""]]
        rl_table = Table([rl_header] + rl_rows, colWidths=[4.2 * cm, 4.2 * cm, 3.8 * cm, 5.0 * cm])
        rl_table.setStyle(_HEADER_STYLE)
        story.append(rl_table)

    # =========================================================================
    # REPORTE TIPO: AUDITORÍA
    # =========================================================================
    elif report_type == "auditoria":
        story.append(Paragraph("1. Resumen de Seguridad y Acceso", styles["section"]))
        a_data = [
            ["Resultado de Consulta", "Cantidad", "Porcentaje"],
            ["Consultas Exitosas (SUCCESS)", str(success), _pct(success, total_logs)],
            ["Consultas Denegadas / Bloqueadas (DENIED)", str(denied), _pct(denied, total_logs)],
            ["Errores de Integridad / Red (ERROR)", str(error), _pct(error, total_logs)],
            ["Total de Registros Forenses", str(total_logs), "100%"],
        ]
        story.append(_stat_table(a_data, [8.5 * cm, 4 * cm, 4.5 * cm]))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph("2. Registro Forense Cronológico de Consultas (Últimos 35)", styles["section"]))
        aud_recent = audit_logs[:35]
        ah_header = ["Timestamp", "Consultante", "Estudiante", "Resultado", "IP Cliente"]
        ah_rows = []
        for l in aud_recent:
            ah_rows.append([
                str(l.get("timestamp", ""))[:19],
                str(l.get("consulting_node_id", ""))[:14],
                str(l.get("target_student_id", ""))[:14],
                str(l.get("outcome", ""))[:10],
                str(l.get("client_ip", "127.0.0.1"))[:15],
            ])
        if not ah_rows:
            ah_rows = [["Sin registros de auditoría", "", "", "", ""]]
        ah_table = Table([ah_header] + ah_rows, colWidths=[4.0 * cm, 3.6 * cm, 3.5 * cm, 3.0 * cm, 3.1 * cm])
        ah_style = TableStyle(list(_HEADER_STYLE._cmds))
        for idx, row in enumerate(ah_rows, start=1):
            if row[3] == "SUCCESS":
                ah_style.add("TEXTCOLOR", (3, idx), (3, idx), COLOR_ACCENT)
            elif row[3] == "DENIED":
                ah_style.add("TEXTCOLOR", (3, idx), (3, idx), COLOR_DENIED)
            elif row[3] == "ERROR":
                ah_style.add("TEXTCOLOR", (3, idx), (3, idx), COLOR_WARN)
        ah_table.setStyle(ah_style)
        story.append(ah_table)

    # =========================================================================
    # REPORTE TIPO: GENERAL (CONSOLIDADO)
    # =========================================================================
    else:
        story.append(Paragraph("1. Estado de la Red", styles["section"]))
        s1_data = [
            ["Métrica", "Valor"],
            ["Total de nodos registrados", str(total_nodes)],
            ["Nodos activos (ACTIVO)", str(active_nodes)],
            ["Pendientes de aprobación", str(pending_nodes)],
        ]
        story.append(_stat_table(s1_data, [10 * cm, 6 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("2. Volumen y Seguridad de Consultas", styles["section"]))
        s2_data = [
            ["Métrica", "Cantidad", "Porcentaje"],
            ["Total de registros de auditoría", str(total_logs), "100%"],
            ["Consultas exitosas (SUCCESS)", str(success), _pct(success, total_logs)],
            ["Consultas denegadas (DENIED)", str(denied), _pct(denied, total_logs)],
            ["Errores del sistema (ERROR)", str(error), _pct(error, total_logs)],
        ]
        story.append(_stat_table(s2_data, [8 * cm, 4 * cm, 4 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("3. Resiliencia — Consultas por Fuente", styles["section"]))
        s3_data = [
            ["Fuente", "Cantidad", "Porcentaje"],
            ["Nodo Primario (PRIMARY)", str(primary_hits), _pct(primary_hits, total_logs)],
            ["Réplica (REPLICA / failover HU-08)", str(replica_hits), _pct(replica_hits, total_logs)],
            ["Sin entrega de datos", str(total_logs - primary_hits - replica_hits), _pct(total_logs - primary_hits - replica_hits, total_logs)],
        ]
        story.append(_stat_table(s3_data, [8 * cm, 4 * cm, 4 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("4. Muestra de Auditoría Reciente", styles["section"]))
        recent = audit_logs[:15]
        s4_header = ["Timestamp", "Nodo Consultante", "Estudiante", "Resultado", "Fuente"]
        s4_rows = []
        for log in recent:
            s4_rows.append([
                str(log.get("timestamp", ""))[:19],
                str(log.get("consulting_node_id", ""))[:16],
                str(log.get("target_student_id", ""))[:16],
                str(log.get("outcome", ""))[:10],
                str(log.get("data_source", ""))[:10],
            ])
        if not s4_rows:
            s4_rows = [["Sin registros", "", "", "", ""]]
        s4_table = Table([s4_header] + s4_rows, colWidths=[4.2 * cm, 3.8 * cm, 3.5 * cm, 2.5 * cm, 2.5 * cm])
        s4_table.setStyle(_HEADER_STYLE)
        story.append(s4_table)

    # ---- Pie de página -----------------------------------------------------
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=6))
    story.append(Paragraph(
        "Universidad Distrital Francisco José de Caldas · Proyecto RFHA-IES · Sistemas Distribuidos y TGS",
        styles["footer"],
    ))
    story.append(Paragraph(f"Reporte generado el {generated_at}", styles["footer"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "⚠ Este documento puede contener datos ficticios generados para fines académicos y de demostración. "
        "No representa información real de estudiantes ni instituciones.",
        styles["disclaimer"],
    ))

    doc.build(story)
    return buffer.getvalue()
