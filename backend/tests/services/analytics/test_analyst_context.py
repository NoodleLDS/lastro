from datetime import date

from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.allocation_target import AllocationTarget
from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.position import AssetType, Position
from lastro.services.analytics.analyst_context import build_portfolio_context


async def _create_position(
    session: AsyncSession,
    ticker: str,
    asset_type: AssetType,
    quantity: float = 100,
    last_price_cents: int | None = None,
    roe_percentage: float | None = None,
    price_earnings: float | None = None,
    target_yield_pct: float | None = None,
) -> Position:
    position = Position(
        ticker=ticker,
        name=ticker,
        asset_type=asset_type,
        quantity=quantity,
        last_price_cents=last_price_cents,
        roe_percentage=roe_percentage,
        price_earnings=price_earnings,
        target_yield_pct=target_yield_pct,
    )
    session.add(position)
    await session.flush()
    return position


async def test_contexto_inclui_ticker_quantidade_e_preco_medio(session: AsyncSession) -> None:
    position = await _create_position(session, "CPTS11", AssetType.FII)
    session.add(
        Contribution(
            position_id=position.id, date=date(2026, 1, 1), quantity=100, unit_price_cents=1000
        )
    )
    await session.flush()

    context = await build_portfolio_context(session)

    assert "CPTS11" in context
    assert "100" in context
    assert "10,00" in context


async def test_contexto_sem_preco_atual_nao_inclui_total_return(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, last_price_cents=None)

    context = await build_portfolio_context(session)

    assert "total return" not in context


async def test_contexto_com_preco_atual_inclui_total_return(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, last_price_cents=1100)

    context = await build_portfolio_context(session)

    assert "total return" in context


async def test_contexto_inclui_roe_e_price_earnings_quando_disponiveis(
    session: AsyncSession,
) -> None:
    await _create_position(
        session, "BBAS3", AssetType.STOCK, roe_percentage=16.5, price_earnings=9.0
    )

    context = await build_portfolio_context(session)

    assert "ROE 16.5%" in context
    assert "P/L 9.0" in context


async def test_contexto_inclui_valuation_quando_target_yield_definido(
    session: AsyncSession,
) -> None:
    position = await _create_position(
        session, "CPTS11", AssetType.FII, last_price_cents=1000, target_yield_pct=10.0
    )
    for month in range(1, 7):
        session.add(Dividend(position_id=position.id, date=date(2026, month, 1), amount_cents=100))
    await session.flush()

    context = await build_portfolio_context(session)

    assert "preço-teto" in context
    assert "margem de segurança" in context


async def test_contexto_omite_valuation_sem_target_yield(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, last_price_cents=1000)

    context = await build_portfolio_context(session)

    assert "preço-teto" not in context


async def test_contexto_inclui_alocacao_por_classe(session: AsyncSession) -> None:
    await _create_position(session, "CPTS11", AssetType.FII, last_price_cents=1000)
    session.add(AllocationTarget(asset_type=AssetType.FII, target_percentage=15.0))
    await session.flush()

    context = await build_portfolio_context(session)

    assert "fii" in context
    assert "meta 15.0%" in context
