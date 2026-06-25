from datetime import date

from lastro.models.contribution import Contribution
from lastro.services.portfolio.average_price import calculate_average_price_cents


def _contribution(quantity: float, unit_price_cents: int) -> Contribution:
    return Contribution(
        position_id=1, date=date(2026, 1, 1), quantity=quantity, unit_price_cents=unit_price_cents
    )


def test_preco_medio_ponderado_com_multiplos_aportes() -> None:
    contributions = [
        _contribution(200, 1800),
        _contribution(111, 2000),
    ]

    assert calculate_average_price_cents(contributions) == 1871


def test_preco_medio_zero_sem_aportes() -> None:
    assert calculate_average_price_cents([]) == 0


def test_preco_medio_com_um_unico_aporte() -> None:
    contributions = [_contribution(10, 5000)]

    assert calculate_average_price_cents(contributions) == 5000
