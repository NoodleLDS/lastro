from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.allocation_target import AllocationTarget
from lastro.schemas.allocation_target import (
    AllocationTargetCreate,
    AllocationTargetRead,
    AllocationTargetUpdate,
)

router = APIRouter(prefix="/allocation-targets", tags=["allocation-targets"])


@router.get("", response_model=list[AllocationTargetRead])
async def list_allocation_targets(
    session: AsyncSession = Depends(get_session),
) -> list[AllocationTarget]:
    result = await session.exec(select(AllocationTarget))
    return list(result.all())


@router.post("", response_model=AllocationTargetRead, status_code=201)
async def create_allocation_target(
    payload: AllocationTargetCreate, session: AsyncSession = Depends(get_session)
) -> AllocationTarget:
    target = AllocationTarget(**payload.model_dump())
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return target


@router.put("/{target_id}", response_model=AllocationTargetRead)
async def update_allocation_target(
    target_id: int, payload: AllocationTargetUpdate, session: AsyncSession = Depends(get_session)
) -> AllocationTarget:
    target = await session.get(AllocationTarget, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="meta de alocação não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)

    session.add(target)
    await session.commit()
    await session.refresh(target)
    return target


@router.delete("/{target_id}", status_code=204)
async def delete_allocation_target(
    target_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    target = await session.get(AllocationTarget, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="meta de alocação não encontrada")

    await session.delete(target)
    await session.commit()
