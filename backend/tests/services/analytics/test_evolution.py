from datetime import date

import pytest

from lastro.models.price_snapshot import PriceSnapshot
from lastro.services.analytics.evolution import (
    calculate_benchmark_comparison,
    calculate_portfolio_evolution,
)


def _snapshot(month: date, portfolio_value_cents: int) -> PriceSnapshot:
    return PriceSnapshot(
        month=month,
        portfolio_value_cents=portfolio_value_cents,
        emergency_reserve_value_cents=0,
    )


def test_evolucao_ordena_por_mes() -> None:
    snapshots = [
        _snapshot(date(2026, 3, 1), 110_000_00),
        _snapshot(date(2026, 1, 1), 100_000_00),
        _snapshot(date(2026, 2, 1), 105_000_00),
    ]

    points = calculate_portfolio_evolution(snapshots)

    assert [p.month for p in points] == [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
    assert [p.portfolio_value_cents for p in points] == [100_000_00, 105_000_00, 110_000_00]


def test_comparativo_retorna_none_com_menos_de_dois_snapshots() -> None:
    result = calculate_benchmark_comparison(
        [_snapshot(date(2026, 1, 1), 100_000_00)],
        cdi_accumulated_pct=2.0,
        ivvb11_first_price_cents=None,
        ivvb11_current_price_cents=None,
    )

    assert result is None


def test_comparativo_calcula_retorno_percentual_da_carteira_e_benchmarks() -> None:
    snapshots = [
        _snapshot(date(2026, 1, 1), 100_000_00),
        _snapshot(date(2026, 3, 1), 110_000_00),
    ]

    result = calculate_benchmark_comparison(
        snapshots,
        cdi_accumulated_pct=2.4,
        ivvb11_first_price_cents=40000,
        ivvb11_current_price_cents=43000,
    )

    assert result is not None
    assert result.portfolio_return_pct == pytest.approx(10.0)
    assert result.cdi_return_pct == pytest.approx(2.4)
    assert result.ivvb11_return_pct == pytest.approx(7.5)


def test_comparativo_sem_ivvb11_retorna_none_apenas_nesse_campo() -> None:
    snapshots = [
        _snapshot(date(2026, 1, 1), 100_000_00),
        _snapshot(date(2026, 2, 1), 105_000_00),
    ]

    result = calculate_benchmark_comparison(
        snapshots,
        cdi_accumulated_pct=1.0,
        ivvb11_first_price_cents=None,
        ivvb11_current_price_cents=None,
    )

    assert result is not None
    assert result.ivvb11_return_pct is None
