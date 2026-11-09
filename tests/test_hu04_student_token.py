import time

import jwt
import pytest

from src.app import config
from src.app.tokens import TokenError, issue_token, verify_token
from tests.conftest import ADMIN, NODE, STUDENT

URL = "/api/v1/student/auth-token"


def request_token(api, credentials, target):
    return api.post(URL, json={**credentials, "target_node_id": target})


def test_token_valido_lleva_los_claims_del_diseno(api, synced_student):
    origin, credentials = synced_student
    response = request_token(api, credentials, origin)
    assert response.status_code == 201
    body = response.json()
    claims = jwt.decode(
        body["student_auth_token"], config.JWT_SECRET, algorithms=["HS256"], audience=origin
    )
    assert claims["sub"] == STUDENT["student_id"]
    assert claims["doc"] == STUDENT["document_number"]
    assert claims["origin"] == origin
    assert claims["aud"] == origin
    assert claims["jti"] == body["jti"]
    assert set(claims) == {"sub", "doc", "origin", "aud", "jti", "iat", "exp"}


def test_el_token_dura_24_horas(api, synced_student):
    origin, credentials = synced_student
    body = request_token(api, credentials, origin).json()
    claims = jwt.decode(body["student_auth_token"], config.JWT_SECRET, algorithms=["HS256"], audience=origin)
    assert claims["exp"] - claims["iat"] == 24 * 60 * 60
    assert body["expires_in"] == 86400


def test_cada_token_tiene_un_jti_distinto(api, synced_student):
    origin, credentials = synced_student
    first = request_token(api, credentials, origin).json()["jti"]
    second = request_token(api, credentials, origin).json()["jti"]
    assert first != second


def test_el_token_se_dirige_a_la_universidad_elegida(api, synced_student):
    origin, credentials = synced_student
    other = api.post("/api/v1/nodes/register", json={**NODE, "nit": "860007386", "name": "Universidad de los Andes"}).json()["node_id"]
    api.post(f"/api/v1/admin/nodes/{other}/approve", headers=ADMIN)
    body = request_token(api, credentials, other).json()
    assert body["audience"] == other
    assert body["origin"] == origin


def test_clave_incorrecta_devuelve_401(api, synced_student):
    origin, credentials = synced_student
    response = request_token(api, {**credentials, "password": "clave-equivocada"}, origin)
    assert response.status_code == 401


def test_cedula_inexistente_devuelve_el_mismo_401(api, synced_student):
    origin, credentials = synced_student
    wrong_password = request_token(api, {**credentials, "password": "clave-equivocada"}, origin)
    unknown_doc = request_token(api, {**credentials, "document_number": "99999999"}, origin)
    assert unknown_doc.status_code == 401
    assert unknown_doc.json() == wrong_password.json()  # no revela si la cédula existe


def test_estudiante_sin_clave_no_puede_entrar(api, active_node):
    node_id, api_key = active_node
    without_password = {k: v for k, v in STUDENT.items() if k != "password"}
    api.post("/api/v1/node/sync-records", headers={"X-Node-API-Key": api_key}, json={"records": [without_password]})
    response = request_token(api, {"document_number": STUDENT["document_number"], "password": "cualquiera-123"}, node_id)
    assert response.status_code == 401


def test_universidad_destino_inexistente_devuelve_404(api, synced_student):
    _, credentials = synced_student
    assert request_token(api, credentials, "IES-00000000").status_code == 404


def test_universidad_destino_pendiente_devuelve_404(api, synced_student):
    _, credentials = synced_student
    pending = api.post("/api/v1/nodes/register", json={**NODE, "nit": "860007386"}).json()["node_id"]
    assert request_token(api, credentials, pending).status_code == 404


def test_codigo_de_destino_con_formato_invalido_devuelve_422(api, synced_student):
    _, credentials = synced_student
    assert request_token(api, credentials, "cualquier-cosa").status_code == 422


def test_el_token_emitido_queda_registrado_para_poder_revocarlo(api, stores, synced_student):
    origin, credentials = synced_student
    body = request_token(api, credentials, origin).json()
    stored = stores.tokens.get(body["jti"])
    assert stored["document_number"] == STUDENT["document_number"]
    assert stored["aud"] == origin
    assert stored["revoked"] is False
    assert stored["ttl"] == stored["exp"]


