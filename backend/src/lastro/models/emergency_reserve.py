from sqlmodel import Field, SQLModel


class EmergencyReserve(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    institution: str
    balance_cents: int
    cdi_percentage: float
