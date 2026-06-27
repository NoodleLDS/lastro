from datetime import date

from lastro.models.contribution import Contribution
from lastro.models.stock_split import StockSplit
from lastro.services.portfolio.stock_split import adjust_for_splits


def _contribution(d: date, quantity: float, unit_price_cents: int) -> Contribution:
    return Contribution(position_id=1, date=d, quantity=quantity, unit_price_cents=unit_price_cents)


def _split(d: date, ratio_from: float, ratio_to: float) -> StockSplit:
    return StockSplit(position_id=1, date=d, ratio_from=ratio_from, ratio_to=ratio_to)


def test_split_dobra_quantidade_e_divide_preco_de_eventos_anteriores() -> None:
    contributions = [_contribution(date(2026, 1, 1), 100, 2000)]
    splits = [_split(date(2026, 3, 1), ratio_from=1, ratio_to=2)]

    adjusted = adjust_for_splits(contributions, splits)

    assert adjusted[0].quantity == 200
    assert adjusted[0].unit_price_cents == 1000


def test_split_nao_afeta_eventos_posteriores_a_data() -> None:
    contributions = [_contribution(date(2026, 4, 1), 100, 2000)]
    splits = [_split(date(2026, 3, 1), ratio_from=1, ratio_to=2)]

    adjusted = adjust_for_splits(contributions, splits)

    assert adjusted[0].quantity == 100
    assert adjusted[0].unit_price_cents == 2000


def test_grupamento_reduz_quantidade_e_aumenta_preco() -> None:
    contributions = [_contribution(date(2026, 1, 1), 100, 1000)]
    splits = [_split(date(2026, 3, 1), ratio_from=10, ratio_to=1)]

    adjusted = adjust_for_splits(contributions, splits)

    assert adjusted[0].quantity == 10
    assert adjusted[0].unit_price_cents == 10000


def test_splits_consecutivos_compoem_fatores() -> None:
    contributions = [_contribution(date(2026, 1, 1), 100, 4000)]
    splits = [
        _split(date(2026, 2, 1), ratio_from=1, ratio_to=2),
        _split(date(2026, 3, 1), ratio_from=1, ratio_to=2),
    ]

    adjusted = adjust_for_splits(contributions, splits)

    assert adjusted[0].quantity == 400
    assert adjusted[0].unit_price_cents == 1000


def test_valor_total_investido_preservado_apos_split() -> None:
    contributions = [_contribution(date(2026, 1, 1), 100, 2000)]
    splits = [_split(date(2026, 3, 1), ratio_from=1, ratio_to=2)]

    adjusted = adjust_for_splits(contributions, splits)

    assert adjusted[0].quantity * adjusted[0].unit_price_cents == 100 * 2000
