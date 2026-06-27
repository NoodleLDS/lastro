from datetime import date

from pydantic import BaseModel

from lastro.models.dividend import Dividend

_LOOKBACK_MONTHS = 12


class ValuationResult(BaseModel):
    dividends_last_12m_cents: int
    price_ceiling_cents: int
    margin_of_safety_pct: float
    is_undervalued: bool


def calculate_valuation(
    dividends: list[Dividend],
    target_yield_pct: float | None,
    current_price_cents: int | None,
    today: date,
) -> ValuationResult | None:
    """Preço-teto via DY-alvo: preço que faria o dividendo dos últimos 12
    meses render exatamente `target_yield_pct` ao ano. Margem de segurança
    é a distância percentual entre o preço-teto e o preço atual.

    Sem preço atual, sem target_yield_pct ou sem dividendo nos últimos 12
    meses, retorna None — nunca chuta o número."""
    if current_price_cents is None or current_price_cents <= 0:
        return None
    if target_yield_pct is None or target_yield_pct <= 0:
        return None

    cutoff = date(today.year - 1, today.month, 1)
    recent = [d for d in dividends if d.date >= cutoff]
    if not recent:
        return None

    dividends_last_12m_cents = sum(d.amount_cents for d in recent)
    price_ceiling_cents = round(dividends_last_12m_cents / (target_yield_pct / 100))
    margin_of_safety_pct = (
        (price_ceiling_cents - current_price_cents) / current_price_cents * 100
    )

    return ValuationResult(
        dividends_last_12m_cents=dividends_last_12m_cents,
        price_ceiling_cents=price_ceiling_cents,
        margin_of_safety_pct=margin_of_safety_pct,
        is_undervalued=margin_of_safety_pct > 0,
    )
