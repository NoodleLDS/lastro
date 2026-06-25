from datetime import date

import pytest

from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.sale import Sale
from lastro.services.analytics.total_return import calculate_total_return


def _contribution(quantity: float, unit_price_cents: int) -> Contribution:
    return Contribution(
        position_id=1, date=date(2026, 1, 1), quantity=quantity, unit_price_cents=unit_price_cents
    )


def _dividend(amount_cents: int) -> Dividend:
    return Dividend(position_id=1, date=date(2026, 1, 1), amount_cents=amount_cents)


def _sale(quantity: float, unit_price_cents: int) -> Sale:
    return Sale(
        position_id=1, date=date(2026, 2, 1), quantity=quantity, unit_price_cents=unit_price_cents
    )


def test_total_return_cenario_com_valores_conhecidos() -> None:
    contributions = [_contribution(200, 1800), _contribution(111, 2000)]
    dividends = [_dividend(15550)]

    result = calculate_total_return(contributions, dividends, current_price_cents=1986)

    assert result.invested_cents == 582000
    assert result.current_value_cents == 617646
    assert result.price_appreciation_cents == 35646
    assert result.dividends_received_cents == 15550
    assert result.total_return_cents == 51196
    assert result.total_return_pct == pytest.approx(8.7964, abs=1e-3)


def test_total_return_com_prejuizo_de_preco_mas_provento_positivo() -> None:
    contributions = [_contribution(100, 2000)]
    dividends = [_dividend(5000)]

    result = calculate_total_return(contributions, dividends, current_price_cents=1500)

    assert result.invested_cents == 200000
    assert result.current_value_cents == 150000
    assert result.price_appreciation_cents == -50000
    assert result.dividends_received_cents == 5000
    assert result.total_return_cents == -45000
    assert result.total_return_pct == pytest.approx(-22.5, abs=1e-3)


def test_total_return_sem_aportes_retorna_zero_por_cento() -> None:
    result = calculate_total_return([], [], current_price_cents=1000)

    assert result.invested_cents == 0
    assert result.total_return_pct == 0.0


def test_total_return_com_venda_parcial_considera_quantidade_restante() -> None:
    # comprou 100 cotas a R$20, vendeu 40 a R$25 -> sobram 60 a custo médio R$20
    contributions = [_contribution(100, 2000)]
    sales = [_sale(40, 2500)]

    result = calculate_total_return(
        contributions, dividends=[], current_price_cents=2200, sales=sales
    )

    # 60 cotas restantes: custo 60*2000=120000, valor atual 60*2200=132000
    assert result.invested_cents == 120000
    assert result.current_value_cents == 132000
    assert result.price_appreciation_cents == 12000
    # lucro realizado na venda: 40 * (2500 - 2000) = 20000
    assert result.realized_gain_cents == 20000
    assert result.total_return_cents == 32000  # 12000 + 0 (dividendos) + 20000


def test_total_return_com_venda_no_prejuizo_reduz_resultado() -> None:
    contributions = [_contribution(100, 2000)]
    sales = [_sale(40, 1500)]  # vendeu abaixo do custo médio

    result = calculate_total_return(
        contributions, dividends=[], current_price_cents=2200, sales=sales
    )

    # prejuízo realizado: 40 * (1500 - 2000) = -20000
    assert result.realized_gain_cents == -20000
