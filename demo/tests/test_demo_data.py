import pytest
from fastapi.testclient import TestClient

from demo import main
from demo.students import STUDENTS
from demo.tests.test_demo_api import make_token

client = TestClient(main.app)
URL = "/api/v1/federated/academic-history/{}"


def consult(student_id, token=None):
    headers = {"X-Student-Consent-Token": token} if token else {}
    return client.get(URL.format(student_id), headers=headers)


def test_hay_seis_estudiantes_en_cuatro_universidades():
    assert len(STUDENTS) == 6
    assert len({s["university"] for s in STUDENTS.values()}) == 4


@pytest.mark.parametrize("student_id", list(STUDENTS))
def test_cada_estudiante_se_consulta_con_su_token(student_id):
    response = consult(student_id, make_token(student_id=student_id))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_id"] == student_id
    assert data["academic_status"] in {"ACTIVO", "GRADUADO", "RETIRADO"}
    assert data["credits_completed"] <= data["credits_total"]
    assert data["courses"], "debe tener asignaturas"


@pytest.mark.parametrize("student_id", list(STUDENTS))
def test_el_token_de_un_estudiante_no_abre_a_otro(student_id):
    other = next(s for s in STUDENTS if s != student_id)
    assert consult(student_id, make_token(student_id=other)).status_code == 403


@pytest.mark.parametrize("student_id", list(STUDENTS))
def test_estados_de_asignaturas_son_coherentes_con_la_nota(student_id):
    for course in STUDENTS[student_id]["courses"]:
        if course["grade"] is None:
            assert course["status"] == "EN_CURSO"
        elif course["grade"] >= 3.0:
            assert course["status"] == "APROBADA"
        else:
            assert course["status"] == "REPROBADA"
        assert 0 <= (course["grade"] or 0) <= 5


def test_el_graduado_tiene_titulo_y_fecha_de_grado():
    data = STUDENTS["20241122002"]
    assert data["academic_status"] == "GRADUADO"
    assert data["degree"] and data["graduation_date"]
    assert data["credits_completed"] == data["credits_total"]


def test_hay_casos_de_reprobada_y_en_curso():
    statuses = {c["status"] for s in STUDENTS.values() for c in s["courses"]}
    assert statuses == {"APROBADA", "REPROBADA", "EN_CURSO"}


def test_lista_de_estudiantes_solo_en_modo_demo(monkeypatch):
    monkeypatch.setattr(main, "DEMO_MODE", False)
    assert client.get("/api/v1/demo/students").status_code == 404
    monkeypatch.setattr(main, "DEMO_MODE", True)
    response = client.get("/api/v1/demo/students")
    assert response.status_code == 200
    assert len(response.json()) == 6
    assert set(response.json()[0]) == {"student_id", "full_name", "university", "academic_status"}
