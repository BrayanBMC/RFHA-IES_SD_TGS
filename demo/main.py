"""Demo del middleware RFHA-IES (HU-06 y HU-07, versión mínima).

Autónoma: no importa nada de src/app. Corre con uvicorn (local) o en AWS Lambda (Mangum).
"""
import os
from pathlib import Path

import jwt
from fastapi import FastAPI, Header, HTTPException
from mangum import Mangum


def _load_dotenv() -> None:
    """Lee ../.env si existe (solo para desarrollo local). No pisa variables ya definidas."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# Valor por defecto SOLO para desarrollo local. En AWS se define JWT_SECRET en la Lambda.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret-do-not-use-in-aws")

app = FastAPI(
    title="Middleware RFHA-IES - Demo Web Services",
    description="API Gateway + Lambda: consulta federada de historiales académicos (demo).",
)

# Repositorio simulado en memoria (representa DynamoDB).
MOCK_DYNAMODB_NODES = {
    "20262678029": {
        "student_id": "20262678029",
        "full_name": "Brayan Acosta Parrado",
        "university": "Universidad Distrital Francisco José de Caldas",
        "program": "Ingeniería en Telemática",
        "gpa": 4.52,
        "courses": [
            {"code": "165-301", "name": "Sistemas Distribuidos", "grade": 4.8},
            {"code": "165-302", "name": "Teoría General de Sistemas", "grade": 4.5},
        ],
    }
}


def verify_student_token(token: str | None, student_id: str) -> dict:
    """Valida firma, vencimiento y que el token pertenezca al estudiante consultado."""
    if not token:
        raise HTTPException(
            status_code=403,
            detail="ACCESO DENEGADO: falta el token de consentimiento del estudiante.",
        )
    try:
        # PyJWT valida la firma y 'exp'; 'require' exige que el token traiga 'exp'.
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=["HS256"], options={"require": ["exp"]}
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=403, detail="El token de consentimiento ha expirado."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=403,
            detail="ACCESO DENEGADO: token de consentimiento inválido.",
        )
    if payload.get("student_id") != student_id:
        raise HTTPException(
            status_code=403,
            detail="ACCESO DENEGADO: el token no autoriza a este estudiante.",
        )
    return payload


@app.get("/api/v1/federated/academic-history/{student_id}")
async def get_academic_history(
    student_id: str,
    x_student_consent_token: str | None = Header(
        default=None, alias="X-Student-Consent-Token"
    ),
):
    # 1. Validación en la capa middleware (antes de tocar los datos).
    verify_student_token(x_student_consent_token, student_id)

    # 2. Enrutamiento transparente: el cliente no sabe dónde está el dato.
    record = MOCK_DYNAMODB_NODES.get(student_id)
    if not record:
        raise HTTPException(
            status_code=404, detail="Estudiante no encontrado en la red federada."
        )

    return {
        "status": "SUCCESS",
        "middleware_layer": "AWS API Gateway + AWS Lambda",
        "transparency_verified": True,
        "data": record,
    }


# Punto de entrada para AWS Lambda.
handler = Mangum(app, lifespan="off")
