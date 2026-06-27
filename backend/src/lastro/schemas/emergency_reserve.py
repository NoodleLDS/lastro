from pydantic import BaseModel, ConfigDict


class EmergencyReserveCreate(BaseModel):
    institution: str
    balance_cents: int
    cdi_percentage: float


class EmergencyReserveUpdate(BaseModel):
    institution: str | None = None
    balance_cents: int | None = None
    cdi_percentage: float | None = None


class EmergencyReserveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: str
    balance_cents: int
    cdi_percentage: float
