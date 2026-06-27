from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.schemas.emergency_reserve import (
    EmergencyReserveCreate,
    EmergencyReserveRead,
    EmergencyReserveUpdate,
)

router = APIRouter(prefix="/emergency-reserve", tags=["emergency-reserve"])


@router.get("", response_model=list[EmergencyReserveRead])
async def list_emergency_reserves(
    session: AsyncSession = Depends(get_session),
) -> list[EmergencyReserve]:
    result = await session.exec(select(EmergencyReserve))
    return list(result.all())


@router.post("", response_model=EmergencyReserveRead, status_code=201)
async def create_emergency_reserve(
    payload: EmergencyReserveCreate, session: AsyncSession = Depends(get_session)
) -> EmergencyReserve:
    reserve = EmergencyReserve(**payload.model_dump())
    session.add(reserve)
    await session.commit()
    await session.refresh(reserve)
    return reserve


@router.patch("/{reserve_id}", response_model=EmergencyReserveRead)
async def update_emergency_reserve(
    reserve_id: int, payload: EmergencyReserveUpdate, session: AsyncSession = Depends(get_session)
) -> EmergencyReserve:
    reserve = await session.get(EmergencyReserve, reserve_id)
    if reserve is None:
        raise HTTPException(status_code=404, detail="reserva de emergência não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reserve, field, value)

    session.add(reserve)
    await session.commit()
    await session.refresh(reserve)
    return reserve


@router.delete("/{reserve_id}", status_code=204)
async def delete_emergency_reserve(
    reserve_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    reserve = await session.get(EmergencyReserve, reserve_id)
    if reserve is None:
        raise HTTPException(status_code=404, detail="reserva de emergência não encontrada")
    await session.delete(reserve)
    await session.commit()
