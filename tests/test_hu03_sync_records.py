import copy

import boto3
import pytest
from moto import mock_aws

from src.app.repositories import DynamoRecordRepository, record_key
from src.app.security import hash_password, record_signature, verify_password
from tests.conftest import STUDENT

URL = "/api/v1/node/sync-records"


def sync(api, api_key, records):
    return api.post(URL, headers={"X-Node-API-Key": api_key}, json={"records": records})


def test_sin_api_key_devuelve_403(api, active_node):
    assert api.post(URL, json={"records": [STUDENT]}).status_code == 403


def test_api_key_invalida_devuelve_403(api, active_node):
    assert sync(api, "rfha_clave-falsa", [STUDENT]).status_code == 403


def test_la_api_key_de_un_nodo_pendiente_no_existe(api, pending_node):
    """Un nodo sin aprobar no tiene clave: cualquier clave se rechaza."""
    assert sync(api, "rfha_cualquiera", [STUDENT]).status_code == 403


def test_sincronizar_crea_los_historiales(api, stores, active_node):
    node_id, api_key = active_node
    response = sync(api, api_key, [STUDENT])
    assert response.status_code == 200
    assert response.json() == {"node_id": node_id, "received": 1, "created": 1, "updated": 0}
    stored = stores.records.get(node_id, STUDENT["student_id"])
    assert stored["full_name"] == STUDENT["full_name"]
    assert stored["record_key"] == record_key(node_id, STUDENT["student_id"])


def test_el_estado_de_cada_asignatura_se_calcula(api, stores, active_node):
    node_id, api_key = active_node
    sync(api, api_key, [STUDENT])
    statuses = [c["status"] for c in stores.records.get(node_id, STUDENT["student_id"])["courses"]]
    assert statuses == ["APROBADA", "REPROBADA", "EN_CURSO"]


def test_la_clave_del_estudiante_solo_se_guarda_como_hash(api, stores, active_node):
    node_id, api_key = active_node
    sync(api, api_key, [STUDENT])
    stored = stores.records.get(node_id, STUDENT["student_id"])
    assert STUDENT["password"] not in str(stored)
    assert stored["password_hash"].startswith("pbkdf2_sha256$")
    assert verify_password(STUDENT["password"], stored["password_hash"])
    assert not verify_password("otra-clave-123", stored["password_hash"])


def test_cada_historial_lleva_una_firma_sha256_verificable(api, stores, active_node):
    node_id, api_key = active_node
    sync(api, api_key, [STUDENT])
    stored = stores.records.get(node_id, STUDENT["student_id"])
    signed = {k: v for k, v in stored.items() if k not in ("record_key", "password_hash", "digital_signature_hash", "synced_at")}
    assert stored["digital_signature_hash"] == record_signature(signed)
    assert len(stored["digital_signature_hash"]) == 64
    signed["courses"][0]["grade"] = 5.0  # alguien altera una nota
    assert stored["digital_signature_hash"] != record_signature(signed)


def test_la_firma_no_depende_del_orden_de_las_claves():
    assert record_signature({"a": 1, "b": [1, 2]}) == record_signature({"b": [1, 2], "a": 1})


def test_sincronizar_de_nuevo_actualiza_sin_duplicar(api, stores, active_node):
    node_id, api_key = active_node
    sync(api, api_key, [STUDENT])
    changed = copy.deepcopy(STUDENT)
    changed["courses"][1]["grade"] = 3.4
    response = sync(api, api_key, [changed])
    assert response.json() == {"node_id": node_id, "received": 1, "created": 0, "updated": 1}
    stored = stores.records.get(node_id, STUDENT["student_id"])
    assert stored["courses"][1]["grade"] == 3.4
    assert stored["courses"][1]["status"] == "APROBADA"
    assert len(stores.records.find_by_document(STUDENT["document_number"])) == 1


def test_si_no_se_envia_clave_se_conserva_la_anterior(api, stores, active_node):
    node_id, api_key = active_node
    sync(api, api_key, [STUDENT])
    before = stores.records.get(node_id, STUDENT["student_id"])["password_hash"]
    without_password = {k: v for k, v in STUDENT.items() if k != "password"}
    sync(api, api_key, [without_password])
    assert stores.records.get(node_id, STUDENT["student_id"])["password_hash"] == before


def test_un_nodo_no_puede_escribir_datos_de_otro(api, stores, active_node):
    """El dueño sale de la API Key; un node_id en el cuerpo se ignora."""
    node_id, api_key = active_node
    forged = {**STUDENT, "node_id": "IES-FFFFFFFF"}
    assert sync(api, api_key, [forged]).status_code == 200
    assert stores.records.get("IES-FFFFFFFF", STUDENT["student_id"]) is None
    assert stores.records.get(node_id, STUDENT["student_id"]) is not None


def test_acepta_hasta_100_estudiantes(api, active_node):
    _, api_key = active_node
    batch = [{**STUDENT, "student_id": str(20260000000 + i), "document_number": str(1000000000 + i)} for i in range(100)]
    response = sync(api, api_key, batch)
    assert response.status_code == 200
    assert response.json()["created"] == 100


def test_mas_de_100_estudiantes_devuelve_422(api, active_node):
    _, api_key = active_node
    batch = [{**STUDENT, "student_id": str(20260000000 + i)} for i in range(101)]
    assert sync(api, api_key, batch).status_code == 422


def test_lote_vacio_devuelve_422(api, active_node):
    assert sync(api, active_node[1], []).status_code == 422


@pytest.mark.parametrize(
    "change",
    [
        {"student_id": "abc"},
        {"document_number": "12"},
        {"full_name": "ab"},
        {"academic_status": "DESCONOCIDO"},
        {"password": "corta"},
        {"courses": [{"code": "X", "name": "Y", "credits": 3, "grade": 6.0, "semester": "2026-1"}]},
        {"courses": [{"code": "X", "name": "Y", "credits": 3, "grade": 4.0, "semester": "26-1"}]},
        {"courses": [{"code": "X", "name": "Y", "credits": -1, "grade": 4.0, "semester": "2026-1"}]},
    ],
)
def test_datos_invalidos_devuelven_422_y_no_guardan_nada(api, stores, active_node, change):
    assert sync(api, active_node[1], [{**STUDENT, **change}]).status_code == 422
    assert stores.records.find_by_document(STUDENT["document_number"]) == []


def test_hash_de_clave_usa_sal_distinta_cada_vez():
    assert hash_password("misma-clave-1") != hash_password("misma-clave-1")


@mock_aws
def test_repositorio_dynamodb_guarda_notas_decimales(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("dynamodb").create_table(
        TableName="RecordsTable",
        KeySchema=[{"AttributeName": "record_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "record_key", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repo = DynamoRecordRepository("RecordsTable")
    item = {
        "record_key": "IES-AAAAAAAA#1",
        "node_id": "IES-AAAAAAAA",
        "student_id": "1",
        "document_number": "1012345678",
        "courses": [{"code": "A", "grade": 4.5, "credits": 3}, {"code": "B", "grade": None, "credits": 2}],
    }
    repo.upsert(item)
    stored = repo.get("IES-AAAAAAAA", "1")
    assert float(stored["courses"][0]["grade"]) == 4.5
    assert stored["courses"][1]["grade"] is None
    assert [r["record_key"] for r in repo.find_by_document("1012345678")] == ["IES-AAAAAAAA#1"]
    assert repo.find_by_document("999999") == []
