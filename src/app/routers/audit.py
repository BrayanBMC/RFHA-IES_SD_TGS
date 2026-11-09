from fastapi import APIRouter, Depends, Header, HTTPException, Query

from src.app import config
from src.app.models import AuditLogListResponse
from src.app.repositories import AuditRepository, get_audit_repository
from src.app.security import hash_api_key, require_admin
from src.app.repositories import get_node_repository, NodeRepository

router = APIRouter(prefix="/api/v1/audit", tags=["Auditoría"])


@router.get("/logs", response_model=AuditLogListResponse)
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    x_admin_key: str | None = Header(default=None),
    x_node_api_key: str | None = Header(default=None),
    audits: AuditRepository = Depends(get_audit_repository),
    nodes: NodeRepository = Depends(get_node_repository),
) -> AuditLogListResponse:
    """HU-09: Trazabilidad e inmutabilidad de la bitácora de auditoría.

    - Administrador general (X-Admin-Key): ve la bitácora completa de toda la red.
    - Universidad activa (X-Node-API-Key): ve los eventos donde participa su nodo.
    - Sin credencial válida: 403.
    """
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
    return AuditLogListResponse(logs=logs, total=len(logs))
