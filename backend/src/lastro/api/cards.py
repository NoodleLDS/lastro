from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.card import Card
from lastro.schemas.card import BillingCycleRead, CardCreate, CardRead, CardUpdate
from lastro.services.cards.billing_cycle import billing_cycle_range

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=list[CardRead])
async def list_cards(
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_session),
) -> list[Card]:
    statement = select(Card)
    if not include_inactive:
        statement = statement.where(Card.is_active.is_(True))
    result = await session.exec(statement)
    return list(result.all())


@router.post("", response_model=CardRead, status_code=201)
async def create_card(payload: CardCreate, session: AsyncSession = Depends(get_session)) -> Card:
    card = Card(**payload.model_dump())
    session.add(card)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="já existe um cartão com esse nome") from exc
    await session.refresh(card)
    return card


@router.put("/{card_id}", response_model=CardRead)
async def update_card(
    card_id: int, payload: CardUpdate, session: AsyncSession = Depends(get_session)
) -> Card:
    card = await session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="cartão não encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)

    session.add(card)
    await session.commit()
    await session.refresh(card)
    return card


@router.get("/{card_id}/billing-cycle", response_model=BillingCycleRead)
async def get_billing_cycle(
    card_id: int,
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
) -> BillingCycleRead:
    card = await session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="cartão não encontrado")

    if card.closing_day is None:
        last_day = monthrange(year, month)[1]
        return BillingCycleRead(
            year=year,
            month=month,
            date_from=date(year, month, 1),
            date_to=date(year, month, last_day),
            is_calendar_month=True,
        )

    date_from, date_to = billing_cycle_range(card.closing_day, year, month)
    return BillingCycleRead(
        year=year, month=month, date_from=date_from, date_to=date_to, is_calendar_month=False
    )


@router.delete("/{card_id}", status_code=204)
async def deactivate_card(card_id: int, session: AsyncSession = Depends(get_session)) -> None:
    card = await session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="cartão não encontrado")

    card.is_active = False
    session.add(card)
    await session.commit()
