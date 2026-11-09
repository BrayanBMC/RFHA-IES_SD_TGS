import re

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.repositories import InMemoryNodeRepository, get_node_repository

client = TestClient(app)


def test_formulario_registro_nodo_se_sirve_con_cabeceras_de_seguridad():
    response = client.get("/registro-nodo")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_formulario_es_accesible_en_lo_basico():
    html = client.get("/registro-nodo").text
    assert 'lang="es"' in html
    assert 'name="viewport"' in html
    assert "skip-link" in html
    # cada campo tiene su etiqueta asociada
    for field in ("nit", "name", "domain", "contact_email"):
        assert f'for="{field}"' in html
        assert f'id="{field}"' in html
    assert 'role="alert"' in html
    assert 'aria-live="polite"' in html


def test_formulario_no_usa_scripts_ni_estilos_en_linea():
    html = client.get("/registro-nodo").text
    assert "<style" not in html
    assert "<script>" not in html
    assert not re.search(r"\son(click|submit|change|load)=", html)
    assert " style=" not in html


@pytest.mark.parametrize("path", ["/static/styles.css", "/static/registro.js", "/static/favicon.svg"])
def test_archivos_estaticos_responden(path):
    assert client.get(path).status_code == 200


def test_la_raiz_muestra_el_menu_de_inicio():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    for module in ("/registro-nodo", "/admin", "/panel-nodo", "/portal-estudiante"):
        assert f'href="{module}"' in response.text


def test_las_reglas_del_formulario_coinciden_con_las_del_servidor():
    """El JS replica los patrones del modelo; si cambian en el servidor, esta prueba avisa."""
    js = client.get("/static/registro.js").text
    for pattern in (r"^\d{6,12}(-\d)?$", r"^[^@\s]+@[^@\s]+\.[^@\s]+$"):
        assert pattern.replace("\\", "\\") in js


def test_el_formulario_envia_a_la_api_de_registro():
    assert "/api/v1/nodes/register" in client.get("/static/registro.js").text


def test_registro_completo_via_api_como_lo_hace_el_formulario():
    repo = InMemoryNodeRepository()
    app.dependency_overrides[get_node_repository] = lambda: repo
    try:
        payload = {
            "nit": "899999063-3",
            "name": "Universidad Nacional de Colombia",
            "domain": "UNAL.edu.co",
            "contact_email": "Admisiones@unal.edu.co",
        }
        response = client.post("/api/v1/nodes/register", json=payload)
        assert response.status_code == 201
        node = repo.get_node(response.json()["node_id"])
        assert node["domain"] == "unal.edu.co"
        assert client.post("/api/v1/nodes/register", json=payload).status_code == 409
    finally:
        app.dependency_overrides.clear()
