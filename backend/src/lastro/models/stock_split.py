from datetime import date

from sqlmodel import Field, SQLModel


class StockSplit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    position_id: int = Field(foreign_key="position.id", index=True)
    date: date
    ratio_from: float
    ratio_to: float
