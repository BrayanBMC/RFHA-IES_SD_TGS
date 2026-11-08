"""Datos FICTICIOS de la demo (representan lo que cada nodo universitario guardaría en DynamoDB).

Ningún dato aquí corresponde a una persona real. Las universidades se nombran solo para ilustrar la federación.
"""


def _course(code: str, name: str, credits: int, grade: float | None, semester: str) -> dict:
    """grade None = asignatura en curso. Se aprueba con nota >= 3.0 (escala colombiana 0.0 a 5.0)."""
    if grade is None:
        status = "EN_CURSO"
    else:
        status = "APROBADA" if grade >= 3.0 else "REPROBADA"
    return {
        "code": code,
        "name": name,
        "credits": credits,
        "grade": grade,
        "status": status,
        "semester": semester,
    }


STUDENTS: dict[str, dict] = {
    # 1. Caso principal: estudiante activo del nodo Distrital (el del documento de requerimientos).
    "20262678029": {
        "student_id": "20262678029",
        "full_name": "Brayan Acosta Parrado",
        "university": "Universidad Distrital Francisco José de Caldas",
        "program": "Ingeniería en Telemática",
        "academic_status": "ACTIVO",
        "gpa": 4.52,
        "credits_completed": 140,
        "credits_total": 160,
        "courses": [
            _course("165-101", "Cálculo Diferencial", 3, 4.2, "2025-1"),
            _course("165-110", "Programación Orientada a Objetos", 3, 4.6, "2025-1"),
            _course("165-205", "Estructuras de Datos", 3, 4.4, "2025-2"),
            _course("165-220", "Redes de Computadores", 3, 4.7, "2025-2"),
            _course("165-301", "Sistemas Distribuidos", 3, 4.8, "2026-1"),
            _course("165-302", "Teoría General de Sistemas", 2, 4.5, "2026-1"),
            _course("165-315", "Bases de Datos", 3, 4.3, "2026-1"),
            _course("165-330", "Seguridad Informática", 3, None, "2026-2"),
        ],
    },
    # 2. Otro nodo (Nacional). Reprobó una materia y la repitió: caso típico para homologación.
    "20251234501": {
        "student_id": "20251234501",
        "full_name": "Laura Camila Ríos Herrera",
        "university": "Universidad Nacional de Colombia",
        "program": "Ingeniería de Sistemas y Computación",
        "academic_status": "ACTIVO",
        "gpa": 4.18,
        "credits_completed": 118,
        "credits_total": 160,
        "courses": [
            _course("2015167", "Cálculo Integral", 4, 2.6, "2024-2"),
            _course("2015170", "Física Mecánica", 4, 3.9, "2024-2"),
            _course("2016375", "Algoritmos", 3, 4.5, "2024-2"),
            _course("2015167", "Cálculo Integral", 4, 3.4, "2025-1"),
            _course("2016380", "Estructuras de Datos", 3, 4.3, "2025-1"),
            _course("1000003", "Álgebra Lineal", 3, 4.0, "2025-1"),
            _course("2016399", "Arquitectura de Computadores", 3, 4.6, "2025-2"),
            _course("2016412", "Bases de Datos", 3, 4.4, "2025-2"),
            _course("2016430", "Ingeniería de Software", 3, 4.7, "2026-1"),
            _course("2016441", "Sistemas Operativos", 3, 4.2, "2026-1"),
            _course("2016455", "Redes de Datos", 3, None, "2026-2"),
        ],
    },
    # 3. Egresado (nodo Javeriana): sirve para mostrar título y fecha de grado.
    "20241122002": {
        "student_id": "20241122002",
        "full_name": "Andrés Felipe Moreno Castro",
        "university": "Pontificia Universidad Javeriana",
        "program": "Ingeniería Electrónica",
        "academic_status": "GRADUADO",
        "degree": "Ingeniero Electrónico",
        "graduation_date": "2025-12-12",
        "gpa": 4.05,
        "credits_completed": 168,
        "credits_total": 168,
        "courses": [
            _course("IEL-701", "Control Digital", 3, 4.1, "2025-1"),
            _course("IEL-715", "Procesamiento de Señales", 4, 3.9, "2025-1"),
            _course("IEL-740", "Electiva en Robótica", 2, 4.5, "2025-1"),
            _course("IEL-760", "Instrumentación Industrial", 3, 4.0, "2025-2"),
            _course("IEL-799", "Proyecto de Grado", 6, 4.6, "2025-2"),
            _course("IEL-780", "Gerencia de Proyectos", 2, 4.2, "2025-2"),
        ],
    },
    # 4. Promedio alto (nodo Andes): candidata a beca o traslado.
    "20231098763": {
        "student_id": "20231098763",
        "full_name": "Valentina Torres Quintero",
        "university": "Universidad de los Andes",
        "program": "Economía",
        "academic_status": "ACTIVO",
        "gpa": 4.62,
        "credits_completed": 90,
        "credits_total": 140,
        "courses": [
            _course("ECON-2101", "Microeconomía II", 3, 4.8, "2025-1"),
            _course("ESTA-2201", "Estadística Inferencial", 3, 4.5, "2025-1"),
            _course("ECON-2130", "Historia Económica", 3, 4.9, "2025-1"),
            _course("ECON-2201", "Macroeconomía I", 3, 4.7, "2025-2"),
            _course("ECON-2310", "Econometría I", 4, 4.4, "2025-2"),
            _course("MATE-2105", "Cálculo Multivariable", 3, 4.6, "2025-2"),
            _course("ECON-3105", "Teoría de Juegos", 3, 4.9, "2026-1"),
            _course("ECON-3311", "Econometría II", 4, 4.5, "2026-1"),
            _course("ECON-3402", "Economía Pública", 3, None, "2026-2"),
        ],
    },
    # 5. Estudiante retirado (nodo Distrital): quiere cambiar de universidad; promedio bajo y materias repetidas.
    "20221050914": {
        "student_id": "20221050914",
        "full_name": "Juan Sebastián Pardo Gil",
        "university": "Universidad Distrital Francisco José de Caldas",
        "program": "Ingeniería Industrial",
        "academic_status": "RETIRADO",
        "gpa": 3.21,
        "credits_completed": 64,
        "credits_total": 160,
        "courses": [
            _course("170-101", "Cálculo Diferencial", 3, 3.1, "2024-1"),
            _course("170-105", "Física I", 3, 2.8, "2024-1"),
            _course("170-110", "Química General", 3, 3.5, "2024-1"),
            _course("170-201", "Cálculo Integral", 3, 3.0, "2024-2"),
            _course("170-105", "Física I", 3, 3.4, "2024-2"),
            _course("170-130", "Dibujo Técnico", 2, 3.8, "2024-2"),
            _course("170-240", "Estadística I", 3, 3.3, "2025-1"),
            _course("170-245", "Probabilidad", 3, 2.9, "2025-1"),
        ],
    },
    # 6. Primeros semestres (nodo Nacional), con asignaturas en curso.
    "20252345678": {
        "student_id": "20252345678",
        "full_name": "María Fernanda Ospina Duarte",
        "university": "Universidad Nacional de Colombia",
        "program": "Estadística",
        "academic_status": "ACTIVO",
        "gpa": 3.88,
        "credits_completed": 52,
        "credits_total": 150,
        "courses": [
            _course("1000004", "Cálculo I", 4, 3.7, "2025-1"),
            _course("1000012", "Introducción a la Estadística", 3, 4.2, "2025-1"),
            _course("1000021", "Lógica", 3, 4.0, "2025-1"),
            _course("1000005", "Cálculo II", 4, 3.5, "2025-2"),
            _course("1000033", "Probabilidad", 3, 3.9, "2025-2"),
            _course("1000040", "Programación en R", 3, 4.4, "2025-2"),
            _course("1000003", "Álgebra Lineal", 3, 3.6, "2026-1"),
            _course("1000052", "Inferencia Estadística", 3, 4.1, "2026-1"),
            _course("1000061", "Modelos Lineales", 3, None, "2026-2"),
        ],
    },
}
