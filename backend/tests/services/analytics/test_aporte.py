from datetime import date

from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.allocation_target import AllocationTarget
from lastro.models.contribution import Contribution
from lastro.models.position import AssetType, Position
from lastro.services.analytics.aporte import distribute_contribution


async def _create_position(
    session: AsyncSession,
    ticker: str,
    asset_type: AssetType,
    quantity: float = 10,
    price_cents: int = 10_000,
    roe_percentage: float | None = None,
) -> Position:
    position = Position(
        ticker=ticker,
        name=ticker,
        asset_type=asset_type,
        quantity=quantity,
        last_price_cents=price_cents,
        roe_percentage=roe_percentage,
    )
    session.add(position)
    await session.flush()
    return position


async def test_cpts_recebe_fatia_prioritaria_fixa(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII)

    preview = await distribute_contribution(session, total_cents=100_000)

    cpts_allocation = next(a for a in preview.allocations if a.ticker == "CPTS11")
    assert cpts_allocation.amount_cents == 25_000


async def test_bbas3_pausada_sem_roe_preenchido(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII)
    await _create_position(session, "BBAS3", AssetType.STOCK, roe_percentage=None)
    session.add(AllocationTarget(asset_type=AssetType.STOCK, target_percentage=90.0))
    await session.flush()

    preview = await distribute_contribution(session, total_cents=100_000)

    assert not any(a.ticker == "BBAS3" for a in preview.allocations)


async def test_bbas3_elegivel_quando_roe_acima_do_minimo(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, quantity=1000)
    await _create_position(session, "BBAS3", AssetType.STOCK, roe_percentage=16.0)
    session.add(AllocationTarget(asset_type=AssetType.STOCK, target_percentage=90.0))
    session.add(AllocationTarget(asset_type=AssetType.FII, target_percentage=10.0))
    await session.flush()

    preview = await distribute_contribution(session, total_cents=100_000)

    assert any(a.ticker == "BBAS3" for a in preview.allocations)


async def test_bbas3_pausada_quando_roe_abaixo_do_minimo(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, quantity=1000)
    await _create_position(session, "BBAS3", AssetType.STOCK, roe_percentage=10.0)
    session.add(AllocationTarget(asset_type=AssetType.STOCK, target_percentage=90.0))
    session.add(AllocationTarget(asset_type=AssetType.FII, target_percentage=10.0))
    await session.flush()

    preview = await distribute_contribution(session, total_cents=100_000)

    assert not any(a.ticker == "BBAS3" for a in preview.allocations)


async def test_tickers_excluidos_nunca_recebem_aporte(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII)
    await _create_position(session, "TESOURO_IPCA_2035", AssetType.FIXED_INCOME)
    await _create_position(session, "PSEC11", AssetType.FII)
    await _create_position(session, "IVVB11", AssetType.ETF)

    preview = await distribute_contribution(session, total_cents=100_000)

    excluded = {"TESOURO_IPCA_2035", "PSEC11", "IVVB11"}
    assert not any(a.ticker in excluded for a in preview.allocations)


async def test_rotacao_alterna_entre_xpml_e_hglg(session: AsyncSession) -> None:
    xpml = await _create_position(session, "XPML11", AssetType.FII)
    await _create_position(session, "HGLG11", AssetType.FII)
    await _create_position(session, "CPTS11", AssetType.FII)

    session.add(
        Contribution(
            position_id=xpml.id, date=date(2026, 5, 10), quantity=1, unit_price_cents=10_000
        )
    )
    await session.flush()

    preview = await distribute_contribution(session, total_cents=100_000)

    rotating_in_preview = [
        a.ticker for a in preview.allocations if a.ticker in ("XPML11", "HGLG11")
    ]
    assert rotating_in_preview == ["HGLG11"]


async def test_rotacao_sem_historico_usa_primeiro_ticker(session: AsyncSession) -> None:
    await _create_position(session, "XPML11", AssetType.FII)
    await _create_position(session, "HGLG11", AssetType.FII)
    await _create_position(session, "CPTS11", AssetType.FII)

    preview = await distribute_contribution(session, total_cents=100_000)

    rotating_in_preview = [
        a.ticker for a in preview.allocations if a.ticker in ("XPML11", "HGLG11")
    ]
    assert rotating_in_preview == ["XPML11"]


async def test_petr4_so_recebe_se_nao_houver_candidato_melhor(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, quantity=1000)
    await _create_position(session, "PETR4", AssetType.STOCK, quantity=1000)
    await _create_position(session, "BBAS3", AssetType.STOCK, roe_percentage=20.0)
    session.add(AllocationTarget(asset_type=AssetType.STOCK, target_percentage=90.0))
    session.add(AllocationTarget(asset_type=AssetType.FII, target_percentage=10.0))
    await session.flush()

    preview = await distribute_contribution(session, total_cents=100_000)

    stock_allocation = next(a for a in preview.allocations if a.ticker in ("PETR4", "BBAS3"))
    assert stock_allocation.ticker == "BBAS3"


async def test_total_distribuido_bate_com_valor_do_aporte(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII)
    await _create_position(session, "XPML11", AssetType.FII)
    await _create_position(session, "HGLG11", AssetType.FII)

    preview = await distribute_contribution(session, total_cents=100_000)

    assert sum(a.amount_cents for a in preview.allocations) == 100_000
