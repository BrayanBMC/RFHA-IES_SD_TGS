"""Configuración leída de variables de entorno (ver .env.example)."""
import os
from pathlib import Path


def load_dotenv() -> None:
    """Lee .env de la raíz del repo si existe (solo desarrollo local). No pisa variables ya definidas."""
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_dotenv()

REPOSITORY_BACKEND = os.getenv("REPOSITORY_BACKEND", "memory")  # memory | dynamodb
NODES_TABLE = os.getenv("NODES_TABLE", "NodesTable")
