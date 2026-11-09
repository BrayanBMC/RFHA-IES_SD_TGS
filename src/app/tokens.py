"""student_auth_token (JWT HS256, 24 h) y su verificación contra la lista negra.

Claims: sub = student_id, doc = cédula, origin = nodo del historial, aud = nodo destino (a quien se autoriza),
jti = identificador único (permite revocar), iat, exp.
"""
import time
import uuid

import jwt

from src.app import config
from src.app.repositories import TokenRepository

ALGORITHM = "HS256"


class TokenError(Exception):
    """El token no es válido. `reason` es un texto corto para mostrar o registrar."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def issue_token(student: dict, target_node_id: str, tokens: TokenRepository, now: int | None = None) -> dict:
    """Crea el JWT y deja el registro en TokensTable (para listarlo y revocarlo)."""
    issued = int(now if now is not None else time.time())
    expires = issued + config.TOKEN_TTL_SECONDS
    jti = uuid.uuid4().hex
    claims = {
        "sub": student["student_id"],
        "doc": student["document_number"],
        "origin": student["node_id"],
        "aud": target_node_id,
        "jti": jti,
        "iat": issued,
        "exp": expires,
    }
    token = jwt.encode(claims, config.JWT_SECRET, algorithm=ALGORITHM)
    tokens.put(
        {
            "jti": jti,
            "document_number": student["document_number"],
            "student_id": student["student_id"],
            "origin": student["node_id"],
            "aud": target_node_id,
            "issued_at": issued,
            "exp": expires,
            "ttl": expires,
            "revoked": False,
        }
    )
    return {"token": token, "jti": jti, "exp": expires}


def verify_token(token: str, audience: str, tokens: TokenRepository) -> dict:
    """Valida firma, vigencia, destino y lista negra. Devuelve los claims o lanza TokenError."""
    try:
        claims = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[ALGORITHM],
            audience=audience,
            options={"require": ["exp", "aud", "jti", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("El token expiró.")
    except jwt.InvalidAudienceError:
        raise TokenError("El token no fue emitido para esta universidad.")
    except jwt.PyJWTError:
        raise TokenError("El token es inválido.")
    stored = tokens.get(claims["jti"])
    if stored is None or stored.get("revoked"):
        raise TokenError("El token fue revocado por el estudiante o no está registrado.")
    return claims
