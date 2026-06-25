from datetime import date

from sqlmodel import Field, SQLModel


class Dividend(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    position_id: int = Field(foreign_key="position.id", index=True)
    date: date
    amount_cents: int
