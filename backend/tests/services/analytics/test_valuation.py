from datetime import date

from lastro.models.dividend import Dividend
from lastro.services.analytics.valuation import calculate_valuation


def _dividend(year: int, month: int, amount_cents: int) -> Dividend:
    return Dividend(position_id=1, date=date(year, month, 1), amount_cents=amount_cents)


def test_subvalorizado_quando_preco_atual_abaixo_do_preco_teto() -> None:
    # dividendo anual R$120, DY-alvo 10% -> preço-teto R$1200; preço atual R$1000
    dividends = [_dividend(2025, m, 1000) for m in range(7, 13)] + [
        _dividend(2026, m, 1000) for m in range(1, 7)
    ]

    result = calculate_valuation(
        dividends, target_yield_pct=10.0, current_price_cents=100_000, today=date(2026, 6, 25)
    )

    assert result is not None
    assert result.dividends_last_12m_cents == 12_000
    assert result.price_ceiling_cents == 120_000
    assert result.margin_of_safety_pct == 20.0
    assert result.is_undervalued is True


def test_sobrevalorizado_quando_preco_atual_acima_do_preco_teto() -> None:
    dividends = [_dividend(2026, m, 1000) for m in range(1, 7)]

    result = calculate_valuation(
        dividends, target_yield_pct=10.0, current_price_cents=200_000, today=date(2026, 6, 25)
    )

    assert result is not None
    assert result.is_undervalued is False
    assert result.margin_of_safety_pct < 0


def test_retorna_none_sem_target_yield() -> None:
    dividends = [_dividend(2026, m, 1000) for m in range(1, 7)]

    result = calculate_valuation(
        dividends, target_yield_pct=None, current_price_cents=100_000, today=date(2026, 6, 25)
    )

    assert result is None


def test_retorna_none_sem_preco_atual() -> None:
    dividends = [_dividend(2026, m, 1000) for m in range(1, 7)]

    result = calculate_valuation(
        dividends, target_yield_pct=10.0, current_price_cents=None, today=date(2026, 6, 25)
    )

    assert result is None


def test_retorna_none_sem_dividendo_nos_ultimos_12_meses() -> None:
    dividends = [_dividend(2023, 1, 1000)]

    result = calculate_valuation(
        dividends, target_yield_pct=10.0, current_price_cents=100_000, today=date(2026, 6, 25)
    )

    assert result is None


def test_retorna_none_com_target_yield_zero_ou_negativo() -> None:
    dividends = [_dividend(2026, m, 1000) for m in range(1, 7)]

    result = calculate_valuation(
        dividends, target_yield_pct=0.0, current_price_cents=100_000, today=date(2026, 6, 25)
    )

    assert result is None
