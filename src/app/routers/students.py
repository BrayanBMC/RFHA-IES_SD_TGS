import re
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from src.app import config
from src.app.models import (
    ACTIVE_STATUS,
    RevokeResponse,
    StudentCredentials,
    TokenInfo,
    TokenListResponse,
    TokenRequest,
    TokenResponse,
)
from src.app.repositories import (
    NodeRepository,
    RecordRepository,
    TokenRepository,
    get_node_repository,
    get_record_repository,
    get_token_repository,
)
from src.app.security import verify_password
from src.app.tokens import issue_token

router = APIRouter(prefix="/api/v1/student", tags=["Estudiante"])

JTI_PATTERN = r"[0-9a-f]{32}"


def _iso(epoch) -> str:
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()


MAX_ATTEMPTS = 5  # intentos fallidos por cédula antes de bloquear
LOCK_SECONDS = 15 * 60
LOCK_PREFIX = "LOCK#"  # el contador vive en TokensTable (clave "LOCK#<cédula>"): sin tablas nuevas


def authenticate_student(credentials: StudentCredentials, records: RecordRepository, tokens: TokenRepository) -> dict:
    """Cédula + clave sembrada por el nodo (B1), con un máximo de 5 intentos fallidos por cédula.

    Al quinto fallo la cédula queda bloqueada 15 minutos (429). El contador cuenta igual exista o no la cédula,
    así que no revela qué cédulas están registradas. Un ingreso correcto reinicia el contador.
    """
    key = LOCK_PREFIX + credentials.document_number
    now = int(time.time())
    state = tokens.get(key) or {}
    if int(state.get("locked_until", 0)) > now:
        minutes = (int(state["locked_until"]) - now + 59) // 60
        raise HTTPException(status_code=429, detail=f"Demasiados intentos fallidos. Espera {minutes} min e inténtalo de nuevo.")
    failures = int(state.get("failures", 0)) if int(state.get("ttl", 0)) > now else 0

    found = records.find_by_document(credentials.document_number)
    for record in found:
        if verify_password(credentials.password, record.get("password_hash")):
            if failures:
                tokens.put({"jti": key, "failures": 0, "locked_until": 0, "ttl": now + LOCK_SECONDS})
            return record
    if not found:
        verify_password(credentials.password, None)  # mismo costo de cálculo que una cédula existente

    failures += 1
    locked = failures >= MAX_ATTEMPTS
    tokens.put(
        {"jti": key, "failures": failures, "locked_until": now + LOCK_SECONDS if locked else 0, "ttl": now + LOCK_SECONDS}
    )
    if locked:
        raise HTTPException(status_code=429, detail="Demasiados intentos fallidos. La cédula queda bloqueada 15 minutos.")
    left = MAX_ATTEMPTS - failures
    raise HTTPException(
        status_code=401, detail=f"Cédula o clave incorrecta. Te quedan {left} intento{'s' if left != 1 else ''}."
    )


@router.post("/auth-token", response_model=TokenResponse, status_code=201)
def create_auth_token(
    body: TokenRequest,
    records: RecordRepository = Depends(get_record_repository),
    nodes: NodeRepository = Depends(get_node_repository),
    tokens: TokenRepository = Depends(get_token_repository),
) -> TokenResponse:
    """HU-04: el estudiante se autentica y autoriza a UNA universidad destino durante 24 horas."""
    student = authenticate_student(body, records, tokens)
    target = nodes.get_node(body.target_node_id)
    if target is None or target["status"] != ACTIVE_STATUS:
        raise HTTPException(status_code=404, detail="La universidad destino no existe o no está activa en la red.")
    issued = issue_token(student, target["node_id"], tokens)
    return TokenResponse(
        student_auth_token=issued["token"],
        jti=issued["jti"],
        audience=target["node_id"],
        origin=student["node_id"],
        expires_in=config.TOKEN_TTL_SECONDS,
        expires_at=_iso(issued["exp"]),
    )


@router.post("/tokens/list", response_model=TokenListResponse)
def list_tokens(
    body: StudentCredentials,
    records: RecordRepository = Depends(get_record_repository),
    nodes: NodeRepository = Depends(get_node_repository),
    tokens: TokenRepository = Depends(get_token_repository),
) -> TokenListResponse:
    """HU-05: los tokens del estudiante con su estado. Es POST para no poner la clave en la dirección."""
    authenticate_student(body, records, tokens)
    now = time.time()
    result = []
    for item in tokens.list_by_document(body.document_number):
        if item.get("revoked"):
            state = "REVOCADO"
        elif int(item["exp"]) <= now:
            state = "EXPIRADO"
        else:
            state = "ACTIVO"
        node = nodes.get_node(item["aud"])
        result.append(
            TokenInfo(
                jti=item["jti"],
                audience=item["aud"],
                audience_name=node["name"] if node else None,
                issued_at=_iso(item["issued_at"]),
                expires_at=_iso(item["exp"]),
                status=state,
            )
        )
    return TokenListResponse(tokens=result)


@router.post("/tokens/{jti}/revoke", response_model=RevokeResponse)
def revoke_token(
    jti: str,
    body: StudentCredentials,
    records: RecordRepository = Depends(get_record_repository),
    tokens: TokenRepository = Depends(get_token_repository),
) -> RevokeResponse:
    """HU-05: revoca el consentimiento. El jti queda en la lista negra y el token deja de servir al instante."""
    authenticate_student(body, records, tokens)
    item = tokens.get(jti) if re.fullmatch(JTI_PATTERN, jti) else None
    if item is None or item["document_number"] != body.document_number:
        raise HTTPException(status_code=404, detail="Token no encontrado.")  # igual si es de otra persona
    tokens.revoke(jti)  # idempotente
    return RevokeResponse(jti=jti, status="REVOCADO", message="Consentimiento revocado. Ese token ya no abre el historial.")
