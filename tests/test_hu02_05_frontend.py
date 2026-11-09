import re

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from tests.conftest import ADMIN, NODE, STUDENT

client = TestClient(app)

PAGES = {
    "/admin": {"js": "/static/admin.js", "ids": ["admin-key", "status-filter"], "api": ["/api/v1/admin/nodes", "X-Admin-Key"]},
    "/panel-nodo": {"js": "/static/panel-nodo.js", "ids": ["api-key", "records-json"], "api": ["/api/v1/node/sync-records", "X-Node-API-Key"]},
    "/portal-estudiante": {
        "js": "/static/portal-estudiante.js",
        "ids": ["document_number", "password", "target"],
        "api": ["/api/v1/student/auth-token", "/api/v1/student/tokens/list", "/revoke", "/api/v1/nodes/active"],
    },
}


@pytest.mark.parametrize("path", PAGES)
def test_la_pantalla_se_sirve_con_cabeceras_de_seguridad(path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


@pytest.mark.parametrize("path", PAGES)
def test_la_pantalla_es_accesible_en_lo_basico(path):
    html = client.get(path).text
    assert 'lang="es"' in html
    assert 'name="viewport"' in html
    assert "skip-link" in html
    assert 'aria-live="polite"' in html
    assert 'aria-current="page"' in html
    for field in PAGES[path]["ids"]:
        assert f'for="{field}"' in html, f"falta etiqueta para {field}"
        assert f'id="{field}"' in html


@pytest.mark.parametrize("path", [*PAGES, "/registro-nodo"])
def test_la_navegacion_enlaza_todas_las_pantallas(path):
    html = client.get(path).text
    for target in ("/registro-nodo", "/admin", "/panel-nodo", "/portal-estudiante"):
        assert f'href="{target}"' in html


@pytest.mark.parametrize("path", PAGES)
def test_la_pantalla_no_usa_scripts_ni_estilos_en_linea(path):
    html = client.get(path).text
    assert "<style" not in html
    assert "<script>" not in html
    assert " style=" not in html
    assert not re.search(r"\son(click|submit|change|load)=", html)


@pytest.mark.parametrize("path", PAGES)
def test_el_javascript_llama_a_las_rutas_de_la_api(path):
    js = client.get(PAGES[path]["js"]).text
    for fragment in PAGES[path]["api"]:
        assert fragment in js


@pytest.mark.parametrize("js", ["/static/common.js", *[p["js"] for p in PAGES.values()]])
def test_el_javascript_es_seguro(js):
    response = client.get(js)
    assert response.status_code == 200
    code = response.text
    assert "innerHTML" not in code
    assert "localStorage" not in code
    assert "sessionStorage" not in code
    assert "eval(" not in code


def test_la_pantalla_de_estudiante_no_pone_la_clave_en_la_direccion():
    js = client.get("/static/portal-estudiante.js").text
    assert "?password" not in js and "&password" not in js


def test_flujo_completo_registro_aprobacion_carga_token_y_revocacion(api, stores):
    """Lo mismo que hacen las cuatro pantallas, de punta a punta."""
    # HU-01 Registro
    node_id = api.post("/api/v1/nodes/register", json=NODE).json()["node_id"]
    # HU-02 Aprobación
    approval = api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN).json()
    node_headers = {"X-Node-API-Key": approval["api_key"]}
    # HU-03 Carga de historiales
    assert api.post("/api/v1/node/sync-records", headers=node_headers, json={"records": [STUDENT]}).status_code == 200
    # HU-04 Token del estudiante
    credentials = {"document_number": STUDENT["document_number"], "password": STUDENT["password"]}
    token = api.post("/api/v1/student/auth-token", json={**credentials, "target_node_id": node_id}).json()
    assert token["student_auth_token"].count(".") == 2
    # HU-05 Revocación
    revoked = api.post(f"/api/v1/student/tokens/{token['jti']}/revoke", json=credentials)
    assert revoked.status_code == 200
    states = [t["status"] for t in api.post("/api/v1/student/tokens/list", json=credentials).json()["tokens"]]
    assert states == ["REVOCADO"]
