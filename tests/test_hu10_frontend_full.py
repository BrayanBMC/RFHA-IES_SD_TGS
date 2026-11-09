from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)

PAGES_TO_TEST = [
    ("/", "Tu historial académico, en cualquier universidad"),
    ("/registro-nodo", "Registro de universidad"),
    ("/admin", "Solicitudes de nodos"),
    ("/panel-nodo", "Carga de historiales"),
    ("/portal-estudiante", "Tu consentimiento"),
    ("/consulta", "Consulta de historial"),
    ("/auditoria", "Bitácora de auditoría"),
]


def test_todas_las_pantallas_se_sirven_con_cabeceras_de_seguridad_y_espanol():
    for path, expected_text in PAGES_TO_TEST:
        res = client.get(path)
        assert res.status_code == 200, f"Error en pantalla {path}"
        assert 'lang="es"' in res.text
        assert 'name="viewport"' in res.text
        assert expected_text in res.text

        # Seguridad frontend (RNF-F4)
        csp = res.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("referrer-policy") == "no-referrer"

        # Cero estilos o scripts en línea (RNF-F4)
        assert "<style>" not in res.text
        assert "<script>" not in res.text


def test_archivos_estaticos_responden_200():
    static_files = [
        "/static/styles.css",
        "/static/common.js",
        "/static/favicon.svg",
        "/static/registro.js",
        "/static/admin.js",
        "/static/panel-nodo.js",
        "/static/portal-estudiante.js",
        "/static/consulta.js",
        "/static/auditoria.js",
    ]
    for static_path in static_files:
        res = client.get(static_path)
        assert res.status_code == 200, f"Error cargando estático: {static_path}"
