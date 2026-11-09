"""Sembrador de datos de prueba completos para RFHA-IES (local y AWS DynamoDB).

Siembra 4 universidades (nodos IES activos) y 6 estudiantes con historiales reales
para probar todos los casos de uso.
Usa el AWS CLI directamente para aprovechar la sesión de `aws login`.
"""
import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STACK = "rfha-app"
PBKDF2_ITERATIONS = 100_000

SAMPLE_NODES = [
    {
        "node_id": "IES-1111AAAA",
        "name": "Universidad Distrital Francisco José de Caldas",
        "nit": "899999230-7",
        "domain": "udistrital.edu.co",
        "contact_email": "admisiones@udistrital.edu.co",
        "api_key": "rfha_udistrital_prod_key_2026_sec",
    },
    {
        "node_id": "IES-2222BBBB",
        "name": "Universidad Nacional de Colombia",
        "nit": "899999063-3",
        "domain": "unal.edu.co",
        "contact_email": "admisiones@unal.edu.co",
        "api_key": "rfha_unal_prod_key_2026_secure99",
    },
    {
        "node_id": "IES-3333CCCC",
        "name": "Pontificia Universidad Javeriana",
        "nit": "860007386",
        "domain": "javeriana.edu.co",
        "contact_email": "registro@javeriana.edu.co",
        "api_key": "rfha_javeriana_prod_key_2026_sec",
    },
    {
        "node_id": "IES-4444DDDD",
        "name": "Universidad de los Andes",
        "nit": "860007373-4",
        "domain": "uniandes.edu.co",
        "contact_email": "admisiones@uniandes.edu.co",
        "api_key": "rfha_uniandes_prod_key_2026_sec9",
    },
]

