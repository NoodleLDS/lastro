from datetime import date

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.position import Position
from lastro.models.price_snapshot import PriceSnapshot


async def record_monthly_snapshot(session: AsyncSession) -> PriceSnapshot:
    """Cria ou atualiza o snapshot do mês atual com o valor vivo da carteira
    e da reserva de emergência. Idempotente por mês — chamado tanto no
    startup da API quanto manualmente pelo usuário."""
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
