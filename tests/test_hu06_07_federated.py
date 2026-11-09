import time

import boto3
from fastapi.testclient import TestClient
from moto import mock_aws

from src.app.main import app
from src.app.repositories import DynamoRecordRepository
from src.app.routers.federated import SIGNED_FIELDS, _plain
from src.app.security import record_signature
from src.app.tokens import issue_token
from tests.conftest import ADMIN, NODE, STUDENT


def url(student_id=STUDENT["student_id"]):
    return f"/api/v1/federated/academic-history/{student_id}"


def make_token(api, creds, target):
    return api.post("/api/v1/student/auth-token", json={**creds, "target_node_id": target}).json()


def query(api, api_key, token=None, student_id=STUDENT["student_id"]):
    headers = {"X-Node-API-Key": api_key}
    if token:
        headers["X-Student-Consent-Token"] = token
    return api.get(url(student_id), headers=headers)


# ---- HU-06: consulta federada ----


def test_consulta_autorizada_devuelve_el_historial(api, active_node, synced_student):
    node_id, api_key = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    response = query(api, api_key, token)
    assert response.status_code == 200
    assert response.headers["x-data-source"] == "Primary"
    body = response.json()
    assert body["data_source"] == "Primary"
    assert body["data"]["full_name"] == STUDENT["full_name"]
    assert body["data"]["node_id"] == node_id
    assert [c["status"] for c in body["data"]["courses"]] == ["APROBADA", "REPROBADA", "EN_CURSO"]
    assert "password" not in str(body) and "password_hash" not in str(body)


def test_promedio_y_creditos_se_calculan(api, active_node, synced_student):
    node_id, api_key = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    data = query(api, api_key, token).json()["data"]
    assert data["gpa"] == 3.65  # (4.8*3 + 2.5*3) / 6
    assert data["credits_completed"] == 3


def test_otra_universidad_consulta_un_historial_de_otro_nodo(api, active_node, synced_student):
    """La federación: el historial está en el nodo A y lo consulta el nodo B con un token dirigido a B."""
    origin, _ = active_node
    other = api.post("/api/v1/nodes/register", json={**NODE, "nit": "860007386", "name": "Universidad de los Andes"}).json()["node_id"]
    other_key = api.post(f"/api/v1/admin/nodes/{other}/approve", headers=ADMIN).json()["api_key"]
    token = make_token(api, synced_student[1], other)["student_auth_token"]
    response = query(api, other_key, token)
    assert response.status_code == 200
    assert response.json()["data"]["node_id"] == origin


def test_historial_inexistente_devuelve_404(api, stores, active_node, synced_student):
    node_id, api_key = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    stores.records._items.clear()
    stores.replicas._items.clear()
    assert query(api, api_key, token).status_code == 404


def test_historial_alterado_devuelve_500(api, stores, active_node, synced_student):
    node_id, api_key = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    stores.records.get(node_id, STUDENT["student_id"])["courses"][1]["grade"] = 5.0  # alguien cambia una nota
    response = query(api, api_key, token)
    assert response.status_code == 500
    assert "integridad" in response.json()["detail"]


# ---- HU-07: bloqueo de consultas no autorizadas ----


def test_sin_api_key_de_la_universidad_devuelve_403(api, active_node, synced_student):
    node_id, _ = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    assert api.get(url(), headers={"X-Student-Consent-Token": token}).status_code == 403
    assert query(api, "rfha_falsa", token).status_code == 403


def test_sin_token_devuelve_403(api, active_node, synced_student):
    assert query(api, active_node[1]).status_code == 403


def test_token_invalido_devuelve_403(api, active_node, synced_student):
    assert query(api, active_node[1], "esto-no-es-un-jwt").status_code == 403


def test_token_expirado_devuelve_403(api, stores, active_node, synced_student):
    node_id, api_key = active_node
    student = stores.records.get(node_id, STUDENT["student_id"])
    old = issue_token(student, node_id, stores.tokens, now=int(time.time()) - 2 * 86400)["token"]
    response = query(api, api_key, old)
    assert response.status_code == 403
    assert "expiró" in response.json()["detail"]


def test_token_revocado_devuelve_403(api, active_node, synced_student):
    node_id, api_key = active_node
    issued = make_token(api, synced_student[1], node_id)
    assert query(api, api_key, issued["student_auth_token"]).status_code == 200
    api.post(f"/api/v1/student/tokens/{issued['jti']}/revoke", json=synced_student[1])
    response = query(api, api_key, issued["student_auth_token"])
    assert response.status_code == 403
    assert "revocado" in response.json()["detail"]


def test_token_dirigido_a_otra_universidad_devuelve_403(api, active_node, synced_student):
    node_id, api_key = active_node
    other = api.post("/api/v1/nodes/register", json={**NODE, "nit": "860007386"}).json()["node_id"]
    api.post(f"/api/v1/admin/nodes/{other}/approve", headers=ADMIN)
    token_for_other = make_token(api, synced_student[1], other)["student_auth_token"]
    response = query(api, api_key, token_for_other)  # lo usa el nodo A, pero era para B
    assert response.status_code == 403
    assert "esta universidad" in response.json()["detail"]


def test_token_de_otro_estudiante_devuelve_403(api, active_node, synced_student):
    node_id, api_key = active_node
    token = make_token(api, synced_student[1], node_id)["student_auth_token"]
    assert query(api, api_key, token, student_id="20251234501").status_code == 403


# ---- DynamoDB: los Decimal no rompen la firma ----


@mock_aws
def test_la_firma_sobrevive_al_viaje_por_dynamodb(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("dynamodb").create_table(
        TableName="RecordsTable",
        KeySchema=[{"AttributeName": "record_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "record_key", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    signed = {
        "node_id": "IES-AAAAAAAA", "student_id": "1", "document_number": "123456", "full_name": "Ana Prueba",
        "program": "Programa", "academic_status": "ACTIVO",
        "courses": [
            {"code": "A", "name": "A", "credits": 3, "grade": 4.0, "semester": "2026-1", "status": "APROBADA"},
            {"code": "B", "name": "B", "credits": 2, "grade": None, "semester": "2026-2", "status": "EN_CURSO"},
        ],
    }
    repo = DynamoRecordRepository("RecordsTable")
    repo.upsert({"record_key": "IES-AAAAAAAA#1", **signed, "digital_signature_hash": record_signature(signed)})
    back = _plain(repo.get("IES-AAAAAAAA", "1"))
    assert record_signature({k: back[k] for k in SIGNED_FIELDS}) == back["digital_signature_hash"]


# ---- Pantalla ----


def test_la_pantalla_de_consulta_se_sirve_y_llama_a_la_api():
    client = TestClient(app)
    page = client.get("/consulta")
    assert page.status_code == 200 and 'lang="es"' in page.text
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert "<script>" not in page.text and " style=" not in page.text
    for field in ("api-key", "student-id", "token"):
        assert f'for="{field}"' in page.text
    js = client.get("/static/consulta.js").text
    assert "/api/v1/federated/academic-history/" in js and "X-Student-Consent-Token" in js
    assert "innerHTML" not in js and "localStorage" not in js
    assert 'href="/consulta"' in client.get("/").text
