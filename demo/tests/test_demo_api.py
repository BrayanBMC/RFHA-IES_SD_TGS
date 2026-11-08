import time

import jwt
from fastapi.testclient import TestClient

from demo import main

client = TestClient(main.app)
URL = "/api/v1/federated/academic-history/{}"
STUDENT = "20262678029"


def make_token(student_id=STUDENT, exp_delta=3600, secret=None, include_exp=True):
    payload = {"student_id": student_id}
    if include_exp:
        payload["exp"] = int(time.time()) + exp_delta
    return jwt.encode(payload, secret or main.JWT_SECRET, algorithm="HS256")


def get(student_id=STUDENT, token=None):
    headers = {"X-Student-Consent-Token": token} if token else {}
    return client.get(URL.format(student_id), headers=headers)


def test_sin_token_devuelve_403_no_422():
    assert get().status_code == 403


def test_token_valido_devuelve_200_con_historial():
    response = get(token=make_token())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["data"]["student_id"] == STUDENT
    assert len(body["data"]["courses"]) == 2


def test_token_expirado_devuelve_403():
    assert get(token=make_token(exp_delta=-10)).status_code == 403


def test_token_con_firma_incorrecta_devuelve_403():
    assert get(token=make_token(secret="otra-clave-distinta-de-32-caracteres!!")).status_code == 403


def test_token_basura_devuelve_403():
    assert get(token="esto-no-es-un-jwt").status_code == 403


def test_token_sin_exp_devuelve_403():
    assert get(token=make_token(include_exp=False)).status_code == 403


def test_token_de_otro_estudiante_devuelve_403():
    assert get(token=make_token(student_id="99999999")).status_code == 403


def test_estudiante_inexistente_devuelve_404():
    assert get(student_id="00000", token=make_token(student_id="00000")).status_code == 404


def test_handler_lambda_existe():
    assert callable(main.handler)
