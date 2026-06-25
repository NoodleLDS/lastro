from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


class PriceSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    month: date = Field(index=True, unique=True)
    portfolio_value_cents: int
    emergency_reserve_value_cents: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
