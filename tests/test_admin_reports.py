"""HU-Admin-Reports: pruebas del endpoint de descarga del reporte ejecutivo PDF.

Patrón: igual que test_hu02_approve_node.py – usa los fixtures de conftest.py.
"""
import pytest
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
# Respuesta exitosa por tipo de reporte
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("report_type", ["general", "auditoria", "resiliencia", "nodos"])
def test_admin_descarga_diferentes_tipos_de_reporte(api, report_type):
    """El admin puede solicitar cualquiera de los tipos y recibe PDF 200 con su respectivo nombre."""
    response = api.get(f"/api/v1/admin/reports/network-summary?type={report_type}", headers=ADMIN)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 1024
    disposition = response.headers.get("content-disposition", "")
    assert f"reporte-{report_type}-" in disposition
    assert ".pdf" in disposition


def test_tipo_de_reporte_invalido_devuelve_422(api):
    """Un tipo de reporte que no existe debe ser rechazado por validación FastAPI con 422."""
    response = api.get("/api/v1/admin/reports/network-summary?type=tipo_falso", headers=ADMIN)
    assert response.status_code == 422


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
    response = api.get("/api/v1/admin/reports/network-summary?type=nodos", headers=ADMIN)
    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"
    assert len(response.content) > 1024
