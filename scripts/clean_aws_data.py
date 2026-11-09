"""Vacía las tres tablas de la app final en AWS (nodos, historiales y tokens), sin borrar el stack.

Sirve para dejar la app limpia antes de una exposición, después de las pruebas de humo.
Usa el AWS CLI (igual que deploy_aws.py), así funciona con la sesión de `aws login`.

    python scripts/clean_aws_data.py --profile rfha --region us-east-2          # muestra cuántos datos hay
    python scripts/clean_aws_data.py --profile rfha --region us-east-2 --yes    # los borra
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

STACK = "rfha-app"
OUTPUT_KEYS = {"NodesTableName": "node_id", "RecordsTableName": "record_key", "TokensTableName": "jti"}


def find_aws() -> str:
    found = shutil.which("aws")
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Amazon" / "AWSCLIV2" / "aws.exe"
    if local.exists():
        return str(local)
    sys.exit("No se encontró el AWS CLI. Instálalo y abre una terminal nueva.")


def aws_json(exe: str, common: list[str], *args: str):
    result = subprocess.run([exe, *args, *common, "--output", "json"], text=True, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"Falló: aws {' '.join(args[:2])} ...\n{result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Vacía las tablas de la app final en AWS")
    parser.add_argument("--profile", default="rfha", help='perfil del AWS CLI; "none" para no usar perfil')
    parser.add_argument("--region", default="us-east-2")
    parser.add_argument("--yes", action="store_true", help="confirma el borrado (sin esto solo cuenta)")
    args = parser.parse_args()

    exe = find_aws()
    common = (["--profile", args.profile] if args.profile.lower() != "none" else []) + ["--region", args.region]

    outputs = aws_json(exe, common, "cloudformation", "describe-stacks", "--stack-name", STACK,
                       "--query", "Stacks[0].Outputs")
    tables = {o["OutputKey"]: o["OutputValue"] for o in outputs if o["OutputKey"] in OUTPUT_KEYS}
    if len(tables) != len(OUTPUT_KEYS):
        sys.exit("El stack rfha-app no tiene las tres tablas. Despliega la app final primero.")

    for output, key in OUTPUT_KEYS.items():
        name = tables[output]
        scan = aws_json(exe, common, "dynamodb", "scan", "--table-name", name,
                        "--projection-expression", "#k", "--expression-attribute-names", json.dumps({"#k": key}))
        items = scan.get("Items", [])
        print(f"{name}: {len(items)} registros")
        if args.yes:
            for item in items:
                aws_json(exe, common, "dynamodb", "delete-item", "--table-name", name,
                         "--key", json.dumps({key: item[key]}))
            if items:
                print("   borrados")
    if not args.yes:
        print("\nNo se borró nada. Agrega --yes para borrar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
