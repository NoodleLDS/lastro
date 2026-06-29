from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.core.fk import ensure_fk_exists
from lastro.db import get_session
from lastro.models.category import Category
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.variable_expense import VariableExpense
from lastro.schemas.monthly_summary import (
    FixedExpenseCreate,
    FixedExpenseRead,
    FixedExpenseUpdate,
    IncomeCreate,
    IncomeRead,
    IncomeUpdate,
    VariableExpenseCreate,
    VariableExpenseRead,
    VariableExpenseUpdate,
)
from lastro.services.analytics.monthly_summary import MonthlySummary, fetch_monthly_summary

router = APIRouter(tags=["monthly-summary"])


@router.get("/incomes", response_model=list[IncomeRead])
async def list_incomes(
    year: int | None = None,
    month: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Income]:
    statement = select(Income)
    if year is not None:
        statement = statement.where(Income.year == year)
    if month is not None:
        statement = statement.where(Income.month == month)
    result = await session.exec(statement)
    return list(result.all())


@router.post("/incomes", response_model=IncomeRead, status_code=201)
async def create_income(
    payload: IncomeCreate, session: AsyncSession = Depends(get_session)
) -> Income:
    income = Income(**payload.model_dump())
    session.add(income)
    await session.commit()
    await session.refresh(income)
    return income


@router.patch("/incomes/{income_id}", response_model=IncomeRead)
async def update_income(
    income_id: int, payload: IncomeUpdate, session: AsyncSession = Depends(get_session)
) -> Income:
    income = await session.get(Income, income_id)
    if income is None:
        raise HTTPException(status_code=404, detail="receita não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(income, field, value)

    session.add(income)
    await session.commit()
    await session.refresh(income)
    return income


@router.delete("/incomes/{income_id}", status_code=204)
async def delete_income(income_id: int, session: AsyncSession = Depends(get_session)) -> None:
    income = await session.get(Income, income_id)
    if income is None:
        raise HTTPException(status_code=404, detail="receita não encontrada")
    await session.delete(income)
    await session.commit()


@router.get("/fixed-expenses", response_model=list[FixedExpenseRead])
async def list_fixed_expenses(
    year: int | None = None,
    month: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[FixedExpense]:
    statement = select(FixedExpense)
    if year is not None:
        statement = statement.where(FixedExpense.year == year)
    if month is not None:
        statement = statement.where(FixedExpense.month == month)
    result = await session.exec(statement)
    return list(result.all())


@router.post("/fixed-expenses", response_model=FixedExpenseRead, status_code=201)
async def create_fixed_expense(
    payload: FixedExpenseCreate, session: AsyncSession = Depends(get_session)
) -> FixedExpense:
    if payload.category_id is not None:
        await ensure_fk_exists(session, Category, payload.category_id, "category_id")

    expense = FixedExpense(**payload.model_dump())
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.patch("/fixed-expenses/{expense_id}", response_model=FixedExpenseRead)
async def update_fixed_expense(
    expense_id: int, payload: FixedExpenseUpdate, session: AsyncSession = Depends(get_session)
) -> FixedExpense:
    expense = await session.get(FixedExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="despesa fixa não encontrada")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("category_id") is not None:
        await ensure_fk_exists(session, Category, updates["category_id"], "category_id")

    for field, value in updates.items():
        setattr(expense, field, value)

    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.delete("/fixed-expenses/{expense_id}", status_code=204)
async def delete_fixed_expense(
    expense_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    expense = await session.get(FixedExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="despesa fixa não encontrada")
    await session.delete(expense)
    await session.commit()


@router.get("/variable-expenses", response_model=list[VariableExpenseRead])
async def list_variable_expenses(
    year: int | None = None,
    month: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[VariableExpense]:
    statement = select(VariableExpense)
    if year is not None:
        statement = statement.where(VariableExpense.year == year)
    if month is not None:
        statement = statement.where(VariableExpense.month == month)
    result = await session.exec(statement)
    return list(result.all())


@router.post("/variable-expenses", response_model=VariableExpenseRead, status_code=201)
async def create_variable_expense(
    payload: VariableExpenseCreate, session: AsyncSession = Depends(get_session)
) -> VariableExpense:
    if payload.category_id is not None:
        await ensure_fk_exists(session, Category, payload.category_id, "category_id")

    expense = VariableExpense(**payload.model_dump())
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.patch("/variable-expenses/{expense_id}", response_model=VariableExpenseRead)
async def update_variable_expense(
    expense_id: int, payload: VariableExpenseUpdate, session: AsyncSession = Depends(get_session)
) -> VariableExpense:
    expense = await session.get(VariableExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="despesa variável não encontrada")

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("category_id") is not None:
        await ensure_fk_exists(session, Category, updates["category_id"], "category_id")

    for field, value in updates.items():
        setattr(expense, field, value)

    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.delete("/variable-expenses/{expense_id}", status_code=204)
async def delete_variable_expense(
    expense_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    expense = await session.get(VariableExpense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="despesa variável não encontrada")
    await session.delete(expense)
    await session.commit()


@router.get("/monthly-summary", response_model=MonthlySummary)
async def get_monthly_summary(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
) -> MonthlySummary:
    return await fetch_monthly_summary(session, year, month)
