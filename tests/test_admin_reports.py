"""HU-Admin-Reports: pruebas del endpoint de descarga del reporte ejecutivo PDF.

Patrón: igual que test_hu02_approve_node.py – usa los fixtures de conftest.py.
"""
from tests.conftest import ADMIN


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------


def test_sin_clave_de_admin_devuelve_403(api):
    """El endpoint exige X-Admin-Key; sin ella debe rechazar con 403."""
    assert api.get("/api/v1/admin/reports/network-summary").status_code == 403


def test_clave_de_admin_incorrecta_devuelve_403(api):
    """Una clave equivocada también debe rechazarse con 403."""
    assert api.get(
        "/api/v1/admin/reports/network-summary",
        headers={"X-Admin-Key": "clave-incorrecta"},
    ).status_code == 403


# ---------------------------------------------------------------------------
# Respuesta exitosa
# ---------------------------------------------------------------------------


def test_admin_autenticado_recibe_pdf_200(api):
    """Con la clave correcta debe devolver 200 y content-type application/pdf."""
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_pdf_no_esta_vacio(api):
    """El cuerpo de la respuesta debe ser un PDF de al menos 1 KB."""
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    assert len(response.content) > 1024, "El PDF parece vacío o demasiado pequeño"


def test_pdf_empieza_con_cabecera_pdf(api):
    """Los primeros bytes deben ser la firma mágica de PDF (%PDF-)."""
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-", "El contenido no es un PDF válido"


def test_cabecera_content_disposition_presente(api):
    """La respuesta debe incluir Content-Disposition con filename para descarga."""
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "reporte-rfha-" in disposition
    assert ".pdf" in disposition


def test_cabecera_cache_control_no_store(api):
    """La respuesta debe indicar Cache-Control: no-store (datos sensibles)."""
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


# ---------------------------------------------------------------------------
# Reporte con datos reales en repositorios
# ---------------------------------------------------------------------------


def test_reporte_con_nodos_y_logs(api, stores):
    """El reporte se genera correctamente cuando hay nodos y logs en el sistema."""
    from tests.conftest import ADMIN, NODE

    # Registrar y aprobar un nodo
    node_id = api.post("/api/v1/nodes/register", json=NODE).json()["node_id"]
    api.post(f"/api/v1/admin/nodes/{node_id}/approve", headers=ADMIN)

    # El reporte sigue siendo un PDF válido con datos
    response = api.get("/api/v1/admin/reports/network-summary", headers=ADMIN)
    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 1024
