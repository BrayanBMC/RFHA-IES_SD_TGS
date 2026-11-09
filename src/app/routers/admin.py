import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.app.models import (
    ACTIVE_STATUS,
    NODE_ID_PATTERN,
    NodeApprovalResponse,
    NodeListResponse,
    NodeSummary,
)
from src.app.reports import generate_network_report
from src.app.repositories import (
    AuditRepository,
    NodeRepository,
    get_audit_repository,
    get_node_repository,
)
from src.app.security import hash_api_key, new_api_key, require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Administrador general"], dependencies=[Depends(require_admin)])


@router.get("/nodes", response_model=NodeListResponse)
def list_nodes(
    status: str | None = Query(default=None, pattern=r"^[A-Z_]{3,30}$", description="Ej.: PENDIENTE_APROBACION"),
    nodes: NodeRepository = Depends(get_node_repository),
) -> NodeListResponse:
    """HU-02: solicitudes y nodos, con filtro opcional por estado. Nunca devuelve claves ni hashes."""
    return NodeListResponse(nodes=[NodeSummary(**n) for n in nodes.list_nodes(status)])


@router.post("/nodes/{node_id}/approve", response_model=NodeApprovalResponse)
def approve_node(node_id: str, nodes: NodeRepository = Depends(get_node_repository)) -> NodeApprovalResponse:
    """HU-02: activa el nodo y emite su API Key. La clave se devuelve una sola vez; en la base solo queda su hash SHA-256."""
    if not re.fullmatch(NODE_ID_PATTERN, node_id):
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")
    node = nodes.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")
    if node["status"] == ACTIVE_STATUS:
        raise HTTPException(status_code=409, detail="El nodo ya fue aprobado; la API Key no se puede volver a mostrar.")
    api_key = new_api_key()
    nodes.update_node(
        node_id,
        {
            "status": ACTIVE_STATUS,
            "api_key_hash": hash_api_key(api_key),
            "approved_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return NodeApprovalResponse(
        node_id=node_id,
        status=ACTIVE_STATUS,
        api_key=api_key,
        message="Nodo aprobado. Entrega esta API Key a la universidad: no se puede volver a consultar.",
    )


@router.get("/reports/network-summary")
def download_network_report(
    nodes: NodeRepository = Depends(get_node_repository),
    audits: AuditRepository = Depends(get_audit_repository),
) -> Response:
    """HU-Admin-Reports: descarga el reporte ejecutivo de la red en formato PDF.

    Solo accesible con X-Admin-Key válida (protegido por require_admin en el router).
    """
    all_nodes = nodes.list_nodes()
    all_logs = audits.list_logs(limit=200)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf_bytes = generate_network_report(all_nodes, all_logs, generated_at)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"reporte-rfha-{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf\"",
            "Cache-Control": "no-store",
        },
    )
