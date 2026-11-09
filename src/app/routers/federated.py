import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from src.app import config
from src.app.repositories import (
    AuditRepository,
    RecordRepository,
    TokenRepository,
    get_audit_repository,
    get_record_repository,
    get_replica_repository,
    get_token_repository,
)
from src.app.security import record_signature, require_node
from src.app.tokens import TokenError, verify_token

router = APIRouter(prefix="/api/v1/federated", tags=["Consulta federada"])

SIGNED_FIELDS = ("node_id", "student_id", "document_number", "full_name", "program", "academic_status", "courses")


def _plain(value):
    """DynamoDB devuelve Decimal; se vuelve a int/float para recalcular la firma y responder JSON."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() and value.as_tuple().exponent >= 0 else float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _summary(courses: list[dict]) -> dict:
    graded = [c for c in courses if c.get("grade") is not None]
    credits = sum(c["credits"] for c in graded)
    gpa = round(sum(c["grade"] * c["credits"] for c in graded) / credits, 2) if credits else None
    approved = {c["code"]: c["credits"] for c in courses if c.get("status") == "APROBADA"}
    return {"gpa": gpa, "credits_completed": sum(approved.values())}


@router.get("/academic-history/{student_id}")
def academic_history(
    student_id: str,
    response: Response,
    request: Request,
    consulting_node: dict = Depends(require_node),
    x_student_consent_token: str | None = Header(default=None),
    x_simulate_down: bool = Header(default=False),
    records: RecordRepository = Depends(get_record_repository),
    replicas: RecordRepository = Depends(get_replica_repository),
    tokens: TokenRepository = Depends(get_token_repository),
    audits: AuditRepository = Depends(get_audit_repository),
) -> dict:
    """HU-06 a HU-09: consulta federada con autorización, bloqueo, réplica y bitácora.

    Controles en orden:
      1. API Key de la universidad que consulta (X-Node-API-Key).
      2. Token presente, con firma y vigencia válidas (HS256).
      3. Destino aud = universidad que consulta y no revocado (lista negra).
      4. Token perteneciente al mismo estudiante (sub).
      5. Búsqueda con conmutación por error (HU-08): nodo origen o réplica autorizada (X-Data-Source).
      6. Integridad criptográfica verificada con digital_signature_hash.
      7. Registro inmutable en bitácora de auditoría (HU-09).
    """
    def _log(outcome: str, reason: str, data_source: str = "None", origin: str | None = None):
        client_ip = request.client.host if request.client else "unknown"
        audits.record_log({
            "log_id": f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "consulting_node_id": consulting_node["node_id"],
            "target_student_id": student_id,
            "origin_node_id": origin,
            "outcome": outcome,
            "reason": reason,
            "data_source": data_source,
            "client_ip": client_ip,
        })

    if not x_student_consent_token:
        _log("DENIED", "Falta el token de consentimiento del estudiante")
        raise HTTPException(status_code=403, detail="Falta el token de consentimiento del estudiante (X-Student-Consent-Token).")

    try:
        claims = verify_token(x_student_consent_token, consulting_node["node_id"], tokens)
    except TokenError as error:
        _log("DENIED", error.reason)
        raise HTTPException(status_code=403, detail=error.reason)

    if claims["sub"] != student_id:
        _log("DENIED", "El token no pertenece a este estudiante", origin=claims.get("origin"))
        raise HTTPException(status_code=403, detail="El token no pertenece a este estudiante.")

    origin_node = claims["origin"]
    item = None
    source = "Primary"

    # HU-08: Tolerancia a fallos y conmutación a réplica si el primario está caído (simulado o falla)
    node_down = x_simulate_down or (bool(config.SIMULATE_NODE_DOWN) and config.SIMULATE_NODE_DOWN == origin_node)

    if not node_down:
        try:
            item = records.get(origin_node, student_id)
        except Exception:
            item = None

    if item is None:
        # Fallover a réplica autorizada
        replica_item = replicas.get(origin_node, student_id)
        if replica_item is not None:
            item = replica_item
            source = "Replica"

    if item is None:
        _log("ERROR", "No existe un historial para ese estudiante", origin=origin_node)
        raise HTTPException(status_code=404, detail="No existe un historial para ese estudiante.")

    record = _plain(item)
    signed = {k: record[k] for k in SIGNED_FIELDS}
    if record_signature(signed) != record.get("digital_signature_hash"):
        _log("ERROR", "Integridad del historial no verificable", data_source=source, origin=origin_node)
        raise HTTPException(status_code=500, detail="La integridad del historial no se pudo verificar.")

    _log("SUCCESS", f"Consulta exitosa ({source})", data_source=source, origin=origin_node)
    response.headers["X-Data-Source"] = source
    return {
        "data_source": source,
        "data": {
            **{k: signed[k] for k in ("student_id", "full_name", "program", "academic_status", "node_id", "courses")},
            **_summary(signed["courses"]),
        },
        "digital_signature_hash": record["digital_signature_hash"],
    }