SAMPLE_STUDENTS = [
    {
        "node_id": "IES-1111AAAA",
        "student_id": "20262678029",
        "document_number": "1012345678",
        "full_name": "Brayan Acosta Parrado",
        "program": "Ingeniería en Telemática",
        "academic_status": "ACTIVO",
        "password": "Clave-2026-A",
        "courses": [
            {"code": "165-101", "name": "Cálculo Diferencial", "credits": 4, "grade": 4.5, "semester": "2024-1"},
            {"code": "165-102", "name": "Álgebra Lineal", "credits": 3, "grade": 4.8, "semester": "2024-1"},
            {"code": "165-201", "name": "Estructuras de Datos", "credits": 3, "grade": 4.2, "semester": "2024-2"},
            {"code": "165-202", "name": "Redes de Comunicación I", "credits": 3, "grade": 4.7, "semester": "2024-2"},
            {"code": "165-301", "name": "Sistemas Distribuidos", "credits": 3, "grade": 4.9, "semester": "2025-1"},
            {"code": "165-302", "name": "Teoría General de Sistemas", "credits": 3, "grade": 4.6, "semester": "2025-1"},
            {"code": "165-401", "name": "Arquitectura de Redes y Servicios", "credits": 3, "grade": 4.5, "semester": "2025-2"},
            {"code": "165-402", "name": "Proyecto Telemático Final", "credits": 4, "grade": None, "semester": "2026-1"},
        ],
    },
    {
        "node_id": "IES-1111AAAA",
        "student_id": "20221050914",
        "document_number": "1019876543",
        "full_name": "Juan Sebastián Pardo Gil",
        "program": "Ingeniería Industrial",
        "academic_status": "RETIRADO",
        "password": "Clave-Juan-2026",
        "courses": [
            {"code": "IND-101", "name": "Introducción a la Ingeniería Industrial", "credits": 3, "grade": 3.8, "semester": "2022-1"},
            {"code": "IND-102", "name": "Física I", "credits": 4, "grade": 2.8, "semester": "2022-1"},
            {"code": "IND-102", "name": "Física I", "credits": 4, "grade": 3.4, "semester": "2022-2"},
            {"code": "IND-201", "name": "Probabilidad y Estadística", "credits": 3, "grade": 2.9, "semester": "2023-1"},
            {"code": "IND-202", "name": "Química General", "credits": 3, "grade": 3.6, "semester": "2023-1"},
            {"code": "IND-203", "name": "Dibujo Técnico", "credits": 2, "grade": 3.5, "semester": "2023-1"},
        ],
    },
    {
        "node_id": "IES-2222BBBB",
        "student_id": "20251234501",
        "document_number": "1098765432",
        "full_name": "Laura Camila Ríos Herrera",
        "program": "Ingeniería de Sistemas y Computación",
        "academic_status": "ACTIVO",
        "password": "Clave-2026-B",
        "courses": [
            {"code": "UN-101", "name": "Programación Orientada a Objetos", "credits": 3, "grade": 4.8, "semester": "2024-1"},
            {"code": "UN-102", "name": "Cálculo Diferencial", "credits": 4, "grade": 4.0, "semester": "2024-1"},
            {"code": "UN-201", "name": "Cálculo Integral", "credits": 4, "grade": 2.6, "semester": "2024-2"},
            {"code": "UN-201", "name": "Cálculo Integral", "credits": 4, "grade": 3.4, "semester": "2025-1"},
            {"code": "UN-202", "name": "Estructuras Discretas", "credits": 3, "grade": 4.4, "semester": "2025-1"},
            {"code": "UN-203", "name": "Física Mecánica", "credits": 4, "grade": 3.9, "semester": "2025-1"},
            {"code": "UN-301", "name": "Bases de Datos", "credits": 3, "grade": 4.6, "semester": "2025-2"},
            {"code": "UN-302", "name": "Sistemas Operativos", "credits": 3, "grade": 4.3, "semester": "2025-2"},
            {"code": "UN-401", "name": "Ingeniería de Software", "credits": 3, "grade": None, "semester": "2026-1"},
        ],
    },
    {
        "node_id": "IES-2222BBBB",
        "student_id": "20252345678",
        "document_number": "1024681357",
        "full_name": "María Fernanda Ospina Duarte",
        "program": "Estadística",
        "academic_status": "ACTIVO",
        "password": "Clave-Maria-2026",
        "courses": [
            {"code": "EST-101", "name": "Fundamentos de Probabilidad", "credits": 4, "grade": 4.1, "semester": "2025-1"},
            {"code": "EST-102", "name": "Cálculo I", "credits": 4, "grade": 3.7, "semester": "2025-1"},
            {"code": "EST-103", "name": "Programación Estadística en R", "credits": 3, "grade": 4.5, "semester": "2025-1"},
            {"code": "EST-201", "name": "Inferencia Estadística", "credits": 4, "grade": 3.9, "semester": "2025-2"},
            {"code": "EST-202", "name": "Álgebra Lineal Aplicada", "credits": 3, "grade": 3.6, "semester": "2025-2"},
        ],
    },
    {
        "node_id": "IES-3333CCCC",
        "student_id": "20241122002",
        "document_number": "1035792468",
        "full_name": "Andrés Felipe Moreno Castro",
        "program": "Ingeniería Electrónica",
        "academic_status": "GRADUADO",
        "password": "Clave-Andres-2026",
        "courses": [
            {"code": "JAV-101", "name": "Circuitos Eléctricos I", "credits": 4, "grade": 4.2, "semester": "2021-1"},
            {"code": "JAV-102", "name": "Dispositivos Semiconductores", "credits": 3, "grade": 3.9, "semester": "2021-2"},
            {"code": "JAV-201", "name": "Sistemas Digitales", "credits": 4, "grade": 4.3, "semester": "2022-1"},
            {"code": "JAV-301", "name": "Microprocesadores y Embebidos", "credits": 4, "grade": 4.6, "semester": "2023-1"},
            {"code": "JAV-401", "name": "Procesamiento Digital de Señales", "credits": 3, "grade": 4.0, "semester": "2024-1"},
            {"code": "JAV-501", "name": "Trabajo de Grado", "credits": 4, "grade": 4.8, "semester": "2025-2"},
        ],
    },
    {
        "node_id": "IES-4444DDDD",
        "student_id": "20231098763",
        "document_number": "1046801357",
        "full_name": "Valentina Torres Quintero",
        "program": "Economía",
        "academic_status": "ACTIVO",
        "password": "Clave-Vale-2026",
        "courses": [
            {"code": "AND-101", "name": "Principios de Microeconomía", "credits": 3, "grade": 4.8, "semester": "2023-1"},
            {"code": "AND-102", "name": "Principios de Macroeconomía", "credits": 3, "grade": 4.7, "semester": "2023-1"},
            {"code": "AND-201", "name": "Microeconomía Intermedia", "credits": 4, "grade": 4.9, "semester": "2023-2"},
            {"code": "AND-202", "name": "Econometría I", "credits": 4, "grade": 4.4, "semester": "2024-1"},
            {"code": "AND-301", "name": "Teoría de Juegos", "credits": 3, "grade": 4.7, "semester": "2024-2"},
            {"code": "AND-302", "name": "Finanzas Internacionales", "credits": 3, "grade": 4.6, "semester": "2025-1"},
        ],
    },
]


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def _course_status(grade: float | None) -> str:
    if grade is None:
        return "EN_CURSO"
    return "APROBADA" if grade >= 3.0 else "REPROBADA"


