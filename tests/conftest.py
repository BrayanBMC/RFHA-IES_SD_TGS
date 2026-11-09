"""Fixtures compartidas por las pruebas de HU-02 en adelante (repositorios en memoria, sin tocar AWS)."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.app import config, security
from src.app.main import app
from src.app.repositories import (
    InMemoryNodeRepository,
    InMemoryRecordRepository,
    InMemoryTokenRepository,
    get_node_repository,
    get_record_repository,
    get_token_repository,
)

ADMIN_KEY = "clave-admin-de-pruebas"
ADMIN = {"X-Admin-Key": ADMIN_KEY}

NODE = {
    "nit": "899999063-3",
    "name": "Universidad Nacional de Colombia",
    "domain": "unal.edu.co",
    "contact_email": "admisiones@unal.edu.co",
}

STUDENT = {
    "student_id": "20262678029",
    "document_number": "1012345678",
    "full_name": "Brayan Acosta Parrado",
    "program": "Ingeniería en Telemática",
    "academic_status": "ACTIVO",
    "password": "Clave-2026-A",
    "courses": [
        {"code": "165-301", "name": "Sistemas Distribuidos", "credits": 3, "grade": 4.8, "semester": "2026-1"},
        {"code": "165-315", "name": "Bases de Datos", "credits": 3, "grade": 2.5, "semester": "2026-1"},
        {"code": "165-330", "name": "Seguridad Informática", "credits": 3, "grade": None, "semester": "2026-2"},
    ],
}


def seed_student(stores, node_id: str, student_id: str, document_number: str, password: str) -> dict:
    """Deja un estudiante extra directamente en el repositorio (atajo para probar aislamiento entre personas)."""
    item = {
        "record_key": f"{node_id}#{student_id}",
        "node_id": node_id,
        "student_id": student_id,
        "document_number": document_number,
        "password_hash": security.hash_password(password),
        "courses": [],
    }
    stores.records.upsert(item)
    return {"document_number": document_number, "password": password}


@pytest.fixture
def stores(monkeypatch):
    """Repositorios en memoria, clave de administrador y secreto JWT de prueba."""
    nodes, records, tokens = InMemoryNodeRepository(), InMemoryRecordRepository(), InMemoryTokenRepository()
    app.dependency_overrides[get_node_repository] = lambda: nodes
    app.dependency_overrides[get_record_repository] = lambda: records
    app.dependency_overrides[get_token_repository] = lambda: tokens
    monkeypatch.setattr(config, "ADMIN_KEY", ADMIN_KEY)
    monkeypatch.setattr(config, "JWT_SECRET", "secreto-de-pruebas-" + "x" * 32)
    monkeypatch.setattr(security, "PBKDF2_ITERATIONS", 1000)  # rápido en pruebas; el valor real va dentro de cada hash
    yield SimpleNamespace(nodes=nodes, records=records, tokens=tokens)
    app.dependency_overrides.clear()


@pytest.fixture
def api(stores):
    return TestClient(app)


@pytest.fixture
def pending_node(api):
    """Un nodo recién registrado (PENDIENTE_APROBACION). Devuelve su node_id."""
    return api.post("/api/v1/nodes/register", json=NODE).json()["node_id"]


@pytest.fixture
def active_node(api, pending_node):
    """Un nodo aprobado. Devuelve (node_id, api_key)."""
    body = api.post(f"/api/v1/admin/nodes/{pending_node}/approve", headers=ADMIN).json()
    return pending_node, body["api_key"]


@pytest.fixture
def synced_student(api, active_node):
    """Un estudiante cargado por el nodo activo. Devuelve (node_id, credenciales)."""
    node_id, api_key = active_node
    response = api.post(
        "/api/v1/node/sync-records", headers={"X-Node-API-Key": api_key}, json={"records": [STUDENT]}
    )
    assert response.status_code == 200
    return node_id, {"document_number": STUDENT["document_number"], "password": STUDENT["password"]}
