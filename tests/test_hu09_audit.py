from fastapi.testclient import TestClient

from src.app.main import app
from tests.conftest import ADMIN, NODE, STUDENT

client = TestClient(app)


def test_bitacora_exige_autenticacion():
    res = client.get("/api/v1/audit/logs")
    assert res.status_code == 403


def test_bitacora_registra_consultas_exitosas_y_rechazadas(stores):
    api = client
    # 1. Crear nodos y estudiante
    origin_id = api.post("/api/v1/nodes/register", json=NODE).json()["node_id"]
    origin_key = api.post(f"/api/v1/admin/nodes/{origin_id}/approve", headers=ADMIN).json()["api_key"]

    api.post(
        "/api/v1/node/sync-records",
        headers={"X-Node-API-Key": origin_key},
        json={"records": [{**STUDENT, "password": "Password123", "courses": []}]},
    )
    token = api.post(
        "/api/v1/student/auth-token",
        json={"document_number": STUDENT["document_number"], "password": "Password123", "target_node_id": origin_id},
    ).json()["student_auth_token"]

    # 2. Intento rechazado: sin token
    api.get(f"/api/v1/federated/academic-history/{STUDENT['student_id']}", headers={"X-Node-API-Key": origin_key})

    # 3. Intento exitoso: con token
    api.get(
        f"/api/v1/federated/academic-history/{STUDENT['student_id']}",
        headers={"X-Node-API-Key": origin_key, "X-Student-Consent-Token": token},
    )

    # 4. Administrador consulta bitácora completa
    logs_res = api.get("/api/v1/audit/logs", headers=ADMIN)
    assert logs_res.status_code == 200
    logs = logs_res.json()["logs"]
    assert len(logs) >= 2

    outcomes = [l["outcome"] for l in logs]
    assert "DENIED" in outcomes
    assert "SUCCESS" in outcomes

    # 5. Universidad consulta su bitácora mediante X-Node-API-Key
    node_logs_res = api.get("/api/v1/audit/logs", headers={"X-Node-API-Key": origin_key})
    assert node_logs_res.status_code == 200
    assert len(node_logs_res.json()["logs"]) >= 2
