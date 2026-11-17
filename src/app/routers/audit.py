from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from src.app import config
from src.app.models import AuditLogListResponse
from src.app.repositories import AuditRepository, NodeRepository, get_audit_repository, get_node_repository
from src.app.security import hash_api_key

router = APIRouter(prefix="/api/v1/audit", tags=["Auditoría"])


@router.get("/logs", response_model=AuditLogListResponse)
def get_audit_logs(
    response: Response,
    limit: int = Query(default=50, ge=1, le=200),
    since: str | None = Query(default=None, description="Filtro desde fecha ISO-8601 UTC, ej. 2026-11-01T00:00:00Z"),
    x_admin_key: str | None = Header(default=None),
    x_node_api_key: str | None = Header(default=None),
    audits: AuditRepository = Depends(get_audit_repository),
    nodes: NodeRepository = Depends(get_node_repository),
) -> AuditLogListResponse:
    """HU-09: Trazabilidad e inmutabilidad de la bitácora de auditoría.

    - Administrador general (X-Admin-Key): ve la bitácora completa de toda la red.
    - Universidad activa (X-Node-API-Key): ve los eventos donde participa su nodo.
    - Sin credencial válida: 403.
    - `since` (opcional): devuelve solo eventos a partir de esa fecha/hora UTC (ISO-8601).
    - `limit`: máximo de registros (1-200, default 50).
    """
    # Bug fix: fuerza no-cache para garantizar logs en tiempo real
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    filter_node = None
    is_admin = bool(config.ADMIN_KEY and x_admin_key == config.ADMIN_KEY)

    if not is_admin:
        if not x_node_api_key:
            raise HTTPException(status_code=403, detail="Acceso denegado: se requiere clave de administrador o API Key de nodo.")
        node = nodes.find_by_api_key_hash(hash_api_key(x_node_api_key))
        if not node or node.get("status") != "ACTIVO":
            raise HTTPException(status_code=403, detail="API Key de nodo inválida o nodo inactivo.")
        filter_node = node["node_id"]

    logs = audits.list_logs(node_id=filter_node, limit=limit)

    # Filtro por fecha (Mitigación B5)
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            logs = [log for log in logs if datetime.fromisoformat(
                log["timestamp"].replace("Z", "+00:00")
            ) >= since_dt]
        except (ValueError, KeyError):
            raise HTTPException(status_code=422, detail="Formato de 'since' inválido. Usa ISO-8601, ej. 2026-11-01T00:00:00Z")

    return AuditLogListResponse(logs=logs, total=len(logs))
