import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from src.app.main import app
from src.app.repositories import (
    DuplicateNitError,
    DynamoNodeRepository,
    InMemoryNodeRepository,
    get_node_repository,
)

URL = "/api/v1/nodes/register"
VALID = {
    "nit": "899999063-3",
    "name": "Universidad Nacional de Colombia",
    "domain": "unal.edu.co",
    "contact_email": "admisiones@unal.edu.co",
}


@pytest.fixture
def repo():
    repository = InMemoryNodeRepository()
    app.dependency_overrides[get_node_repository] = lambda: repository
    yield repository
    app.dependency_overrides.clear()


@pytest.fixture
def client(repo):
    return TestClient(app)


def test_registro_valido_crea_nodo_pendiente(client, repo):
    response = client.post(URL, json=VALID)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDIENTE_APROBACION"
    assert body["node_id"].startswith("IES-")
    stored = repo.get_node(body["node_id"])
    assert stored["status"] == "PENDIENTE_APROBACION"
    assert stored["nit"] == VALID["nit"]


def test_nit_duplicado_devuelve_409(client):
    assert client.post(URL, json=VALID).status_code == 201
    assert client.post(URL, json=VALID).status_code == 409


@pytest.mark.parametrize("field", list(VALID))
def test_campo_faltante_devuelve_422(client, field):
    payload = {k: v for k, v in VALID.items() if k != field}
    assert client.post(URL, json=payload).status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [
        ("nit", "abc"),
        ("domain", "no es un dominio"),
        ("contact_email", "correo-invalido"),
        ("name", "ab"),
    ],
)
def test_datos_invalidos_devuelven_422(client, field, value):
    assert client.post(URL, json={**VALID, field: value}).status_code == 422


def test_dominio_y_correo_se_normalizan_a_minusculas(client, repo):
    payload = {**VALID, "domain": "UNAL.edu.co", "contact_email": "Admisiones@UNAL.edu.co"}
    body = client.post(URL, json=payload).json()
    stored = repo.get_node(body["node_id"])
    assert stored["domain"] == "unal.edu.co"
    assert stored["contact_email"] == "admisiones@unal.edu.co"


@mock_aws
def test_repositorio_dynamodb_crea_y_detecta_duplicado(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    boto3.client("dynamodb").create_table(
        TableName="NodesTable",
        KeySchema=[{"AttributeName": "node_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "node_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    repository = DynamoNodeRepository("NodesTable")
    node = repository.create_node(dict(VALID))
    assert repository.get_node(node["node_id"])["status"] == "PENDIENTE_APROBACION"
    with pytest.raises(DuplicateNitError):
        repository.create_node(dict(VALID))
