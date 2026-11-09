import json

import boto3
import pytest
from moto import mock_aws

from src.app.repositories import DynamoNodeRepository
from src.app.security import hash_api_key
from tests.conftest import ADMIN, NODE


def test_listar_sin_clave_de_administrador_devuelve_403(api):
    assert api.get("/api/v1/admin/nodes").status_code == 403


def test_clave_de_administrador_incorrecta_devuelve_403(api, pending_node):
    wrong = {"X-Admin-Key": "otra-clave"}
    assert api.get("/api/v1/admin/nodes", headers=wrong).status_code == 403
    assert api.post(f"/api/v1/admin/nodes/{pending_node}/approve", headers=wrong).status_code == 403


def test_sin_clave_configurada_en_el_servidor_nadie_entra(api, monkeypatch):
    from src.app import config

    monkeypatch.setattr(config, "ADMIN_KEY", "")
    assert api.get("/api/v1/admin/nodes", headers={"X-Admin-Key": ""}).status_code == 403
    assert api.get("/api/v1/admin/nodes").status_code == 403


def test_el_administrador_ve_las_solicitudes_pendientes_sin_datos_secretos(api, pending_node):
    response = api.get("/api/v1/admin/nodes?status=PENDIENTE_APROBACION", headers=ADMIN)
    assert response.status_code == 200
    nodes = response.json()["nodes"]
    assert [n["node_id"] for n in nodes] == [pending_node]
    assert nodes[0]["nit"] == NODE["nit"]
    assert "api_key_hash" not in nodes[0]


def test_aprobar_activa_el_nodo_y_entrega_la_api_key(api, stores, pending_node):
    response = api.post(f"/api/v1/admin/nodes/{pending_node}/approve", headers=ADMIN)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ACTIVO"
    assert body["api_key"].startswith("rfha_")
    assert stores.nodes.get_node(pending_node)["status"] == "ACTIVO"


def test_en_la_base_solo_se_guarda_el_hash_sha256_de_la_api_key(api, stores, pending_node):
    api_key = api.post(f"/api/v1/admin/nodes/{pending_node}/approve", headers=ADMIN).json()["api_key"]
    stored = stores.nodes.get_node(pending_node)
    assert stored["api_key_hash"] == hash_api_key(api_key)
    assert len(stored["api_key_hash"]) == 64
    assert api_key not in json.dumps(stored)


def test_cada_aprobacion_emite_una_clave_distinta(api):
    keys = set()
    for nit in ("899999063-3", "860007386", "860007373-4"):
        node_id = api.post("/api/v1/nodes/register", json={**NODE, "nit": nit}).json()["node_id"]
        keys.add(api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN).json()["api_key"])
    assert len(keys) == 3


def test_aprobar_dos_veces_devuelve_409_y_no_cambia_la_clave(api, stores, active_node):
    node_id, _ = active_node
    before = stores.nodes.get_node(node_id)["api_key_hash"]
    assert api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN).status_code == 409
    assert stores.nodes.get_node(node_id)["api_key_hash"] == before


@pytest.mark.parametrize("node_id", ["IES-00000000", "no-es-un-codigo", "IES-ZZZZZZZZ"])
def test_aprobar_un_nodo_inexistente_devuelve_404(api, node_id):
    assert api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN).status_code == 404


def test_los_nodos_aprobados_salen_de_la_lista_de_pendientes(api, active_node):
    pending = api.get("/api/v1/admin/nodes?status=PENDIENTE_APROBACION", headers=ADMIN).json()["nodes"]
    active = api.get("/api/v1/admin/nodes?status=ACTIVO", headers=ADMIN).json()["nodes"]
    assert pending == []
    assert [n["node_id"] for n in active] == [active_node[0]]


def test_nodos_activos_publicos_solo_muestran_codigo_y_nombre(api, active_node):
    other = {**NODE, "nit": "860007386", "name": "Pontificia Universidad Javeriana", "domain": "javeriana.edu.co"}
    api.post("/api/v1/nodes/register", json=other)  # queda pendiente: no debe aparecer
    response = api.get("/api/v1/nodes/active")
    assert response.status_code == 200
    assert response.json() == {"nodes": [{"node_id": active_node[0], "name": NODE["name"]}]}


@mock_aws
def test_repositorio_dynamodb_actualiza_y_busca_por_hash(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("dynamodb").create_table(
        TableName="NodesTable",
        KeySchema=[{"AttributeName": "node_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "node_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repo = DynamoNodeRepository("NodesTable")
    node = repo.create_node(dict(NODE))
    assert [n["node_id"] for n in repo.list_nodes("PENDIENTE_APROBACION")] == [node["node_id"]]
    repo.update_node(node["node_id"], {"status": "ACTIVO", "api_key_hash": "abc123"})
    assert repo.get_node(node["node_id"])["status"] == "ACTIVO"
    assert repo.find_by_api_key_hash("abc123")["node_id"] == node["node_id"]
    assert repo.find_by_api_key_hash("otro") is None
    assert repo.list_nodes("PENDIENTE_APROBACION") == []