def record_signature(record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def find_aws() -> str:
    found = shutil.which("aws")
    if found:
        return found
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Amazon" / "AWSCLIV2" / "aws.exe"
    if local.exists():
        return str(local)
    sys.exit("No se encontró el AWS CLI. Instálalo y abre una terminal nueva.")


def aws_cmd(exe: str, common: list[str], *args: str) -> dict:
    cmd = [exe, *args, *common, "--output", "json"]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"Falló aws {' '.join(args[:2])} ...\n{result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def py_to_dynamo_json(val):
    """Convierte tipos python a formato typed de DynamoDB para aws cli."""
    if val is None:
        return {"NULL": True}
    elif isinstance(val, str):
        return {"S": val}
    elif isinstance(val, (int, float)):
        return {"N": str(val)}
    elif isinstance(val, bool):
        return {"BOOL": val}
    elif isinstance(val, list):
        return {"L": [py_to_dynamo_json(x) for x in val]}
    elif isinstance(val, dict):
        return {"M": {k: py_to_dynamo_json(v) for k, v in val.items()}}
    return {"NULL": True}


def put_item_aws(exe: str, common: list[str], table: str, item_dict: dict):
    typed_item = {k: py_to_dynamo_json(v) for k, v in item_dict.items()}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(typed_item, f)
        temp_name = f.name
    try:
        aws_cmd(exe, common, "dynamodb", "put-item", "--table-name", table, "--item", f"file://{temp_name}")
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)


def main():
    parser = argparse.ArgumentParser(description="Siembra datos de prueba en AWS DynamoDB")
    parser.add_argument("--profile", default="rfha", help="Perfil AWS CLI")
    parser.add_argument("--region", default="us-east-2", help="Región AWS")
    args = parser.parse_args()

    exe = find_aws()
    common = (["--profile", args.profile] if args.profile.lower() != "none" else []) + ["--region", args.region]

    print(f"-> Obteniendo tablas de CloudFormation stack '{STACK}'...")
    outputs = aws_cmd(exe, common, "cloudformation", "describe-stacks", "--stack-name", STACK,
                      "--query", "Stacks[0].Outputs")
    table_map = {o["OutputKey"]: o["OutputValue"] for o in outputs}
    nodes_table = table_map.get("NodesTableName")
    records_table = table_map.get("RecordsTableName")

    if not nodes_table or not records_table:
        sys.exit("No se encontraron las tablas en los outputs de CloudFormation.")

    print(f"   NodesTable:   {nodes_table}")
    print(f"   RecordsTable: {records_table}")

    now = datetime.now(timezone.utc).isoformat()

    # 1. Sembrar Nodos
    print("\n1. Sembrando Nodos Universitarios...")
    for n in SAMPLE_NODES:
        item = {
            "node_id": n["node_id"],
            "status": "ACTIVO",
            "name": n["name"],
            "nit": n["nit"],
            "domain": n["domain"],
            "contact_email": n["contact_email"],
            "api_key_hash": hash_api_key(n["api_key"]),
            "created_at": now,
            "approved_at": now,
        }
        put_item_aws(exe, common, nodes_table, item)
        print(f"   [OK] {n['node_id']} - {n['name']}")

    # 2. Sembrar Estudiantes
    print("\n2. Sembrando Historiales de Estudiantes...")
    for s in SAMPLE_STUDENTS:
        courses = [
            {
                "code": c["code"],
                "name": c["name"],
                "credits": c["credits"],
                "grade": c["grade"],
                "semester": c["semester"],
                "status": _course_status(c["grade"]),
            }
            for c in s["courses"]
        ]
        data_for_sig = {
            "node_id": s["node_id"],
            "student_id": s["student_id"],
            "document_number": s["document_number"],
            "full_name": s["full_name"],
            "program": s["program"],
            "academic_status": s["academic_status"],
            "courses": courses,
        }
        signature = record_signature(data_for_sig)
        pw_hash = hash_password(s["password"])

        item = {
            "record_key": f"{s['node_id']}#{s['student_id']}",
            "node_id": s["node_id"],
            "student_id": s["student_id"],
            "document_number": s["document_number"],
            "full_name": s["full_name"],
            "program": s["program"],
            "academic_status": s["academic_status"],
            "courses": courses,
            "password_hash": pw_hash,
            "digital_signature_hash": signature,
            "synced_at": now,
        }
        put_item_aws(exe, common, records_table, item)
        print(f"   [OK] {s['document_number']} - {s['full_name']} ({s['program']})")

    print("\n-> SIEMBRA EXITOSA: Todos los datos están cargados y activos en AWS DynamoDB.")


if __name__ == "__main__":
    main()
