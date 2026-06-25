from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.dividend import Dividend
from lastro.schemas.dividend import DividendCreate, DividendRead

router = APIRouter(prefix="/dividends", tags=["dividends"])


@router.get("", response_model=list[DividendRead])
async def list_dividends(
    position_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Dividend]:
    statement = select(Dividend)
    if position_id is not None:
        statement = statement.where(Dividend.position_id == position_id)
    result = await session.exec(statement)
    return list(result.all())


@router.post("", response_model=DividendRead, status_code=201)
async def create_dividend(
    payload: DividendCreate, session: AsyncSession = Depends(get_session)
) -> Dividend:
    dividend = Dividend(**payload.model_dump())
    session.add(dividend)
    await session.commit()
    await session.refresh(dividend)
    return dividend


@router.delete("/{dividend_id}", status_code=204)
async def delete_dividend(dividend_id: int, session: AsyncSession = Depends(get_session)) -> None:
    dividend = await session.get(Dividend, dividend_id)
    if dividend is None:
        raise HTTPException(status_code=404, detail="provento não encontrado")

    await session.delete(dividend)
    await session.commit()
