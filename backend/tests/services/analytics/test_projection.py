import pytest

from lastro.services.analytics.projection import project_portfolio_value


def test_projecao_com_aporte_mensal_bate_com_formula_de_juros_compostos() -> None:
    values = project_portfolio_value(
        current_value_cents=5_000_000,
        monthly_contribution_cents=300_000,
        monthly_return_rate=0.008,
        months=12,
    )

    assert len(values) == 13
    assert values[0] == 5_000_000
    assert values[12] == pytest.approx(9_264_394, abs=50)


def test_projecao_sem_aporte_e_sem_retorno_mantem_valor_constante() -> None:
    values = project_portfolio_value(
        current_value_cents=1_000_000,
        monthly_contribution_cents=0,
        monthly_return_rate=0.0,
        months=6,
    )

    assert all(v == 1_000_000 for v in values)


def test_projecao_com_zero_meses_retorna_apenas_valor_atual() -> None:
    values = project_portfolio_value(
        current_value_cents=1_000_000,
        monthly_contribution_cents=300_000,
        monthly_return_rate=0.008,
        months=0,
    )

    assert values == [1_000_000]
