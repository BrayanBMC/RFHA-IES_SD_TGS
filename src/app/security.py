"""Seguridad: claves de API (SHA-256), claves de estudiante (PBKDF2), firma de historiales y control de acceso."""
import hashlib
import hmac
import json
import secrets

from fastapi import Depends, Header, HTTPException

from src.app import config
from src.app.models import ACTIVE_STATUS
from src.app.repositories import NodeRepository, get_node_repository

PBKDF2_ITERATIONS = 200_000
API_KEY_PREFIX = "rfha_"


# ---- API Key del nodo (HU-02): solo se guarda el hash SHA-256 ----

def new_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


# ---- Clave del estudiante (HU-03/04): PBKDF2 de la biblioteca estándar, con sal ----

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """Siempre hace el cálculo, incluso sin clave guardada, para que el tiempo de respuesta no delate si la cédula existe."""
    if not stored:
        stored = DUMMY_HASH
        valid_format = False
    else:
        valid_format = True
    try:
        _, iterations, salt, expected = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), expected) and valid_format


DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---- Firma del historial (HU-03, B6): SHA-256 del JSON canónico ----

def record_signature(record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---- Control de acceso ----

def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """HU-02: el administrador general envía X-Admin-Key. Sin clave configurada en el servidor, nadie entra."""
    expected = config.ADMIN_KEY
    if not expected or not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=403, detail="Se requiere la clave del administrador (X-Admin-Key).")


def require_node(
    x_node_api_key: str | None = Header(default=None),
    nodes: NodeRepository = Depends(get_node_repository),
) -> dict:
    """HU-03: un nodo activo se identifica con X-Node-API-Key. Devuelve el nodo autenticado."""
    node = nodes.find_by_api_key_hash(hash_api_key(x_node_api_key)) if x_node_api_key else None
    if not node or node.get("status") != ACTIVE_STATUS:
        raise HTTPException(status_code=403, detail="API Key de nodo ausente, inválida o nodo inactivo (X-Node-API-Key).")
    return node
