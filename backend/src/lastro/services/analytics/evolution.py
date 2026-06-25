from datetime import date

from pydantic import BaseModel

from lastro.models.price_snapshot import PriceSnapshot


class EvolutionPoint(BaseModel):
    month: date
    portfolio_value_cents: int


class BenchmarkComparison(BaseModel):
    portfolio_return_pct: float
    cdi_return_pct: float
    ivvb11_return_pct: float | None


def calculate_portfolio_evolution(snapshots: list[PriceSnapshot]) -> list[EvolutionPoint]:
    ordered = sorted(snapshots, key=lambda s: s.month)
    return [
        EvolutionPoint(month=snapshot.month, portfolio_value_cents=snapshot.portfolio_value_cents)
        for snapshot in ordered
    ]


def calculate_benchmark_comparison(
    snapshots: list[PriceSnapshot],
    cdi_accumulated_pct: float,
    ivvb11_first_price_cents: int | None,
    ivvb11_current_price_cents: int | None,
) -> BenchmarkComparison | None:
    """Compara o retorno % da carteira (entre o primeiro e o último
    snapshot) com o CDI acumulado e o IVVB11 no mesmo período. Retorna None
    se não houver pelo menos 2 snapshots (sem período pra comparar)."""
    ordered = sorted(snapshots, key=lambda s: s.month)
    if len(ordered) < 2:
        return None

    first, last = ordered[0], ordered[-1]
    portfolio_return_pct = (
        (last.portfolio_value_cents - first.portfolio_value_cents)
        / first.portfolio_value_cents
        * 100
        if first.portfolio_value_cents
        else 0.0
    )

    ivvb11_return_pct = None
    if ivvb11_first_price_cents is not None and ivvb11_current_price_cents is not None:
        ivvb11_return_pct = (
            (ivvb11_current_price_cents - ivvb11_first_price_cents) / ivvb11_first_price_cents * 100
            if ivvb11_first_price_cents
            else 0.0
        )

    return BenchmarkComparison(
        portfolio_return_pct=portfolio_return_pct,
        cdi_return_pct=cdi_accumulated_pct,
        ivvb11_return_pct=ivvb11_return_pct,
    )
