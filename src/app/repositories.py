"""Repositorio de nodos: una interfaz mínima con dos implementaciones (memoria y DynamoDB)."""
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Protocol

from src.app import config
from src.app.models import PENDING_STATUS


class DuplicateNitError(Exception):
    """Ya existe un nodo registrado con ese NIT."""


class NodeRepository(Protocol):
    def create_node(self, data: dict) -> dict: ...

    def get_node(self, node_id: str) -> dict | None: ...


def _new_node(data: dict) -> dict:
    return {
        "node_id": "IES-" + uuid.uuid4().hex[:8].upper(),
        "status": PENDING_STATUS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }


class InMemoryNodeRepository:
    def __init__(self) -> None:
        self._nodes: dict[str, dict] = {}

    def create_node(self, data: dict) -> dict:
        if any(n["nit"] == data["nit"] for n in self._nodes.values()):
            raise DuplicateNitError(data["nit"])
        node = _new_node(data)
        self._nodes[node["node_id"]] = node
        return node

    def get_node(self, node_id: str) -> dict | None:
        return self._nodes.get(node_id)


class DynamoNodeRepository:
    """Tabla NodesTable con clave de partición `node_id`. El catálogo es pequeño, por eso el NIT se busca con Scan."""

    def __init__(self, table_name: str) -> None:
        import boto3

        self._table = boto3.resource("dynamodb").Table(table_name)

    def create_node(self, data: dict) -> dict:
        from boto3.dynamodb.conditions import Attr

        found = self._table.scan(FilterExpression=Attr("nit").eq(data["nit"]), Limit=1000)
        if found.get("Items"):
            raise DuplicateNitError(data["nit"])
        node = _new_node(data)
        self._table.put_item(Item=node, ConditionExpression="attribute_not_exists(node_id)")
        return node

    def get_node(self, node_id: str) -> dict | None:
        return self._table.get_item(Key={"node_id": node_id}).get("Item")


@lru_cache(maxsize=1)
def get_node_repository() -> NodeRepository:
    if config.REPOSITORY_BACKEND == "dynamodb":
        return DynamoNodeRepository(config.NODES_TABLE)
    return InMemoryNodeRepository()
