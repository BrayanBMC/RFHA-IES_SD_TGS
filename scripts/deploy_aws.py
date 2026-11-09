"""Despliega la demo o la app final en AWS usando solo el AWS CLI y Python 3.12 (sin instalar SAM CLI).

Qué hace, en orden:
  1. Arma la carpeta build/<destino> con el código y sus librerías para Lambda (Linux, Python 3.12).
  2. Crea (si no existe) un depósito S3 propio para subir el paquete.
  3. `aws cloudformation package`: sube el código al depósito y genera la plantilla final.
  4. `aws cloudformation deploy`: crea o actualiza el paquete (stack) en AWS.
  5. Imprime la dirección pública.

Uso (con la sesión iniciada: aws login --profile rfha --region us-east-2):
    python scripts/deploy_aws.py demo --profile rfha --region us-east-2 --demo-mode 1
    python scripts/deploy_aws.py app  --profile rfha --region us-east-2
Para borrar:  python scripts/deploy_aws.py demo --delete --profile rfha --region us-east-2
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

TARGETS = {
    "demo": {"template": ROOT / "demo" / "template.yaml", "stack": "rfha-demo", "output": "ApiUrl"},
    "app": {"template": ROOT / "template.yaml", "stack": "rfha-app", "output": "AppUrl"},
}


def find_aws() -> str:
    found = shutil.which("aws")
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Amazon" / "AWSCLIV2" / "aws.exe"
    if local.exists():
        return str(local)
    sys.exit("No se encontró el AWS CLI. Instálalo y abre una terminal nueva.")


def read_secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    env_file = ROOT / ".env"
    if not secret and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("JWT_SECRET="):
                secret = line.split("=", 1)[1].strip()
    if not secret or len(secret) < 32:
        sys.exit("Falta JWT_SECRET (mínimo 32 caracteres) en el entorno o en .env.")
    return secret


class Aws:
    def __init__(self, profile: str, region: str) -> None:
        self.exe = find_aws()
        # "none" = no usar perfil (por ejemplo, en GitHub Actions, que entrega las claves por variables de entorno)
        self.profile = "" if profile.lower() in ("none", "") else profile
        self.region = region

    def common(self) -> list[str]:
        return (["--profile", self.profile] if self.profile else []) + ["--region", self.region]

    def run(self, *args: str, capture: bool = False) -> str:
        cmd = [self.exe, *args, *self.common()]
        result = subprocess.run(cmd, text=True, capture_output=capture)
        if result.returncode != 0:
            detail = (result.stderr or "").strip() if capture else ""
            sys.exit(f"Falló: aws {' '.join(args[:3])} ...\n{detail}")
        return (result.stdout or "").strip() if capture else ""


def build_package(target: str) -> Path:
    dest = BUILD / target
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if target == "demo":
        for name in ("main.py", "students.py"):
            shutil.copy2(ROOT / "demo" / name, dest / name)
        shutil.copytree(ROOT / "demo" / "static", dest / "static")
        requirements = ROOT / "demo" / "requirements.txt"
    else:
        shutil.copytree(
            ROOT / "src", dest / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "requirements-lambda.txt"),
        )
        requirements = ROOT / "src" / "requirements-lambda.txt"
    print(f"Instalando librerías para Lambda (Linux, Python 3.12) en {dest} ...")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements), "--target", str(dest),
            "--platform", "manylinux2014_x86_64", "--implementation", "cp", "--python-version", "3.12",
            "--only-binary=:all:", "--upgrade",
        ],
        check=True,
    )
    shutil.copy2(requirements, dest / "requirements.txt")
    return dest


def ensure_bucket(aws: Aws) -> str:
    account = aws.run("sts", "get-caller-identity", "--query", "Account", "--output", "text", capture=True)
    bucket = f"rfha-deploy-{account}-{aws.region}"
    head = subprocess.run(
        [aws.exe, "s3api", "head-bucket", "--bucket", bucket, *aws.common()],
        capture_output=True, text=True,
    )
    if head.returncode != 0:
        print(f"Creando el depósito S3 {bucket} ...")
        aws.run(
            "s3api", "create-bucket", "--bucket", bucket,
            "--create-bucket-configuration", f"LocationConstraint={aws.region}",
        )
    return bucket


def main() -> int:
    parser = argparse.ArgumentParser(description="Despliega la demo o la app final en AWS")
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("--profile", default="rfha", help='perfil del AWS CLI; "none" para no usar perfil')
    parser.add_argument("--region", default="us-east-2")
    parser.add_argument("--demo-mode", choices=["0", "1"], default="1", help="solo demo: 1 = botones de simulación")
    parser.add_argument("--delete", action="store_true", help="borra el paquete (stack) en vez de desplegar")
    args = parser.parse_args()

    if sys.version_info[:2] != (3, 12):
        print(f"Aviso: se recomienda Python 3.12 (estás usando {sys.version_info.major}.{sys.version_info.minor}).")

    info = TARGETS[args.target]
    aws = Aws(args.profile, args.region)

    if args.delete:
        print(f"Borrando el paquete {info['stack']} ...")
        aws.run("cloudformation", "delete-stack", "--stack-name", info["stack"])
        aws.run("cloudformation", "wait", "stack-delete-complete", "--stack-name", info["stack"])
        print("Borrado. (El depósito S3 rfha-deploy-... se borra a mano si ya no se usa.)")
        return 0

    build_package(args.target)
    bucket = ensure_bucket(aws)
    packaged = BUILD / f"packaged-{args.target}.yaml"

    print("Subiendo el código y generando la plantilla ...")
    aws.run(
        "cloudformation", "package", "--template-file", str(info["template"]),
        "--s3-bucket", bucket, "--output-template-file", str(packaged),
    )

    overrides = []
    if args.target == "demo":
        overrides = [f"JwtSecret={read_secret()}", f"DemoMode={args.demo_mode}"]

    print(f"Desplegando {info['stack']} (2 a 4 minutos) ...")
    cmd = [
        "cloudformation", "deploy", "--template-file", str(packaged), "--stack-name", info["stack"],
        "--capabilities", "CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND", "--no-fail-on-empty-changeset",
    ]
    if overrides:
        cmd += ["--parameter-overrides", *overrides]
    aws.run(*cmd)

    outputs = json.loads(
        aws.run("cloudformation", "describe-stacks", "--stack-name", info["stack"],
                "--query", "Stacks[0].Outputs", "--output", "json", capture=True)
    )
    url = next((o["OutputValue"] for o in outputs if o["OutputKey"] == info["output"]), "(no encontrada)")
    print(f"\nLISTO. Dirección pública: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
