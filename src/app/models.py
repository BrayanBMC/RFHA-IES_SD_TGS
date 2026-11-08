from pydantic import BaseModel, ConfigDict, Field, field_validator

PENDING_STATUS = "PENDIENTE_APROBACION"


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
