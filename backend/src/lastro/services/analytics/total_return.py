from pydantic import BaseModel

from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.sale import Sale


class TotalReturnResult(BaseModel):
    invested_cents: int
    current_value_cents: int
    price_appreciation_cents: int
    dividends_received_cents: int
    realized_gain_cents: int
    total_return_cents: int
    total_return_pct: float


def calculate_total_return(
    contributions: list[Contribution],
    dividends: list[Dividend],
    current_price_cents: int,
    sales: list[Sale] | None = None,
) -> TotalReturnResult:
    """Total return = (valor atual das cotas restantes - custo dessas cotas)
    + proventos recebidos + lucro/perda realizado nas vendas.

    Nunca apenas (atual - custo) / custo: proventos sempre entram na conta,
    mesmo quando a valorização de preço é negativa. Vender não altera o
    preço médio das cotas remanescentes — só realiza o resultado das cotas
    que saíram, calculado sobre esse mesmo preço médio.
    """
    sales = sales or []

    bought_quantity = sum(c.quantity for c in contributions)
    invested_total_cents = sum(c.quantity * c.unit_price_cents for c in contributions)
    average_price_cents = invested_total_cents / bought_quantity if bought_quantity else 0.0

    sold_quantity = sum(s.quantity for s in sales)
    remaining_quantity = bought_quantity - sold_quantity

    invested_cents = round(remaining_quantity * average_price_cents)
    current_value_cents = round(remaining_quantity * current_price_cents)
    price_appreciation_cents = current_value_cents - invested_cents

    realized_gain_cents = round(
        sum(s.quantity * (s.unit_price_cents - average_price_cents) for s in sales)
    )

    dividends_received_cents = sum(d.amount_cents for d in dividends)
    total_return_cents = price_appreciation_cents + dividends_received_cents + realized_gain_cents
    total_invested_for_pct_cents = round(bought_quantity * average_price_cents)
    total_return_pct = (
        (total_return_cents / total_invested_for_pct_cents * 100)
        if total_invested_for_pct_cents
        else 0.0
    )

    return TotalReturnResult(
        invested_cents=invested_cents,
        current_value_cents=current_value_cents,
        price_appreciation_cents=price_appreciation_cents,
        dividends_received_cents=dividends_received_cents,
        realized_gain_cents=realized_gain_cents,
        total_return_cents=total_return_cents,
        total_return_pct=total_return_pct,
    )
