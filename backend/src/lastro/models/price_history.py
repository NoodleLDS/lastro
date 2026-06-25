from datetime import date

from sqlmodel import Field, SQLModel


class PriceHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    position_id: int = Field(foreign_key="position.id", index=True)
    date: date
    price_cents: int
