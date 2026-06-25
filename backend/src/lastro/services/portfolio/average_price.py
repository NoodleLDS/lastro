from lastro.models.contribution import Contribution


def calculate_average_price_cents(contributions: list[Contribution]) -> int:
    """Preço médio ponderado pelos aportes. Retorna 0 se não houver aportes."""
    total_quantity = sum(c.quantity for c in contributions)
    if total_quantity == 0:
        return 0

    total_cost_cents = sum(c.quantity * c.unit_price_cents for c in contributions)
    return round(total_cost_cents / total_quantity)
