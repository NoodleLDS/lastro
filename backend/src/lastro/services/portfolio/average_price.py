from lastro.models.contribution import Contribution
from lastro.models.stock_split import StockSplit
from lastro.services.portfolio.stock_split import adjust_for_splits


def calculate_average_price_cents(
    contributions: list[Contribution], splits: list[StockSplit] | None = None
) -> int:
    """Preço médio ponderado pelos aportes. Retorna 0 se não houver aportes."""
    events = adjust_for_splits(contributions, splits or [])

    total_quantity = sum(e.quantity for e in events)
    if total_quantity == 0:
        return 0

    total_cost_cents = sum(e.quantity * e.unit_price_cents for e in events)
    return round(total_cost_cents / total_quantity)
