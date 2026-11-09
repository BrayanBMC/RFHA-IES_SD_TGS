"""Repositorios: una interfaz mínima por tabla, cada una con dos implementaciones (memoria y DynamoDB).

- NodesTable   (HU-01, HU-02): nodos institucionales y el hash de su API Key.
- RecordsTable (HU-03): historiales sincronizados por los nodos.
- TokensTable  (HU-04, HU-05): tokens emitidos al estudiante; `revoked` = lista negra.
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from typing import Protocol

from src.app import config
from src.app.models import PENDING_STATUS


class DuplicateNitError(Exception):
    """Ya existe un nodo registrado con ese NIT."""


# ---------------------------------------------------------------- utilidades


def _new_node(data: dict) -> dict:
    return {
        "node_id": "IES-" + uuid.uuid4().hex[:8].upper(),
        "status": PENDING_STATUS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }


def _to_dynamo(item: dict) -> dict:
    """DynamoDB no acepta float: se convierten a Decimal."""
    return json.loads(json.dumps(item), parse_float=Decimal)


def _scan_all(table, **kwargs) -> list[dict]:
    """Scan con paginación. Los catálogos de este proyecto son pequeños, así que no se crean índices."""
    items: list[dict] = []
    response = table.scan(**kwargs)
    items += response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"], **kwargs)
        items += response.get("Items", [])
    return items


def _dynamo_table(name: str):
    import boto3

    return boto3.resource("dynamodb").Table(name)


# ---------------------------------------------------------------- nodos


class NodeRepository(Protocol):
    def create_node(self, data: dict) -> dict: ...

    def get_node(self, node_id: str) -> dict | None: ...

    def list_nodes(self, status: str | None = None) -> list[dict]: ...

    def update_node(self, node_id: str, fields: dict) -> dict: ...

    def find_by_api_key_hash(self, api_key_hash: str) -> dict | None: ...


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

    def list_nodes(self, status: str | None = None) -> list[dict]:
        nodes = [n for n in self._nodes.values() if status is None or n["status"] == status]
        return sorted(nodes, key=lambda n: n["created_at"])

    def update_node(self, node_id: str, fields: dict) -> dict:
        self._nodes[node_id].update(fields)
        return self._nodes[node_id]

    def find_by_api_key_hash(self, api_key_hash: str) -> dict | None:
        return next((n for n in self._nodes.values() if n.get("api_key_hash") == api_key_hash), None)


class DynamoNodeRepository:
    """Tabla NodesTable con clave de partición `node_id`."""

    def __init__(self, table_name: str) -> None:
        self._table = _dynamo_table(table_name)

    def create_node(self, data: dict) -> dict:
        from boto3.dynamodb.conditions import Attr

        if _scan_all(self._table, FilterExpression=Attr("nit").eq(data["nit"])):
            raise DuplicateNitError(data["nit"])
        node = _new_node(data)
        self._table.put_item(Item=node, ConditionExpression="attribute_not_exists(node_id)")
        return node

    def get_node(self, node_id: str) -> dict | None:
        return self._table.get_item(Key={"node_id": node_id}).get("Item")

    def list_nodes(self, status: str | None = None) -> list[dict]:
        from boto3.dynamodb.conditions import Attr

        kwargs = {"FilterExpression": Attr("status").eq(status)} if status else {}
        return sorted(_scan_all(self._table, **kwargs), key=lambda n: n["created_at"])

    def update_node(self, node_id: str, fields: dict) -> dict:
        names = {f"#{k}": k for k in fields}
        values = {f":{k}": v for k, v in fields.items()}
        expression = "SET " + ", ".join(f"#{k} = :{k}" for k in fields)
        response = self._table.update_item(
            Key={"node_id": node_id},
            UpdateExpression=expression,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ConditionExpression="attribute_exists(node_id)",
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]

    def find_by_api_key_hash(self, api_key_hash: str) -> dict | None:
        from boto3.dynamodb.conditions import Attr

        found = _scan_all(self._table, FilterExpression=Attr("api_key_hash").eq(api_key_hash))
        return found[0] if found else None


@lru_cache(maxsize=1)
def get_node_repository() -> NodeRepository:
    if config.REPOSITORY_BACKEND == "dynamodb":
        return DynamoNodeRepository(config.NODES_TABLE)
    return InMemoryNodeRepository()


# ---------------------------------------------------------------- historiales (HU-03)


def record_key(node_id: str, student_id: str) -> str:
    return f"{node_id}#{student_id}"


class RecordRepository(Protocol):
    def get(self, node_id: str, student_id: str) -> dict | None: ...

    def upsert(self, item: dict) -> None: ...

    def find_by_document(self, document_number: str) -> list[dict]: ...


class InMemoryRecordRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def get(self, node_id: str, student_id: str) -> dict | None:
        return self._items.get(record_key(node_id, student_id))

    def upsert(self, item: dict) -> None:
        self._items[item["record_key"]] = item

    def find_by_document(self, document_number: str) -> list[dict]:
        return [i for i in self._items.values() if i["document_number"] == document_number]


class DynamoRecordRepository:
    """Tabla RecordsTable con clave `record_key` = `<node_id>#<student_id>` (upsert por clave, B12)."""

    def __init__(self, table_name: str) -> None:
        self._table = _dynamo_table(table_name)

    def get(self, node_id: str, student_id: str) -> dict | None:
        return self._table.get_item(Key={"record_key": record_key(node_id, student_id)}).get("Item")

    def upsert(self, item: dict) -> None:
        self._table.put_item(Item=_to_dynamo(item))

    def find_by_document(self, document_number: str) -> list[dict]:
        from boto3.dynamodb.conditions import Attr

        return _scan_all(self._table, FilterExpression=Attr("document_number").eq(document_number))


@lru_cache(maxsize=1)
def get_record_repository() -> RecordRepository:
    if config.REPOSITORY_BACKEND == "dynamodb":
        return DynamoRecordRepository(config.RECORDS_TABLE)
    return InMemoryRecordRepository()


# ---------------------------------------------------------------- tokens y lista negra (HU-04, HU-05)


class TokenRepository(Protocol):
    def put(self, item: dict) -> None: ...

    def get(self, jti: str) -> dict | None: ...

    def list_by_document(self, document_number: str) -> list[dict]: ...

    def revoke(self, jti: str) -> None: ...


class InMemoryTokenRepository:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def put(self, item: dict) -> None:
        self._items[item["jti"]] = item

    def get(self, jti: str) -> dict | None:
        return self._items.get(jti)

    def list_by_document(self, document_number: str) -> list[dict]:
        found = [i for i in self._items.values() if i["document_number"] == document_number]
        return sorted(found, key=lambda i: i["issued_at"], reverse=True)

    def revoke(self, jti: str) -> None:
        self._items[jti]["revoked"] = True


class DynamoTokenRepository:
    """Tabla TokensTable con clave `jti`. El atributo `ttl` (= exp del token) hace que DynamoDB borre el registro al vencer."""

    def __init__(self, table_name: str) -> None:
        self._table = _dynamo_table(table_name)

    def put(self, item: dict) -> None:
        self._table.put_item(Item=_to_dynamo(item))

    def get(self, jti: str) -> dict | None:
        return self._table.get_item(Key={"jti": jti}).get("Item")

    def list_by_document(self, document_number: str) -> list[dict]:
        from boto3.dynamodb.conditions import Attr

        found = _scan_all(self._table, FilterExpression=Attr("document_number").eq(document_number))
        return sorted(found, key=lambda i: i["issued_at"], reverse=True)

    def revoke(self, jti: str) -> None:
        self._table.update_item(
            Key={"jti": jti},
            UpdateExpression="SET revoked = :t",
            ExpressionAttributeValues={":t": True},
            ConditionExpression="attribute_exists(jti)",
        )


@lru_cache(maxsize=1)
def get_token_repository() -> TokenRepository:
    if config.REPOSITORY_BACKEND == "dynamodb":
        return DynamoTokenRepository(config.TOKENS_TABLE)
    return InMemoryTokenRepository()
