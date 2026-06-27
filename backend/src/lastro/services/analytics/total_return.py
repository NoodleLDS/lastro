from pydantic import BaseModel

from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.sale import Sale
from lastro.models.stock_split import StockSplit
from lastro.services.portfolio.stock_split import adjust_for_splits


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
    splits: list[StockSplit] | None = None,
) -> TotalReturnResult:
    """Total return = (valor atual das cotas restantes - custo dessas cotas)
    + proventos recebidos + lucro/perda realizado nas vendas.

    Nunca apenas (atual - custo) / custo: proventos sempre entram na conta,
    mesmo quando a valorização de preço é negativa. Vender não altera o
    preço médio das cotas remanescentes — só realiza o resultado das cotas
    que saíram, calculado sobre esse mesmo preço médio. Splits ajustam
    quantidade/preço dos eventos anteriores à data do desdobramento, sem
    alterar o valor total investido.
    """
    sales = sales or []
    splits = splits or []

    contribution_events = adjust_for_splits(contributions, splits)
    sale_events = adjust_for_splits(sales, splits)

    bought_quantity = sum(e.quantity for e in contribution_events)
    invested_total_cents = sum(e.quantity * e.unit_price_cents for e in contribution_events)
    average_price_cents = invested_total_cents / bought_quantity if bought_quantity else 0.0

    sold_quantity = sum(e.quantity for e in sale_events)
    remaining_quantity = bought_quantity - sold_quantity

    invested_cents = round(remaining_quantity * average_price_cents)
    current_value_cents = round(remaining_quantity * current_price_cents)
    price_appreciation_cents = current_value_cents - invested_cents

    realized_gain_cents = round(
        sum(e.quantity * (e.unit_price_cents - average_price_cents) for e in sale_events)
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
