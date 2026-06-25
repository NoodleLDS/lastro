from typing import Protocol

from pydantic import BaseModel


class Quote(BaseModel):
    ticker: str
    price_cents: int
    price_earnings: float | None = None
    earnings_per_share: float | None = None


class QuoteProvider(Protocol):
    async def get_quote(self, ticker: str) -> Quote: ...
