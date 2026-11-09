from fastapi.testclient import TestClient

from src.app.main import app
from src.app.repositories import (
    get_node_repository,
    get_record_repository,
    get_replica_repository,
    get_token_repository,
)
from tests.conftest import ADMIN, NODE, STUDENT

client = TestClient(app)


def test_failover_a_replica_cuando_primario_no_responde(stores):
    api = client
    # 1. Registrar y aprobar nodo origen
    origin_id = api.post("/api/v1/nodes/register", json=NODE).json()["node_id"]
    origin_key = api.post(f"/api/v1/admin/nodes/{origin_id}/approve", headers=ADMIN).json()["api_key"]

    # 2. Registrar y aprobar nodo consultante
    other_node = {"nit": "860007386", "name": "Universidad Javeriana", "domain": "javeriana.edu.co", "contact_email": "reg@javeriana.edu.co"}
    other_id = api.post("/api/v1/nodes/register", json=other_node).json()["node_id"]
    other_key = api.post(f"/api/v1/admin/nodes/{other_id}/approve", headers=ADMIN).json()["api_key"]

    # 3. Sincronizar historial (se guarda en primario y en réplica)
    record_payload = {
        "records": [
            {
                **STUDENT,
                "password": "Password123",
                "courses": [{"code": "MAT-101", "name": "Cálculo", "credits": 4, "grade": 4.5, "semester": "2025-1"}],
            }
        ]
    }
    sync_res = api.post("/api/v1/node/sync-records", headers={"X-Node-API-Key": origin_key}, json=record_payload)
    assert sync_res.status_code == 200

    # 4. Estudiante genera token hacia nodo consultante
    token_res = api.post(
        "/api/v1/student/auth-token",
        json={"document_number": STUDENT["document_number"], "password": "Password123", "target_node_id": other_id},
    )
    token = token_res.json()["student_auth_token"]

    # 5. Consulta normal (debe venir de Primary)
    res_primary = api.get(
        f"/api/v1/federated/academic-history/{STUDENT['student_id']}",
        headers={"X-Node-API-Key": other_key, "X-Student-Consent-Token": token},
    )
    assert res_primary.status_code == 200
    assert res_primary.headers["x-data-source"] == "Primary"
    assert res_primary.json()["data_source"] == "Primary"

    # 6. Simular caída del nodo origen con cabecera X-Simulate-Down
    res_failover = api.get(
        f"/api/v1/federated/academic-history/{STUDENT['student_id']}",
        headers={"X-Node-API-Key": other_key, "X-Student-Consent-Token": token, "X-Simulate-Down": "true"},
    )
    assert res_failover.status_code == 200
    assert res_failover.headers["x-data-source"] == "Replica"
    assert res_failover.json()["data_source"] == "Replica"
    assert res_failover.json()["data"]["student_id"] == STUDENT["student_id"]


def test_falla_si_primario_y_replica_no_tienen_el_historial(stores):
    api = client
    # Nodo y token válidos
    node_id = api.post("/api/v1/nodes/register", json={"nit": "890900608", "name": "UdeA", "domain": "udea.edu.co", "contact_email": "c@udea.edu.co"}).json()["node_id"]
    api_key = api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN).json()["api_key"]

    # Cargar y luego vaciar ambos
    sync_res = api.post(
        "/api/v1/node/sync-records",
        headers={"X-Node-API-Key": api_key},
        json={"records": [{**STUDENT, "student_id": "999999", "document_number": "999999", "password": "Pw123456", "courses": []}]},
    )
    token = api.post("/api/v1/student/auth-token", json={"document_number": "999999", "password": "Pw123456", "target_node_id": node_id}).json()["student_auth_token"]

    # Limpiar primario y réplica
    stores.records._items.clear()
    stores.replicas._items.clear()

    res = api.get(
        "/api/v1/federated/academic-history/999999",
        headers={"X-Node-API-Key": api_key, "X-Student-Consent-Token": token},
    )
    assert res.status_code == 404
