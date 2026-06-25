from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.category import Category
from lastro.schemas.category import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(session: AsyncSession = Depends(get_session)) -> list[Category]:
    result = await session.exec(select(Category))
    return list(result.all())


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    payload: CategoryCreate, session: AsyncSession = Depends(get_session)
) -> Category:
    category = Category(name=payload.name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category
