from datetime import date as date_

from pydantic import BaseModel, ConfigDict

from lastro.models.transaction import CategorizedBy, TransactionSource, TransactionStatus


class QuickEntryCreate(BaseModel):
    card_id: int
    raw: str
    date: date_


class TransactionUpdate(BaseModel):
    description: str | None = None
    amount_cents: int | None = None
    category_id: int | None = None
    date: date_ | None = None
    installment_current: int | None = None
    installment_total: int | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_
    description: str
    amount_cents: int
    card_id: int
    category_id: int | None
    categorized_by: CategorizedBy
    source: TransactionSource
    status: TransactionStatus
    installment_current: int | None
    installment_total: int | None
    parent_id: int | None


class QuickEntryResult(BaseModel):
    transaction: TransactionRead
    installments: list[TransactionRead]


class ConfirmBatchRequest(BaseModel):
    ids: list[int]


class CategorizationStats(BaseModel):
    total: int
    by_rule: int
    by_llm: int
    by_manual: int
    uncategorized: int
    resolved_without_ai_pct: float | None
