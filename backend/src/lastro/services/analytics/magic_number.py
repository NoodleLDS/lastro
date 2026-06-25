from datetime import date

from pydantic import BaseModel

from lastro.models.dividend import Dividend

_LOOKBACK_MONTHS = 12


class MagicNumberResult(BaseModel):
    average_monthly_dividend_cents: int
    shares_bought_per_month: float
    is_achieved: bool


def calculate_magic_number(
    dividends: list[Dividend], current_price_cents: int, today: date
) -> MagicNumberResult | None:
    """Número mágico: quando os proventos médios mensais (últimos 12 meses)
    já compram >= 1 cota/ação no preço atual. Retorna None sem dado
    suficiente (sem preço atual ou sem dividendo no período)."""
    if current_price_cents <= 0:
        return None

    cutoff = date(today.year - 1, today.month, 1)
    recent = [d for d in dividends if d.date >= cutoff]
    if not recent:
        return None

    months_with_data = {(d.date.year, d.date.month) for d in recent}
    divisor = min(len(months_with_data), _LOOKBACK_MONTHS)

    total_cents = sum(d.amount_cents for d in recent)
    average_monthly_dividend_cents = round(total_cents / divisor)
    shares_bought_per_month = average_monthly_dividend_cents / current_price_cents

    return MagicNumberResult(
        average_monthly_dividend_cents=average_monthly_dividend_cents,
        shares_bought_per_month=shares_bought_per_month,
        is_achieved=shares_bought_per_month >= 1.0,
    )
