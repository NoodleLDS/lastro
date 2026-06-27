from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.fk import ensure_fk_exists
from lastro.db import get_session
from lastro.models.category import Category
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
    await ensure_fk_exists(session, Category, payload.category_id, "category_id")

    statement = select(MerchantRule).where(
        MerchantRule.pattern == payload.pattern, MerchantRule.is_active.is_(True)
    )
    existing = (await session.exec(statement)).first()
    if existing is not None:
        raise HTTPException(status_code=422, detail="já existe uma regra ativa com esse pattern")

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

    updates = payload.model_dump(exclude_unset=True)
    new_pattern = updates.get("pattern", rule.pattern)
    new_is_active = updates.get("is_active", rule.is_active)

    if "category_id" in updates:
        await ensure_fk_exists(session, Category, updates["category_id"], "category_id")

    if new_is_active:
        statement = select(MerchantRule).where(
            MerchantRule.pattern == new_pattern,
            MerchantRule.is_active.is_(True),
            MerchantRule.id != rule_id,
        )
        existing = (await session.exec(statement)).first()
        if existing is not None:
            raise HTTPException(
                status_code=422, detail="já existe uma regra ativa com esse pattern"
            )

    for field, value in updates.items():
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
