from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.contribution import Contribution
from lastro.schemas.contribution import (
    ContributionCreate,
    ContributionRead,
    DistributeContributionRequest,
)
from lastro.services.analytics.aporte import ContributionPreview, distribute_contribution
from lastro.services.portfolio.price_history import record_price_point
from lastro.services.portfolio.quantity import apply_quantity_delta

router = APIRouter(prefix="/contributions", tags=["contributions"])


@router.post("/distribute", response_model=ContributionPreview)
async def distribute(
    payload: DistributeContributionRequest, session: AsyncSession = Depends(get_session)
) -> ContributionPreview:
    if payload.total_cents <= 0:
        raise HTTPException(status_code=422, detail="total_cents deve ser maior que zero")
    return await distribute_contribution(session, payload.total_cents)


@router.get("", response_model=list[ContributionRead])
async def list_contributions(
    position_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Contribution]:
    statement = select(Contribution)
    if position_id is not None:
        statement = statement.where(Contribution.position_id == position_id)
    result = await session.exec(statement)
    return list(result.all())


@router.post("", response_model=ContributionRead, status_code=201)
async def create_contribution(
    payload: ContributionCreate, session: AsyncSession = Depends(get_session)
) -> Contribution:
    contribution = Contribution(**payload.model_dump())
    session.add(contribution)
    await apply_quantity_delta(session, payload.position_id, payload.quantity)
    await record_price_point(session, payload.position_id, payload.date, payload.unit_price_cents)
    await session.commit()
    await session.refresh(contribution)
    return contribution


@router.delete("/{contribution_id}", status_code=204)
async def delete_contribution(
    contribution_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    contribution = await session.get(Contribution, contribution_id)
    if contribution is None:
        raise HTTPException(status_code=404, detail="aporte não encontrado")

    await apply_quantity_delta(session, contribution.position_id, -contribution.quantity)
    await session.delete(contribution)
    await session.commit()
