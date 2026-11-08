"""Genera tokens JWT de consentimiento para la demo.

Uso:
    python scripts/generate_token.py                  # estudiante 20262678029
    python scripts/generate_token.py 20262678029      # estudiante explícito

Usa JWT_SECRET del entorno o de .env. En AWS debe ser el mismo valor que tiene la Lambda.
"""
import os
import sys
import time
from pathlib import Path

import jwt

DEFAULT_STUDENT = "20262678029"
DEFAULT_SECRET = "dev-only-insecure-secret-do-not-use-in-aws"


def _load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def make_token(student_id: str = DEFAULT_STUDENT, expires_in: int = 86400) -> str:
    """expires_in en segundos; un valor negativo genera un token ya expirado."""
    _load_dotenv()
    secret = os.getenv("JWT_SECRET", DEFAULT_SECRET)
    now = int(time.time())
    payload = {"student_id": student_id, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, secret, algorithm="HS256")


if __name__ == "__main__":
    student = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STUDENT
    print("TOKEN VÁLIDO (24 h):")
    print(make_token(student))
    print()
    print("TOKEN EXPIRADO:")
    print(make_token(student, expires_in=-3600))
