"""Lanzador de la demo: prepara todo y la deja corriendo con UN comando.

    python scripts/run_demo.py                 # puerto 8000
    python scripts/run_demo.py --port 8010
    python scripts/run_demo.py --no-check      # no ejecuta la verificación automática

Qué hace, en orden:
  1. Crea el entorno virtual .venv si no existe.
  2. Instala las dependencias de demo/requirements-local.txt (solo si cambiaron).
  3. Crea .env con un JWT_SECRET aleatorio si no existe.
  4. Levanta la API con uvicorn.
  5. Verifica los 3 escenarios (403 / 403 / 200).
  6. Imprime un token válido y uno expirado para pegar en Thunder Client.
  7. Se queda corriendo hasta que presiones Ctrl+C.

Solo usa la biblioteca estándar, así que funciona con cualquier Python 3.10+.
"""
import argparse
import hashlib
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "demo" / "requirements-local.txt"
LAMBDA_REQUIREMENTS = ROOT / "demo" / "requirements.txt"
ENV_FILE = ROOT / ".env"
DEPS_MARK = VENV_DIR / ".demo_deps_hash"


def step(message: str) -> None:
    print(f"\n==> {message}", flush=True)


def venv_python() -> Path:
    sub = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return VENV_DIR / sub


def ensure_venv() -> None:
    if venv_python().exists():
        print("Entorno virtual .venv: ya existe.")
        return
    step("Creando entorno virtual .venv (solo la primera vez)")
    venv.create(VENV_DIR, with_pip=True)


def ensure_dependencies() -> None:
    current = hashlib.sha256(
        REQUIREMENTS.read_bytes() + LAMBDA_REQUIREMENTS.read_bytes()
    ).hexdigest()
    if DEPS_MARK.exists() and DEPS_MARK.read_text().strip() == current:
        print("Dependencias: al día.")
        return
    step("Instalando dependencias (solo la primera vez o si cambiaron)")
    result = subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)]
    )
    if result.returncode != 0:
        sys.exit(
            "\nNo se pudieron instalar las dependencias.\n"
            "Si usas Python 3.14 o superior, instala Python 3.12 y vuelve a ejecutar con ese Python."
        )
    DEPS_MARK.write_text(current)


def ensure_env_file() -> None:
    if ENV_FILE.exists() and "JWT_SECRET=" in ENV_FILE.read_text(encoding="utf-8"):
        print("Archivo .env: ya existe.")
        return
    step("Creando .env con un JWT_SECRET aleatorio")
    line = f"JWT_SECRET={secrets.token_urlsafe(48)}\n"
    with ENV_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def wait_until_up(base_url: str, timeout: int = 40) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{base_url}/docs", timeout=2)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


def run_script(name: str, *args: str) -> int:
    return subprocess.run([str(venv_python()), str(ROOT / "scripts" / name), *args], cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Levanta la demo del middleware RFHA-IES")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-check", action="store_true", help="omite la verificación automática")
    parser.add_argument(
        "--once", action="store_true", help="levanta, verifica los 3 escenarios y termina (para CI)"
    )
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        sys.exit("Se necesita Python 3.10 o superior (recomendado 3.11 o 3.12).")
    if not port_is_free(args.port):
        sys.exit(f"El puerto {args.port} está ocupado. Usa: python scripts/run_demo.py --port 8010")

    ensure_venv()
    ensure_dependencies()
    ensure_env_file()

    base_url = f"http://127.0.0.1:{args.port}"
    step(f"Levantando la API en {base_url}")
    server = subprocess.Popen(
        [str(venv_python()), "-m", "uvicorn", "demo.main:app", "--port", str(args.port)],
        cwd=ROOT,
    )
    try:
        if not wait_until_up(base_url):
            server.terminate()
            sys.exit("La API no arrancó a tiempo. Revisa los mensajes de arriba.")

        if not args.no_check:
            step("Verificando los 3 escenarios")
            check_code = run_script("check_demo.py", base_url)
            if args.once:
                return check_code
        elif args.once:
            return 0

        step("Tokens para Thunder Client (variables validToken y expiredToken)")
        run_script("generate_token.py")

        print(
            f"\nDEMO LISTA\n"
            f"  API:            {base_url}\n"
            f"  Documentación:  {base_url}/docs\n"
            f"  Detener:        Ctrl+C\n",
            flush=True,
        )
        server.wait()
    except KeyboardInterrupt:
        print("\nDeteniendo la demo...")
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
