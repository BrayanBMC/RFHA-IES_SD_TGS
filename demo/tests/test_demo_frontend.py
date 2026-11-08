from fastapi.testclient import TestClient

from demo import main

client = TestClient(main.app)
URL = "/api/v1/federated/academic-history/20262678029"


def test_pagina_principal_es_html_accesible_y_con_csp():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'lang="es"' in response.text
    assert 'name="viewport"' in response.text
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_pagina_no_usa_scripts_ni_estilos_en_linea():
    html = client.get("/").text
    assert "<style" not in html
    assert "onclick=" not in html
    assert "<script>" not in html


def test_archivos_estaticos_se_sirven():
    for path in ("/static/styles.css", "/static/app.js", "/static/favicon.svg"):
        assert client.get(path).status_code == 200, path


def test_config_indica_modo_demo_apagado_por_defecto(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", False)
    assert client.get("/api/v1/demo/config").json() == {"demo_mode": False}


def test_generar_token_esta_deshabilitado_fuera_del_modo_demo(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", False)
    response = client.post("/api/v1/demo/consent-token", json={"student_id": "20262678029"})
    assert response.status_code == 404


def test_token_generado_en_modo_demo_abre_el_historial(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", True)
    response = client.post("/api/v1/demo/consent-token", json={"student_id": "20262678029"})
    assert response.status_code == 200
    token = response.json()["token"]
    ok = client.get(URL, headers={"X-Student-Consent-Token": token})
    assert ok.status_code == 200


def test_token_expirado_generado_en_modo_demo_es_rechazado(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", True)
    response = client.post(
        "/api/v1/demo/consent-token", json={"student_id": "20262678029", "expired": True}
    )
    token = response.json()["token"]
    assert client.get(URL, headers={"X-Student-Consent-Token": token}).status_code == 403


def test_generar_token_valida_el_codigo_del_estudiante(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", True)
    response = client.post("/api/v1/demo/consent-token", json={"student_id": "<script>"})
    assert response.status_code == 422
