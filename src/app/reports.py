"""Módulo de generación de reportes PDF para el Administrador de RFHA-IES.

HU-Admin-Reports: produce un reporte ejecutivo de la red en memoria (sin tocar disco).
"""
import io

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
            fontSize=18,
            textColor=COLOR_PRIMARY,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            parent=base["Heading2"],
            fontSize=12,
            textColor=COLOR_PRIMARY,
            spaceBefore=14,
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


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def generate_network_report(nodes: list[dict], audit_logs: list[dict], generated_at: str) -> bytes:
    """Genera el PDF en memoria y retorna los bytes.

    Args:
        nodes: lista de nodos tal como los devuelve NodeRepository.list_nodes().
        audit_logs: lista de registros de auditoría tal como los devuelve AuditRepository.list_logs().
        generated_at: cadena de fecha/hora ya formateada (p.ej. "2026-11-09 18:00 UTC").
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="RFHA-IES — Reporte Ejecutivo de la Red Federada",
        author="Sistema RFHA-IES",
    )

    styles = _build_styles()
    story = []

    # ---- Encabezado --------------------------------------------------------
    story.append(Paragraph("RFHA-IES — Reporte Ejecutivo de la Red Federada", styles["title"]))
    story.append(Paragraph(f"Generado: {generated_at}", styles["subtitle"]))
    story.append(Paragraph(
        "Universidad Distrital Francisco José de Caldas · Sistemas Distribuidos y TGS",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceAfter=10))

    # ---- Sección 1: Estado de la Red ---------------------------------------
    story.append(Paragraph("1. Estado de la Red", styles["section"]))

    total_nodes = len(nodes)
    active_nodes = sum(1 for n in nodes if n.get("status") == "ACTIVO")
    pending_nodes = sum(1 for n in nodes if n.get("status") == "PENDIENTE_APROBACION")
    other_nodes = total_nodes - active_nodes - pending_nodes

    s1_data = [
        ["Métrica", "Valor"],
        ["Total de nodos registrados", str(total_nodes)],
        ["Nodos activos (ACTIVO)", str(active_nodes)],
        ["Pendientes de aprobación", str(pending_nodes)],
        ["Otros estados", str(other_nodes)],
    ]
    story.append(_stat_table(s1_data, [10 * cm, 5 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    # ---- Sección 2: Volumen de Consultas -----------------------------------
    story.append(Paragraph("2. Volumen de Consultas", styles["section"]))

    total_logs = len(audit_logs)
    success = sum(1 for l in audit_logs if l.get("outcome") == "SUCCESS")
    denied = sum(1 for l in audit_logs if l.get("outcome") == "DENIED")
    error = sum(1 for l in audit_logs if l.get("outcome") == "ERROR")

    def _pct(n: int) -> str:
        return f"{n / total_logs * 100:.1f}%" if total_logs else "—"

    s2_data = [
        ["Métrica", "Cantidad", "Porcentaje"],
        ["Total de registros de auditoría", str(total_logs), "100%"],
        ["Consultas exitosas (SUCCESS)", str(success), _pct(success)],
        ["Consultas denegadas (DENIED)", str(denied), _pct(denied)],
        ["Errores del sistema (ERROR)", str(error), _pct(error)],
    ]
    s2_table = Table(s2_data, colWidths=[8 * cm, 3.5 * cm, 3.5 * cm])
    s2_style = TableStyle(list(_HEADER_STYLE._cmds))
    # Colorear filas de resultado
    if total_logs:
        for row_idx, result_val in [(2, success), (3, denied), (4, error)]:
            if row_idx < len(s2_data):
                col = COLOR_ACCENT if row_idx == 2 else (COLOR_DENIED if row_idx == 3 else COLOR_WARN)
                s2_style.add("TEXTCOLOR", (0, row_idx), (-1, row_idx), col)
    s2_table.setStyle(s2_style)
    story.append(s2_table)
    story.append(Spacer(1, 0.3 * cm))

    # ---- Sección 3: Resiliencia --------------------------------------------
    story.append(Paragraph("3. Resiliencia — Consultas por Fuente", styles["section"]))

    primary_hits = sum(1 for l in audit_logs if l.get("data_source") == "Primary")
    replica_hits = sum(1 for l in audit_logs if l.get("data_source") == "Replica")
    failover_pct = _pct(replica_hits) if total_logs else "—"

    s3_data = [
        ["Fuente", "Cantidad", "Porcentaje"],
        ["Nodo Primario (PRIMARY)", str(primary_hits), _pct(primary_hits)],
        ["Réplica (REPLICA / failover)", str(replica_hits), failover_pct],
        ["Sin información de fuente", str(total_logs - primary_hits - replica_hits), ""],
    ]
    story.append(_stat_table(s3_data, [8 * cm, 3.5 * cm, 3.5 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    # ---- Sección 4: Tabla detalle de últimos 20 registros ------------------
    story.append(Paragraph("4. Detalle — Últimos 20 Registros de Auditoría", styles["section"]))

    recent = audit_logs[:20]
    s4_header = ["Timestamp", "Nodo Consultante", "Estudiante", "Resultado", "Fuente"]
    s4_rows = []
    for log in recent:
        ts = str(log.get("timestamp", ""))[:19]  # cortar a segundos
        node = str(log.get("consulting_node_id", "—"))[:18]
        student = str(log.get("target_student_id", "—"))[:18]
        result = str(log.get("outcome", "—"))
        source = str(log.get("data_source", "—"))
        s4_rows.append([ts, node, student, result, source])

    if not s4_rows:
        s4_rows = [["Sin registros", "", "", "", ""]]

    s4_data = [s4_header] + s4_rows
    s4_table = Table(s4_data, colWidths=[4.2 * cm, 3.8 * cm, 3.5 * cm, 2.2 * cm, 2.3 * cm])
    s4_style = TableStyle(list(_HEADER_STYLE._cmds))
    # Colorear celdas de resultado
    for i, row in enumerate(s4_rows, start=1):
        result_val = row[3] if len(row) > 3 else ""
        if result_val == "SUCCESS":
            s4_style.add("TEXTCOLOR", (3, i), (3, i), COLOR_ACCENT)
        elif result_val == "DENIED":
            s4_style.add("TEXTCOLOR", (3, i), (3, i), COLOR_DENIED)
        elif result_val == "ERROR":
            s4_style.add("TEXTCOLOR", (3, i), (3, i), COLOR_WARN)
    s4_table.setStyle(s4_style)
    story.append(s4_table)

    # ---- Pie de página -----------------------------------------------------
    story.append(Spacer(1, 1 * cm))
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
