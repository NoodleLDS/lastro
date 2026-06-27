from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.position import Position
from lastro.models.stock_split import StockSplit
from lastro.schemas.stock_split import StockSplitCreate, StockSplitRead
from lastro.services.portfolio.quantity import sync_position_quantity

router = APIRouter(prefix="/stock-splits", tags=["stock-splits"])


@router.get("", response_model=list[StockSplitRead])
async def list_stock_splits(
    position_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[StockSplit]:
    statement = select(StockSplit)
    if position_id is not None:
        statement = statement.where(StockSplit.position_id == position_id)
    result = await session.exec(statement)
    return list(result.all())


@router.post("", response_model=StockSplitRead, status_code=201)
async def create_stock_split(
    payload: StockSplitCreate, session: AsyncSession = Depends(get_session)
) -> StockSplit:
    if payload.ratio_from <= 0 or payload.ratio_to <= 0:
        raise HTTPException(
            status_code=422, detail="ratio_from e ratio_to devem ser maiores que zero"
        )

    position = await session.get(Position, payload.position_id)
    if position is None:
        raise HTTPException(status_code=422, detail="position_id não encontrada")

    split = StockSplit(**payload.model_dump())
    session.add(split)
    await session.flush()
    await sync_position_quantity(session, payload.position_id)
    await session.commit()
    await session.refresh(split)
    return split


@router.delete("/{stock_split_id}", status_code=204)
async def delete_stock_split(
    stock_split_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    split = await session.get(StockSplit, stock_split_id)
    if split is None:
        raise HTTPException(status_code=404, detail="stock split não encontrado")

    position_id = split.position_id
    await session.delete(split)
    await session.flush()
    await sync_position_quantity(session, position_id)
    await session.commit()
