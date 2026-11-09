from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from src.app.models import SyncRequest, SyncResponse
from src.app.repositories import RecordRepository, get_record_repository, record_key
from src.app.security import hash_password, record_signature, require_node

router = APIRouter(prefix="/api/v1/node", tags=["Nodo IES"])


def _course_status(grade: float | None) -> str:
    if grade is None:
        return "EN_CURSO"
    return "APROBADA" if grade >= 3.0 else "REPROBADA"


@router.post("/sync-records", response_model=SyncResponse)
def sync_records(
    body: SyncRequest,
    node: dict = Depends(require_node),
    records: RecordRepository = Depends(get_record_repository),
) -> SyncResponse:
    """HU-03: el nodo carga o actualiza historiales (hasta 100 estudiantes por petición).

    El nodo dueño sale de la API Key, no del cuerpo: un nodo nunca puede escribir datos de otro.
    Si el estudiante ya existe se reemplaza (upsert por nodo + student_id).
    """
    created = updated = 0
    for student in body.records:
        existing = records.get(node["node_id"], student.student_id)
        password_hash = hash_password(student.password) if student.password else (existing or {}).get("password_hash")
        data = {
            "node_id": node["node_id"],
            "student_id": student.student_id,
            "document_number": student.document_number,
            "full_name": student.full_name,
            "program": student.program,
            "academic_status": student.academic_status,
            "courses": [
                {**c.model_dump(), "status": _course_status(c.grade)} for c in student.courses
            ],
        }
        records.upsert(
            {
                "record_key": record_key(node["node_id"], student.student_id),
                **data,
                "password_hash": password_hash,
                "digital_signature_hash": record_signature(data),
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if existing:
            updated += 1
        else:
            created += 1
    return SyncResponse(node_id=node["node_id"], received=len(body.records), created=created, updated=updated)
