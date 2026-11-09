from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from src.app.repositories import RecordRepository, TokenRepository, get_record_repository, get_token_repository
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
    graded = [c for c in courses if c["grade"] is not None]
    credits = sum(c["credits"] for c in graded)
    gpa = round(sum(c["grade"] * c["credits"] for c in graded) / credits, 2) if credits else None
    approved = {c["code"]: c["credits"] for c in courses if c["status"] == "APROBADA"}
    return {"gpa": gpa, "credits_completed": sum(approved.values())}


@router.get("/academic-history/{student_id}")
def academic_history(
    student_id: str,
    response: Response,
    consulting_node: dict = Depends(require_node),
    x_student_consent_token: str | None = Header(default=None),
    records: RecordRepository = Depends(get_record_repository),
    tokens: TokenRepository = Depends(get_token_repository),
) -> dict:
    """HU-06 y HU-07: consulta del historial por una universidad activa con el permiso del estudiante.

    Controles en orden (el primero que falla corta con 403; el expediente solo se busca al final):
      1. API Key de la universidad que consulta (X-Node-API-Key).
      2. Token presente, con firma y vigencia válidas.
      3. Token dirigido a ESTA universidad (aud) y no revocado (lista negra).
      4. Token del mismo estudiante que la URL.
      5. El expediente existe (404) y su firma SHA-256 coincide (integridad).
    """
    if not x_student_consent_token:
        raise HTTPException(status_code=403, detail="Falta el token de consentimiento del estudiante (X-Student-Consent-Token).")
    try:
        claims = verify_token(x_student_consent_token, consulting_node["node_id"], tokens)
    except TokenError as error:
        raise HTTPException(status_code=403, detail=error.reason)
    if claims["sub"] != student_id:
        raise HTTPException(status_code=403, detail="El token no pertenece a este estudiante.")

    item = records.get(claims["origin"], student_id)
    if item is None:
        raise HTTPException(status_code=404, detail="No existe un historial para ese estudiante.")
    record = _plain(item)
    signed = {k: record[k] for k in SIGNED_FIELDS}
    if record_signature(signed) != record.get("digital_signature_hash"):
        raise HTTPException(status_code=500, detail="La integridad del historial no se pudo verificar.")

    response.headers["X-Data-Source"] = "Primary"
    return {
        "data_source": "Primary",
        "data": {
            **{k: signed[k] for k in ("student_id", "full_name", "program", "academic_status", "node_id", "courses")},
            **_summary(signed["courses"]),
        },
        "digital_signature_hash": record["digital_signature_hash"],
    }
