from datetime import UTC, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


class CardInvoicePayment(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("card_id", "year", "month"),)

    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True)
    year: int = Field(index=True)
    month: int = Field(index=True)
    paid_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
