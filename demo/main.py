"""Demo del middleware RFHA-IES (HU-06 y HU-07, versión mínima).

Autónoma: no importa nada de src/app. Corre con uvicorn (local) o en AWS Lambda (Mangum).
"""
import os
import time
from pathlib import Path

import jwt
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
from pydantic import BaseModel, Field


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

# Modo demostración: habilita los botones que simulan el consentimiento del estudiante.
# Apagado por defecto. En AWS solo se activa si se despliega con DemoMode=1.
DEMO_MODE = os.getenv("DEMO_MODE") == "1"

STATIC_DIR = Path(__file__).resolve().parent / "static"
PAGE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

app = FastAPI(
    title="Middleware RFHA-IES - Demo Web Services",
    description="API Gateway + Lambda: consulta federada de historiales académicos (demo).",
)

# Repositorio simulado en memoria (representa DynamoDB de cada universidad). Datos ficticios.
try:
    from .students import STUDENTS  # al correr como paquete: demo.main
except ImportError:  # en AWS Lambda el módulo se llama "main" y está en la raíz del paquete
    from students import STUDENTS

MOCK_DYNAMODB_NODES = STUDENTS


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


@app.get("/api/v1/demo/students")
async def demo_students():
    """Lista de estudiantes de ejemplo para el selector de la interfaz. Solo en modo demostración."""
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="No disponible.")
    return [
        {
            "student_id": s["student_id"],
            "full_name": s["full_name"],
            "university": s["university"],
            "academic_status": s["academic_status"],
        }
        for s in MOCK_DYNAMODB_NODES.values()
    ]


class ConsentTokenRequest(BaseModel):
    student_id: str = Field(pattern=r"^[0-9A-Za-z_-]{1,32}$")
    expired: bool = False


@app.get("/api/v1/demo/config")
async def demo_config():
    """Le dice a la interfaz si debe mostrar las herramientas de demostración."""
    return {"demo_mode": DEMO_MODE}


@app.post("/api/v1/demo/consent-token")
async def demo_consent_token(body: ConsentTokenRequest):
    """Simula el paso en que el estudiante autoriza la consulta (en el proyecto final será HU-04)."""
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="No disponible.")
    now = int(time.time())
    exp = now - 3600 if body.expired else now + 86400
    token = jwt.encode(
        {"student_id": body.student_id, "iat": now, "exp": exp},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"token": token, "expires_at": exp}


# Interfaz web (HTML/CSS/JS estáticos, sin build).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(STATIC_DIR / "index.html", headers=PAGE_HEADERS)


# Punto de entrada para AWS Lambda.
handler = Mangum(app, lifespan="off")
