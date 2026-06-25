from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.position import Position
from lastro.models.price_snapshot import PriceSnapshot
from lastro.schemas.price_snapshot import SnapshotRead

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotRead])
async def list_snapshots(session: AsyncSession = Depends(get_session)) -> list[PriceSnapshot]:
    result = await session.exec(select(PriceSnapshot).order_by(PriceSnapshot.month))
    return list(result.all())


@router.post("", response_model=SnapshotRead, status_code=201)
async def create_snapshot(session: AsyncSession = Depends(get_session)) -> PriceSnapshot:
    result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = result.all()
    portfolio_value_cents = sum(
        round(position.quantity * position.last_price_cents)
        for position in positions
        if position.last_price_cents is not None
    )

    reserve_result = await session.exec(select(EmergencyReserve))
    reserves = reserve_result.all()
    emergency_reserve_value_cents = sum(reserve.balance_cents for reserve in reserves)

    month = date.today().replace(day=1)

    existing_result = await session.exec(select(PriceSnapshot).where(PriceSnapshot.month == month))
    snapshot = existing_result.first()

    if snapshot is None:
        snapshot = PriceSnapshot(
            month=month,
            portfolio_value_cents=portfolio_value_cents,
            emergency_reserve_value_cents=emergency_reserve_value_cents,
        )
    else:
        snapshot.portfolio_value_cents = portfolio_value_cents
        snapshot.emergency_reserve_value_cents = emergency_reserve_value_cents

    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot
