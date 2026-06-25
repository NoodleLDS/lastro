from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.merchant_rule import MerchantRule
from lastro.schemas.merchant_rule import MerchantRuleCreate, MerchantRuleRead, MerchantRuleUpdate

router = APIRouter(prefix="/merchant-rules", tags=["merchant-rules"])


@router.get("", response_model=list[MerchantRuleRead])
async def list_merchant_rules(
    session: AsyncSession = Depends(get_session),
) -> list[MerchantRule]:
    result = await session.exec(select(MerchantRule))
    return list(result.all())


@router.post("", response_model=MerchantRuleRead, status_code=201)
async def create_merchant_rule(
    payload: MerchantRuleCreate, session: AsyncSession = Depends(get_session)
) -> MerchantRule:
    rule = MerchantRule(**payload.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=MerchantRuleRead)
async def update_merchant_rule(
    rule_id: int, payload: MerchantRuleUpdate, session: AsyncSession = Depends(get_session)
) -> MerchantRule:
    rule = await session.get(MerchantRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="regra não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_merchant_rule(rule_id: int, session: AsyncSession = Depends(get_session)) -> None:
    rule = await session.get(MerchantRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="regra não encontrada")

    await session.delete(rule)
    await session.commit()
