from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.contribution import Contribution
from lastro.models.position import Position
from lastro.models.sale import Sale
from lastro.models.stock_split import StockSplit
from lastro.schemas.sale import SaleCreate, SaleRead
from lastro.services.portfolio.price_history import record_price_point
from lastro.services.portfolio.quantity import calculate_quantity, sync_position_quantity

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=list[SaleRead])
async def list_sales(
    position_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Sale]:
    statement = select(Sale)
    if position_id is not None:
        statement = statement.where(Sale.position_id == position_id)
    result = await session.exec(statement)
    return list(result.all())


@router.post("", response_model=SaleRead, status_code=201)
async def create_sale(payload: SaleCreate, session: AsyncSession = Depends(get_session)) -> Sale:
    if payload.quantity <= 0:
        raise HTTPException(status_code=422, detail="quantity deve ser maior que zero")

    position = await session.get(Position, payload.position_id)
    if position is None:
        raise HTTPException(status_code=422, detail="position_id não encontrada")

    contributions_result = await session.exec(
        select(Contribution).where(Contribution.position_id == payload.position_id)
    )
    sales_result = await session.exec(select(Sale).where(Sale.position_id == payload.position_id))
    splits_result = await session.exec(
        select(StockSplit).where(StockSplit.position_id == payload.position_id)
    )
    current_quantity = calculate_quantity(
        list(contributions_result.all()), list(sales_result.all()), list(splits_result.all())
    )
    if payload.quantity > current_quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f"quantity ({payload.quantity}) excede a quantidade atual da posição "
                f"({current_quantity})"
            ),
        )

    sale = Sale(**payload.model_dump())
    session.add(sale)
    await record_price_point(session, payload.position_id, payload.date, payload.unit_price_cents)
    await session.flush()
    await sync_position_quantity(session, payload.position_id)
    await session.commit()
    await session.refresh(sale)
    return sale


@router.delete("/{sale_id}", status_code=204)
async def delete_sale(sale_id: int, session: AsyncSession = Depends(get_session)) -> None:
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="venda não encontrada")

    position_id = sale.position_id
    await session.delete(sale)
    await session.flush()
    await sync_position_quantity(session, position_id)
    await session.commit()
