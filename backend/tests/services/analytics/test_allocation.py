import pytest

from lastro.models.allocation_target import AllocationTarget
from lastro.models.position import AssetType, Position
from lastro.services.analytics.allocation import calculate_allocation


def _position(asset_type: AssetType, quantity: float, price_cents: int) -> Position:
    return Position(
        ticker=f"{asset_type}-test",
        name="teste",
        asset_type=asset_type,
        quantity=quantity,
        last_price_cents=price_cents,
    )


def test_alocacao_com_desvio_acima_do_threshold_gera_alerta() -> None:
    positions = [
        _position(AssetType.STOCK, 1, 3_000_000),  # R$30.000
        _position(AssetType.FII, 1, 5_000_000),  # R$50.000
    ]
    targets = [
        AllocationTarget(asset_type=AssetType.STOCK, target_percentage=30.0),
        AllocationTarget(asset_type=AssetType.FII, target_percentage=70.0),
    ]

    breakdown = calculate_allocation(positions, targets)
    by_type = {b.asset_type: b for b in breakdown}

    assert by_type[AssetType.STOCK].current_percentage == pytest.approx(37.5)
    assert by_type[AssetType.FII].current_percentage == pytest.approx(62.5)
    assert by_type[AssetType.STOCK].deviation_pct == pytest.approx(7.5)
    assert by_type[AssetType.FII].deviation_pct == pytest.approx(-7.5)
    assert by_type[AssetType.STOCK].is_deviation_alert is True
    assert by_type[AssetType.FII].is_deviation_alert is True


def test_alocacao_com_desvio_abaixo_do_threshold_nao_gera_alerta() -> None:
    positions = [
        _position(AssetType.STOCK, 1, 3_000_000),  # 37.5% real
        _position(AssetType.FII, 1, 5_000_000),  # 62.5% real
    ]
    targets = [
        AllocationTarget(asset_type=AssetType.STOCK, target_percentage=35.0),  # desvio 2.5pp
        AllocationTarget(asset_type=AssetType.FII, target_percentage=65.0),  # desvio -2.5pp
    ]

    breakdown = calculate_allocation(positions, targets)
    by_type = {b.asset_type: b for b in breakdown}

    assert by_type[AssetType.STOCK].is_deviation_alert is False
    assert by_type[AssetType.FII].is_deviation_alert is False


def test_alocacao_ignora_posicoes_sem_cotacao() -> None:
    positions = [
        _position(AssetType.STOCK, 1, 3_000_000),
        Position(ticker="sem-cotacao", name="t", asset_type=AssetType.FII, quantity=10),
    ]

    breakdown = calculate_allocation(positions, [])

    assert len(breakdown) == 1
    assert breakdown[0].asset_type == AssetType.STOCK
    assert breakdown[0].current_percentage == 100.0


def test_alocacao_sem_meta_retorna_deviation_none() -> None:
    positions = [_position(AssetType.STOCK, 1, 3_000_000)]

    breakdown = calculate_allocation(positions, [])

    assert breakdown[0].target_percentage is None
    assert breakdown[0].deviation_pct is None
    assert breakdown[0].is_deviation_alert is False
