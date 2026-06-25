from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.position import Position
from lastro.models.sale import Sale
from lastro.schemas.sale import SaleCreate, SaleRead
from lastro.services.portfolio.price_history import record_price_point
from lastro.services.portfolio.quantity import apply_quantity_delta

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
    if payload.quantity > position.quantity:
        raise HTTPException(
            status_code=422,
            detail=(
                f"quantity ({payload.quantity}) excede a quantidade atual da posição "
                f"({position.quantity})"
            ),
        )

    sale = Sale(**payload.model_dump())
    session.add(sale)
    await apply_quantity_delta(session, payload.position_id, -payload.quantity)
    await record_price_point(session, payload.position_id, payload.date, payload.unit_price_cents)
    await session.commit()
    await session.refresh(sale)
    return sale


@router.delete("/{sale_id}", status_code=204)
async def delete_sale(sale_id: int, session: AsyncSession = Depends(get_session)) -> None:
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="venda não encontrada")

    await apply_quantity_delta(session, sale.position_id, sale.quantity)
    await session.delete(sale)
    await session.commit()
