from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class AssetType(StrEnum):
    STOCK = "stock"
    FII = "fii"
    ETF = "etf"
    FIXED_INCOME = "fixed_income"
    CRYPTO = "crypto"


class Position(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    name: str
    asset_type: AssetType
    quantity: float = Field(default=0)
    is_active: bool = Field(default=True)
    last_price_cents: int | None = Field(default=None)
    last_price_fetched_at: datetime | None = Field(default=None)
    roe_percentage: float | None = Field(default=None)
    price_earnings: float | None = Field(default=None)
    earnings_per_share: float | None = Field(default=None)
    target_yield_pct: float | None = Field(default=None)
