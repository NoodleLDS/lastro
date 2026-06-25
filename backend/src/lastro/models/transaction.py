from datetime import UTC, date, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class TransactionSource(StrEnum):
    MANUAL = "manual"
    VISION_PREVIEW = "vision_preview"


class TransactionStatus(StrEnum):
    CONFIRMED = "confirmed"
    PENDING_REVIEW = "pending_review"


class CategorizedBy(StrEnum):
    RULE = "rule"
    LLM = "llm"
    MANUAL = "manual"
    NONE = "none"


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    description: str
    amount_cents: int
    card_id: int = Field(foreign_key="card.id", index=True)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    categorized_by: CategorizedBy = Field(default=CategorizedBy.NONE)
    source: TransactionSource = Field(default=TransactionSource.MANUAL)
    status: TransactionStatus = Field(default=TransactionStatus.CONFIRMED)
    installment_current: int | None = Field(default=None)
    installment_total: int | None = Field(default=None)
    parent_id: int | None = Field(default=None, foreign_key="transaction.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