# ---- verificación (la usarán HU-06 y HU-07) ----


def issue(stores, origin, now=None, audience=None):
    student = stores.records.get(origin, STUDENT["student_id"])
    return issue_token(student, audience or origin, stores.tokens, now=now)


def test_verify_token_acepta_un_token_vigente(stores, synced_student):
    origin, _ = synced_student
    claims = verify_token(issue(stores, origin)["token"], origin, stores.tokens)
    assert claims["sub"] == STUDENT["student_id"]


def test_verify_token_rechaza_otra_universidad(stores, synced_student):
    origin, _ = synced_student
    token = issue(stores, origin)["token"]
    with pytest.raises(TokenError, match="no fue emitido para esta universidad"):
        verify_token(token, "IES-FFFFFFFF", stores.tokens)


def test_verify_token_rechaza_un_token_expirado(stores, synced_student):
    origin, _ = synced_student
    token = issue(stores, origin, now=int(time.time()) - 2 * 86400)["token"]
    with pytest.raises(TokenError, match="expiró"):
        verify_token(token, origin, stores.tokens)


def test_verify_token_rechaza_firma_alterada(stores, synced_student):
    origin, _ = synced_student
    forged = jwt.encode({"sub": "1", "aud": origin, "jti": "a" * 32, "exp": int(time.time()) + 100}, "otro-secreto-" + "y" * 32, algorithm="HS256")
    with pytest.raises(TokenError, match="inválido"):
        verify_token(forged, origin, stores.tokens)


def test_verify_token_rechaza_basura(stores, synced_student):
    with pytest.raises(TokenError):
        verify_token("esto-no-es-un-jwt", synced_student[0], stores.tokens)


# ---- límite de 5 intentos fallidos por cédula ----


def wrong(api, doc, origin):
    return request_token(api, {"document_number": doc, "password": "clave-equivocada"}, origin)


def test_al_quinto_intento_fallido_la_cedula_se_bloquea(api, synced_student):
    origin, credentials = synced_student
    doc = credentials["document_number"]
    assert wrong(api, doc, origin).json()["detail"].endswith("Te quedan 4 intentos.")
    for _ in range(3):
        assert wrong(api, doc, origin).status_code == 401
    assert wrong(api, doc, origin).status_code == 429  # quinto fallo
    # bloqueada: ni siquiera la clave correcta entra
    blocked = request_token(api, credentials, origin)
    assert blocked.status_code == 429
    assert "Espera" in blocked.json()["detail"]


def test_un_ingreso_correcto_reinicia_el_contador(api, synced_student):
    origin, credentials = synced_student
    doc = credentials["document_number"]
    for _ in range(4):
        wrong(api, doc, origin)
    assert request_token(api, credentials, origin).status_code == 201
    assert wrong(api, doc, origin).json()["detail"].endswith("Te quedan 4 intentos.")


def test_el_bloqueo_es_por_cedula_y_vale_tambien_para_cedulas_inexistentes(api, synced_student):
    origin, credentials = synced_student
    for _ in range(5):
        wrong(api, "99999999", origin)
    assert wrong(api, "99999999", origin).status_code == 429
    assert request_token(api, credentials, origin).status_code == 201  # otra cédula no se afecta


def test_el_bloqueo_termina_a_los_15_minutos(api, stores, synced_student, monkeypatch):
    import time as real_time

    origin, credentials = synced_student
    for _ in range(5):
        wrong(api, credentials["document_number"], origin)
    assert request_token(api, credentials, origin).status_code == 429
    later = real_time.time() + 16 * 60
    monkeypatch.setattr("src.app.routers.students.time.time", lambda: later)
    assert request_token(api, credentials, origin).status_code == 201


def test_los_intentos_fallidos_tambien_cuentan_al_listar_y_revocar(api, synced_student):
    _, credentials = synced_student
    bad = {**credentials, "password": "equivocada-1"}
    for _ in range(5):
        api.post("/api/v1/student/tokens/list", json=bad)
    assert api.post("/api/v1/student/tokens/list", json=credentials).status_code == 429
