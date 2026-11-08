"""Verifica los tres escenarios de la demo contra una URL base (local o AWS).

Uso:
    python scripts/check_demo.py http://127.0.0.1:8000
    python scripts/check_demo.py https://xxxx.execute-api.us-east-1.amazonaws.com

JWT_SECRET debe ser el mismo que usa el servidor probado.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_token import DEFAULT_STUDENT, make_token  # noqa: E402


def get(base_url: str, token: str | None) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}/api/v1/federated/academic-history/{DEFAULT_STUDENT}"
    request = urllib.request.Request(url)
    if token:
        request.add_header("X-Student-Consent-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1]
    scenarios = [
        ("Sin token", None, 403),
        ("Token expirado", make_token(expires_in=-3600), 403),
        ("Token válido", make_token(), 200),
    ]
    failed = 0
    for name, token, expected in scenarios:
        status, body = get(base, token)
        ok = status == expected
        if ok and expected == 200:
            ok = body.get("data", {}).get("student_id") == DEFAULT_STUDENT
        print(f"[{'OK' if ok else 'FALLO'}] {name}: HTTP {status} (esperado {expected})")
        failed += 0 if ok else 1
    print("RESULTADO:", "TODO BIEN" if failed == 0 else f"{failed} escenario(s) fallaron")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
