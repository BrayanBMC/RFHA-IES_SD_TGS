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
RECORDS_TABLE = os.getenv("RECORDS_TABLE", "RecordsTable")
REPLICAS_TABLE = os.getenv("REPLICAS_TABLE", "ReplicasTable")
TOKENS_TABLE = os.getenv("TOKENS_TABLE", "TokensTable")
AUDIT_TABLE = os.getenv("AUDIT_TABLE", "AuditLogsTable")

# Simular caída de un nodo para pruebas de failover (HU-08). Formato: node_id (ej. IES-1111AAAA)
SIMULATE_NODE_DOWN = os.getenv("SIMULATE_NODE_DOWN", "")

# Clave del administrador general (HU-02). Si está vacía, ninguna petición de administración es válida.
ADMIN_KEY = os.getenv("ADMIN_KEY", "")
# Secreto para firmar los tokens del estudiante (HU-04). El valor por defecto solo sirve en desarrollo local.
JWT_SECRET = os.getenv("JWT_SECRET", "secreto-solo-para-desarrollo-local-cambiar-0123456789")
TOKEN_TTL_SECONDS = 24 * 60 * 60  # 24 horas
