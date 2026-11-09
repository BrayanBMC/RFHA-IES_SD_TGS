from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PENDING_STATUS = "PENDIENTE_APROBACION"
ACTIVE_STATUS = "ACTIVO"
NODE_ID_PATTERN = r"^IES-[A-F0-9]{8}$"


class NodeRegistration(BaseModel):
    """Datos que envía la universidad al solicitar su alta como nodo (HU-01)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nit: str = Field(pattern=r"^\d{6,12}(-\d)?$", examples=["899999063-3"])
    name: str = Field(min_length=3, max_length=200, examples=["Universidad Nacional de Colombia"])
    domain: str = Field(
        pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$",
        max_length=253,
        examples=["unal.edu.co"],
    )
    contact_email: str = Field(
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254, examples=["admisiones@unal.edu.co"]
    )

    @field_validator("domain", "contact_email", mode="before")
    @classmethod
    def to_lower(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class NodeRegistrationResponse(BaseModel):
    node_id: str
    status: str
    message: str


# ---------------------------------------------------------------- HU-02: aprobación del nodo


class NodeSummary(BaseModel):
    """Lo que ve el administrador de cada nodo. Nunca incluye la clave ni su hash."""

    node_id: str
    nit: str
    name: str
    domain: str
    contact_email: str
    status: str
    created_at: str


class NodeListResponse(BaseModel):
    nodes: list[NodeSummary]


class NodeApprovalResponse(BaseModel):
    node_id: str
    status: str
    api_key: str
    message: str


class ActiveNode(BaseModel):
    node_id: str
    name: str


class ActiveNodesResponse(BaseModel):
    nodes: list[ActiveNode]


# ---------------------------------------------------------------- HU-03: sincronización de historiales


class Course(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=20, examples=["165-301"])
    name: str = Field(min_length=1, max_length=150, examples=["Sistemas Distribuidos"])
    credits: int = Field(ge=0, le=20, examples=[3])
    grade: float | None = Field(default=None, ge=0, le=5, examples=[4.8])  # None = en curso
    semester: str = Field(pattern=r"^\d{4}-[1-3]$", examples=["2026-1"])


class StudentRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str = Field(pattern=r"^\d{6,15}$", examples=["20262678029"])
    document_number: str = Field(pattern=r"^\d{5,15}$", examples=["1012345678"])
    full_name: str = Field(min_length=3, max_length=200)
    program: str = Field(min_length=3, max_length=200)
    academic_status: Literal["ACTIVO", "GRADUADO", "RETIRADO"] = "ACTIVO"
    # Clave inicial del estudiante para el portal (HU-04). Solo se guarda su hash.
    password: str | None = Field(default=None, min_length=8, max_length=72)
    courses: list[Course] = Field(max_length=80)


class SyncRequest(BaseModel):
    records: list[StudentRecord] = Field(min_length=1, max_length=100)


class SyncResponse(BaseModel):
    node_id: str
    received: int
    created: int
    updated: int


# ---------------------------------------------------------------- HU-04 y HU-05: token del estudiante


class StudentCredentials(BaseModel):
    document_number: str = Field(pattern=r"^\d{5,15}$")
    password: str = Field(min_length=1, max_length=72)


class TokenRequest(StudentCredentials):
    target_node_id: str = Field(pattern=NODE_ID_PATTERN, examples=["IES-1A2B3C4D"])


class TokenResponse(BaseModel):
    student_auth_token: str
    jti: str
    audience: str
    origin: str
    expires_in: int
    expires_at: str


class TokenInfo(BaseModel):
    jti: str
    audience: str
    audience_name: str | None = None
    issued_at: str
    expires_at: str
    status: Literal["ACTIVO", "REVOCADO", "EXPIRADO"]


class TokenListResponse(BaseModel):
    tokens: list[TokenInfo]


class RevokeResponse(BaseModel):
    jti: str
    status: Literal["REVOCADO"]
    message: str


# ---------------------------------------------------------------- HU-09: auditoría e inmutabilidad


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    log_id: str
    timestamp: str
    consulting_node_id: str
    target_student_id: str
    origin_node_id: str | None = None
    outcome: Literal["SUCCESS", "DENIED", "ERROR"]
    reason: str | None = None
    data_source: Literal["Primary", "Replica", "None"] = "None"
    client_ip: str | None = None


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogEntry]
    total: int
