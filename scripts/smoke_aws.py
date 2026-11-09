"""Prueba de humo de lo desplegado en AWS, solo con la biblioteca estándar.

    python scripts/smoke_aws.py demo https://xxxx.execute-api.us-east-2.amazonaws.com
    python scripts/smoke_aws.py app  https://xxxx.execute-api.us-east-2.amazonaws.com

La demo debe estar desplegada con DemoMode=1 (usa el generador de tokens de prueba).
"""
import json
import sys
import time
import urllib.error
import urllib.request


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
