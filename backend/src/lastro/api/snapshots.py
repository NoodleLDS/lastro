from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.price_snapshot import PriceSnapshot
from lastro.schemas.price_snapshot import SnapshotRead
from lastro.services.analytics.snapshot import record_monthly_snapshot

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotRead])
async def list_snapshots(session: AsyncSession = Depends(get_session)) -> list[PriceSnapshot]:
    result = await session.exec(select(PriceSnapshot).order_by(PriceSnapshot.month))
    return list(result.all())


@router.post("", response_model=SnapshotRead, status_code=201)
async def create_snapshot(session: AsyncSession = Depends(get_session)) -> PriceSnapshot:
    return await record_monthly_snapshot(session)
