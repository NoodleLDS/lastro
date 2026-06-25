import pytest

from lastro.services.analytics.fire import calculate_dividend_yield_pct, calculate_fire


def test_dividend_yield_calculado_corretamente() -> None:
    yield_pct = calculate_dividend_yield_pct(
        dividends_last_12m_cents=4_000_00, portfolio_value_cents=80_000_00
    )

    assert yield_pct == pytest.approx(5.0)


def test_dividend_yield_zero_quando_sem_patrimonio() -> None:
    assert (
        calculate_dividend_yield_pct(dividends_last_12m_cents=100, portfolio_value_cents=0) == 0.0
    )


def test_fire_ainda_nao_atingiu_o_alvo_calcula_quanto_falta() -> None:
    result = calculate_fire(
        portfolio_value_cents=80_000_00,
        dividend_yield_pct=8.0,
        ipca_pct=4.0,
        target_monthly_expense_cents=500_00,
    )

    # taxa de retirada segura = 4% a.a. -> renda mensal sustentável hoje:
    # 8_000_000 * 0.04 / 12 = 26_666.67 -> round = 26667 cents = R$266,67
    assert result.safe_withdrawal_rate_pct == pytest.approx(4.0)
    assert result.sustainable_monthly_income_cents == 26667
    assert result.has_reached_target is False
    # patrimônio necessário = 500_00*12 / 0.04 = 150_000_00
    assert result.required_portfolio_cents == 150_000_00
    assert result.missing_portfolio_cents == 70_000_00


def test_fire_ja_atingiu_o_alvo() -> None:
    result = calculate_fire(
        portfolio_value_cents=200_000_00,
        dividend_yield_pct=8.0,
        ipca_pct=4.0,
        target_monthly_expense_cents=500_00,
    )

    assert result.has_reached_target is True
    assert result.missing_portfolio_cents == 0


def test_fire_taxa_de_retirada_negativa_nao_calcula_patrimonio_necessario() -> None:
    result = calculate_fire(
        portfolio_value_cents=80_000_00,
        dividend_yield_pct=2.0,
        ipca_pct=4.0,
        target_monthly_expense_cents=500_00,
    )

    assert result.safe_withdrawal_rate_pct == pytest.approx(-2.0)
    assert result.required_portfolio_cents is None
    assert result.missing_portfolio_cents is None
    assert result.has_reached_target is False
