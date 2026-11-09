"""Prueba de humo de lo desplegado en AWS, solo con la biblioteca estándar.

    python scripts/smoke_aws.py demo https://xxxx.execute-api.us-east-2.amazonaws.com
    python scripts/smoke_aws.py app  https://xxxx.execute-api.us-east-2.amazonaws.com

La demo debe estar desplegada con DemoMode=1 (usa el generador de tokens de prueba).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def call(method: str, url: str, body: dict | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in {**({"Content-Type": "application/json"} if body is not None else {}), **(headers or {})}.items():
        req.add_header(key, value)
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            raw = resp.read()
            return resp.status, raw, resp.headers, time.time() - started
    except urllib.error.HTTPError as err:
        return err.code, err.read(), err.headers, time.time() - started


def show(name: str, ok: bool, status: int, seconds: float) -> bool:
    print(f"[{'OK' if ok else 'FALLO'}] {name}: HTTP {status} ({seconds:.2f} s)")
    return ok


def smoke_demo(base: str) -> bool:
    student = "20262678029"
    url = f"{base}/api/v1/federated/academic-history/{student}"
    results = []

    s, body, h, t = call("GET", base + "/")
    results.append(show("Pantalla principal", s == 200 and b"Consulta federada" in body, s, t))

    s, body, h, t = call("GET", base + "/static/app.js")
    results.append(show("Archivo estático", s == 200, s, t))

    s, body, h, t = call("GET", url)
    results.append(show("Sin token -> 403", s == 403 and b"detail" in body, s, t))

    s, body, h, t = call("POST", base + "/api/v1/demo/consent-token", {"student_id": student})
    valid = json.loads(body).get("token") if s == 200 else None
    results.append(show("Generar token válido (modo demo)", bool(valid), s, t))

    s, body, h, t = call("POST", base + "/api/v1/demo/consent-token", {"student_id": student, "expired": True})
    expired = json.loads(body).get("token") if s == 200 else None
    results.append(show("Generar token expirado (modo demo)", bool(expired), s, t))

    if valid:
        s, body, h, t = call("GET", url, headers={"X-Student-Consent-Token": valid})
        ok = s == 200 and json.loads(body).get("data", {}).get("student_id") == student
        results.append(show("Token válido -> 200", ok, s, t))
        s, body, h, t = call("GET", url + "9", headers={"X-Student-Consent-Token": valid})
        results.append(show("Token de otro estudiante -> 403", s == 403, s, t))
    if expired:
        s, body, h, t = call("GET", url, headers={"X-Student-Consent-Token": expired})
        results.append(show("Token expirado -> 403", s == 403, s, t))
    if valid:
        s, body, h, t = call("POST", base + "/api/v1/demo/consent-token", {"student_id": "12345"})
        t12345 = json.loads(body)["token"]
        s, body, h, t = call("GET", f"{base}/api/v1/federated/academic-history/12345",
                             headers={"X-Student-Consent-Token": t12345})
        results.append(show("Estudiante inexistente -> 404", s == 404, s, t))
    return all(results)


def smoke_app(base: str) -> bool:
    results = []
    s, body, h, t = call("GET", base + "/registro-nodo")
    results.append(show("Formulario /registro-nodo", s == 200 and b"Registro de universidad" in body, s, t))

    nit = str(int(time.time()))[-9:]
    payload = {"nit": nit, "name": "Universidad de Prueba Humo", "domain": "humo.edu.co",
               "contact_email": "contacto@humo.edu.co"}
    s, body, h, t = call("POST", base + "/api/v1/nodes/register", payload)
    data = json.loads(body) if s == 201 else {}
    results.append(show("Registro de nodo -> 201", s == 201 and data.get("status") == "PENDIENTE_APROBACION", s, t))
    if data:
        print(f"      código del nodo: {data.get('node_id')} (NIT de prueba {nit})")

    s, body, h, t = call("POST", base + "/api/v1/nodes/register", payload)
    results.append(show("NIT duplicado -> 409", s == 409, s, t))

    s, body, h, t = call("POST", base + "/api/v1/nodes/register", {**payload, "nit": "abc"})
    results.append(show("Datos inválidos -> 422", s == 422, s, t))

    for path, text in (("/admin", b"Solicitudes de nodos"), ("/panel-nodo", b"Carga de historiales"),
                       ("/portal-estudiante", b"Tu consentimiento")):
        s, body, h, t = call("GET", base + path)
        results.append(show(f"Pantalla {path}", s == 200 and text in body, s, t))

    admin_key = read_admin_key()
    if not data or not admin_key:
        print("      (se omite HU-02 a HU-05: falta ADMIN_KEY en .env o en el entorno)")
        return all(results)
    return all(results) and smoke_flow(base, data["node_id"], admin_key)


def read_admin_key() -> str:
    """ADMIN_KEY del entorno o del archivo .env (que no se sube a git). Nunca se imprime."""
    if os.environ.get("ADMIN_KEY"):
        return os.environ["ADMIN_KEY"]
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def smoke_flow(base: str, node_id: str, admin_key: str) -> bool:
    """HU-02 a HU-05 con el nodo recién registrado: aprobar, cargar, autorizar y revocar."""
    results = []
    admin = {"X-Admin-Key": admin_key}

    s, body, h, t = call("GET", base + "/api/v1/admin/nodes")
    results.append(show("Administración sin clave -> 403", s == 403, s, t))

    s, body, h, t = call("POST", f"{base}/api/v1/admin/nodes/{node_id}/approve", headers=admin)
    api_key = json.loads(body).get("api_key") if s == 200 else None
    results.append(show("Aprobar nodo -> 200 con API Key", bool(api_key), s, t))
    if not api_key:
        return False

    s, body, h, t = call("POST", f"{base}/api/v1/admin/nodes/{node_id}/approve", headers=admin)
    results.append(show("Aprobar otra vez -> 409", s == 409, s, t))

    doc = str(int(time.time()))[-10:]
    student = {
        "student_id": str(int(time.time())), "document_number": doc, "full_name": "Estudiante de Prueba Humo",
        "program": "Programa de Prueba", "password": "Clave-Humo-2026",
        "courses": [{"code": "H-1", "name": "Materia de prueba", "credits": 3, "grade": 4.1, "semester": "2026-1"}],
    }
    s, body, h, t = call("POST", base + "/api/v1/node/sync-records", {"records": [student]})
    results.append(show("Cargar sin API Key -> 403", s == 403, s, t))
    s, body, h, t = call("POST", base + "/api/v1/node/sync-records", {"records": [student]},
                         headers={"X-Node-API-Key": api_key})
    results.append(show("Cargar historial -> 200", s == 200 and json.loads(body).get("created") == 1, s, t))

    creds = {"document_number": doc, "password": "Clave-Humo-2026"}
    s, body, h, t = call("POST", base + "/api/v1/student/auth-token", {**creds, "password": "incorrecta", "target_node_id": node_id})
    results.append(show("Clave incorrecta -> 401", s == 401, s, t))
    s, body, h, t = call("POST", base + "/api/v1/student/auth-token", {**creds, "target_node_id": node_id})
    token = json.loads(body) if s == 201 else {}
    results.append(show("Generar token -> 201", bool(token.get("student_auth_token")), s, t))
    if not token:
        return False

    s, body, h, t = call("POST", base + "/api/v1/student/tokens/list", creds)
    states = [x["status"] for x in json.loads(body).get("tokens", [])] if s == 200 else []
    results.append(show("Listar tokens -> ACTIVO", states == ["ACTIVO"], s, t))
    s, body, h, t = call("POST", f"{base}/api/v1/student/tokens/{token['jti']}/revoke", creds)
    results.append(show("Revocar token -> 200", s == 200, s, t))
    s, body, h, t = call("POST", base + "/api/v1/student/tokens/list", creds)
    states = [x["status"] for x in json.loads(body).get("tokens", [])] if s == 200 else []
    results.append(show("Listar tokens -> REVOCADO", states == ["REVOCADO"], s, t))
    return all(results)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("demo", "app"):
        print(__doc__)
        return 2
    base = sys.argv[2].rstrip("/")
    ok = smoke_demo(base) if sys.argv[1] == "demo" else smoke_app(base)
    print("RESULTADO:", "TODO BIEN" if ok else "HAY FALLOS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
