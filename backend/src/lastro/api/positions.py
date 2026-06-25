from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.position import AssetType, Position
from lastro.models.price_history import PriceHistory
from lastro.models.sale import Sale
from lastro.schemas.position import (
    PositionCreate,
    PositionEvent,
    PositionEventType,
    PositionHistory,
    PositionRead,
    PricePoint,
)
from lastro.services.analytics.magic_number import calculate_magic_number
from lastro.services.analytics.total_return import calculate_total_return
from lastro.services.portfolio.average_price import calculate_average_price_cents
from lastro.services.portfolio.price_history import record_price_point
from lastro.services.quotes.dependency import get_quote_provider

router = APIRouter(prefix="/positions", tags=["positions"])


async def _contributions_for(session: AsyncSession, position_id: int) -> list[Contribution]:
    result = await session.exec(select(Contribution).where(Contribution.position_id == position_id))
    return list(result.all())


async def _dividends_for(session: AsyncSession, position_id: int) -> list[Dividend]:
    result = await session.exec(select(Dividend).where(Dividend.position_id == position_id))
    return list(result.all())


async def _sales_for(session: AsyncSession, position_id: int) -> list[Sale]:
    result = await session.exec(select(Sale).where(Sale.position_id == position_id))
    return list(result.all())


async def _to_position_read(session: AsyncSession, position: Position) -> PositionRead:
    contributions = await _contributions_for(session, position.id)
    average_price_cents = calculate_average_price_cents(contributions)

    total_return = None
    magic_number = None
    if position.last_price_cents is not None:
        dividends = await _dividends_for(session, position.id)
        sales = await _sales_for(session, position.id)
        total_return = calculate_total_return(
            contributions, dividends, position.last_price_cents, sales
        )
        magic_number = calculate_magic_number(dividends, position.last_price_cents, date.today())

    return PositionRead(
        id=position.id,
        ticker=position.ticker,
        name=position.name,
        asset_type=position.asset_type,
        quantity=position.quantity,
        is_active=position.is_active,
        average_price_cents=average_price_cents,
        last_price_cents=position.last_price_cents,
        last_price_fetched_at=position.last_price_fetched_at,
        price_earnings=position.price_earnings,
        earnings_per_share=position.earnings_per_share,
        total_return=total_return,
        magic_number=magic_number,
    )


@router.get("", response_model=list[PositionRead])
async def list_positions(session: AsyncSession = Depends(get_session)) -> list[PositionRead]:
    result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = result.all()
    return [await _to_position_read(session, position) for position in positions]


@router.post("", response_model=PositionRead, status_code=201)
async def create_position(
    payload: PositionCreate, session: AsyncSession = Depends(get_session)
) -> PositionRead:
    position = Position(**payload.model_dump())
    session.add(position)
    await session.commit()
    await session.refresh(position)
    return await _to_position_read(session, position)


@router.delete("/{position_id}", status_code=204)
async def deactivate_position(
    position_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    position = await session.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="posição não encontrada")

    position.is_active = False
    session.add(position)
    await session.commit()


@router.get("/{position_id}/history", response_model=PositionHistory)
async def get_position_history(
    position_id: int, session: AsyncSession = Depends(get_session)
) -> PositionHistory:
    position = await session.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="posição não encontrada")

    contributions = await _contributions_for(session, position_id)
    sales = await _sales_for(session, position_id)
    dividends = await _dividends_for(session, position_id)

    events = [
        PositionEvent(
            type=PositionEventType.CONTRIBUTION,
            date=c.date,
            quantity=c.quantity,
            unit_price_cents=c.unit_price_cents,
        )
        for c in contributions
    ]
    events += [
        PositionEvent(
            type=PositionEventType.SALE,
            date=s.date,
            quantity=s.quantity,
            unit_price_cents=s.unit_price_cents,
        )
        for s in sales
    ]
    events += [
        PositionEvent(type=PositionEventType.DIVIDEND, date=d.date, amount_cents=d.amount_cents)
        for d in dividends
    ]
    events.sort(key=lambda e: e.date)

    price_result = await session.exec(
        select(PriceHistory)
        .where(PriceHistory.position_id == position_id)
        .order_by(PriceHistory.date)
    )
    price_history = [PricePoint(date=p.date, price_cents=p.price_cents) for p in price_result.all()]

    return PositionHistory(events=events, price_history=price_history)


@router.post("/refresh-quotes", response_model=list[PositionRead])
async def refresh_quotes(session: AsyncSession = Depends(get_session)) -> list[PositionRead]:
    result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = result.all()

    for position in positions:
        if position.asset_type == AssetType.FIXED_INCOME:
            continue

        provider = get_quote_provider(position.asset_type)
        quote = await provider.get_quote(position.ticker)
        position.last_price_cents = quote.price_cents
        position.last_price_fetched_at = datetime.now(UTC)
        position.price_earnings = quote.price_earnings
        position.earnings_per_share = quote.earnings_per_share
        session.add(position)
        await record_price_point(session, position.id, datetime.now(UTC).date(), quote.price_cents)

    await session.commit()
    for position in positions:
        await session.refresh(position)

    return [await _to_position_read(session, position) for position in positions]
