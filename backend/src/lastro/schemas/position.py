from datetime import date as date_
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from lastro.models.position import AssetType
from lastro.services.analytics.magic_number import MagicNumberResult
from lastro.services.analytics.total_return import TotalReturnResult
from lastro.services.analytics.valuation import ValuationResult


class PositionCreate(BaseModel):
    ticker: str
    name: str
    asset_type: AssetType


class PositionUpdate(BaseModel):
    target_yield_pct: float | None = None


class PositionRead(BaseModel):
    id: int
    ticker: str
    name: str
    asset_type: AssetType
    quantity: float
    is_active: bool
    average_price_cents: int
    last_price_cents: int | None = None
    last_price_fetched_at: datetime | None = None
    price_earnings: float | None = None
    earnings_per_share: float | None = None
    target_yield_pct: float | None = None
    total_return: TotalReturnResult | None = None
    magic_number: MagicNumberResult | None = None
    valuation: ValuationResult | None = None


class PositionEventType(StrEnum):
    CONTRIBUTION = "contribution"
    SALE = "sale"
    DIVIDEND = "dividend"
    STOCK_SPLIT = "stock_split"


class PositionEvent(BaseModel):
    type: PositionEventType
    date: date_
    quantity: float | None = None
    unit_price_cents: int | None = None
    amount_cents: int | None = None
    ratio_from: float | None = None
    ratio_to: float | None = None


class PricePoint(BaseModel):
    date: date_
    price_cents: int


class PositionHistory(BaseModel):
    events: list[PositionEvent]
    price_history: list[PricePoint]
