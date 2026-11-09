import time

import boto3
import pytest
from moto import mock_aws

from src.app.repositories import DynamoTokenRepository
from src.app.tokens import TokenError, issue_token, verify_token
from tests.conftest import NODE, STUDENT, seed_student

LIST_URL = "/api/v1/student/tokens/list"


def make_token(api, origin, credentials):
    return api.post("/api/v1/student/auth-token", json={**credentials, "target_node_id": origin}).json()


def revoke(api, jti, credentials):
    return api.post(f"/api/v1/student/tokens/{jti}/revoke", json=credentials)


def test_la_lista_muestra_los_tokens_del_estudiante(api, synced_student):
    origin, credentials = synced_student
    first = make_token(api, origin, credentials)
    response = api.post(LIST_URL, json=credentials)
    assert response.status_code == 200
    tokens = response.json()["tokens"]
    assert [t["jti"] for t in tokens] == [first["jti"]]
    assert tokens[0]["status"] == "ACTIVO"
    assert tokens[0]["audience_name"] == NODE["name"]


def test_la_lista_exige_credenciales_correctas(api, synced_student):
    _, credentials = synced_student
    assert api.post(LIST_URL, json={**credentials, "password": "equivocada-1"}).status_code == 401


def test_revocar_pone_el_token_en_la_lista_negra(api, stores, synced_student):
    origin, credentials = synced_student
    token = make_token(api, origin, credentials)
    response = revoke(api, token["jti"], credentials)
    assert response.status_code == 200
    assert response.json()["status"] == "REVOCADO"
    assert stores.tokens.get(token["jti"])["revoked"] is True


def test_un_token_revocado_deja_de_ser_valido(api, stores, synced_student):
    origin, credentials = synced_student
    token = make_token(api, origin, credentials)
    assert verify_token(token["student_auth_token"], origin, stores.tokens)["jti"] == token["jti"]
    revoke(api, token["jti"], credentials)
    with pytest.raises(TokenError, match="revocado"):
        verify_token(token["student_auth_token"], origin, stores.tokens)


def test_revocar_un_token_no_afecta_a_los_demas(api, stores, synced_student):
    origin, credentials = synced_student
    kept = make_token(api, origin, credentials)
    revoked = make_token(api, origin, credentials)
    revoke(api, revoked["jti"], credentials)
    assert verify_token(kept["student_auth_token"], origin, stores.tokens)
    states = {t["jti"]: t["status"] for t in api.post(LIST_URL, json=credentials).json()["tokens"]}
    assert states == {kept["jti"]: "ACTIVO", revoked["jti"]: "REVOCADO"}


def test_revocar_dos_veces_es_inofensivo(api, synced_student):
    origin, credentials = synced_student
    token = make_token(api, origin, credentials)
    assert revoke(api, token["jti"], credentials).status_code == 200
    assert revoke(api, token["jti"], credentials).status_code == 200


def test_revocar_exige_credenciales_correctas(api, stores, synced_student):
    origin, credentials = synced_student
    token = make_token(api, origin, credentials)
    assert revoke(api, token["jti"], {**credentials, "password": "equivocada-1"}).status_code == 401
    assert stores.tokens.get(token["jti"])["revoked"] is False


def test_no_se_puede_revocar_el_token_de_otra_persona(api, stores, synced_student):
    origin, credentials = synced_student
    token = make_token(api, origin, credentials)
    intruder = seed_student(stores, origin, "20251234501", "1098765432", "Clave-2026-B")
    assert revoke(api, token["jti"], intruder).status_code == 404
    assert stores.tokens.get(token["jti"])["revoked"] is False


@pytest.mark.parametrize("jti", ["0" * 32, "no-es-un-jti", "A" * 32])
def test_revocar_un_token_inexistente_devuelve_404(api, synced_student, jti):
    _, credentials = synced_student
    assert revoke(api, jti, credentials).status_code == 404


def test_la_lista_marca_los_tokens_vencidos(api, stores, synced_student):
    origin, credentials = synced_student
    student = stores.records.get(origin, STUDENT["student_id"])
    old = issue_token(student, origin, stores.tokens, now=int(time.time()) - 3 * 86400)
    states = {t["jti"]: t["status"] for t in api.post(LIST_URL, json=credentials).json()["tokens"]}
    assert states[old["jti"]] == "EXPIRADO"


def test_un_estudiante_no_ve_los_tokens_de_otro(api, stores, synced_student):
    origin, credentials = synced_student
    make_token(api, origin, credentials)
    other = seed_student(stores, origin, "2", "55555555", "Otra-clave-1")
    assert api.post(LIST_URL, json=other).json() == {"tokens": []}


@mock_aws
def test_repositorio_dynamodb_de_tokens_revoca(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("dynamodb").create_table(
        TableName="TokensTable",
        KeySchema=[{"AttributeName": "jti", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "jti", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repo = DynamoTokenRepository("TokensTable")
    now = int(time.time())
    for jti, issued in (("a" * 32, now), ("b" * 32, now + 5)):
        repo.put({"jti": jti, "document_number": "123456", "aud": "IES-AAAAAAAA", "issued_at": issued, "exp": now + 86400, "ttl": now + 86400, "revoked": False})
    assert [t["jti"] for t in repo.list_by_document("123456")] == ["b" * 32, "a" * 32]  # el más nuevo primero
    repo.revoke("a" * 32)
    assert repo.get("a" * 32)["revoked"] is True
    assert repo.get("b" * 32)["revoked"] is False
    assert repo.get("c" * 32) is None
