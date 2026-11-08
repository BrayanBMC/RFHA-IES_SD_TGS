from fastapi import APIRouter, Depends, HTTPException

from src.app.models import NodeRegistration, NodeRegistrationResponse
from src.app.repositories import DuplicateNitError, NodeRepository, get_node_repository

router = APIRouter(prefix="/api/v1/nodes", tags=["Nodos IES"])


@router.post("/register", response_model=NodeRegistrationResponse, status_code=201)
def register_node(
    body: NodeRegistration, repo: NodeRepository = Depends(get_node_repository)
) -> NodeRegistrationResponse:
    """HU-01: una universidad solicita su alta. Queda en PENDIENTE_APROBACION hasta que el admin la apruebe."""
    try:
        node = repo.create_node(body.model_dump())
    except DuplicateNitError:
        raise HTTPException(status_code=409, detail="Ya existe una solicitud o nodo con ese NIT.")
    return NodeRegistrationResponse(
        node_id=node["node_id"],
        status=node["status"],
        message="Solicitud recibida. Un administrador de la red la revisará.",
    )
