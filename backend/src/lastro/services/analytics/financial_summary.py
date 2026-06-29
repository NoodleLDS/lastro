from datetime import date

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.card import Card
from lastro.models.category import Category
from lastro.models.contribution import Contribution
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense

RESERVE_AVERAGE_EXPENSE_MONTHS = 3


class CategoryCardBreakdown(BaseModel):
    category_id: int | None
    category_name: str
    card_id: int
    card_name: str
    total_cents: int


class MonthlyFinancialTotals(BaseModel):
    year: int
    month: int
    income_total_cents: int
    expense_total_cents: int
    contribution_total_cents: int
    balance_cents: int


class YearlyFinancialTotals(BaseModel):
    year: int
    income_total_cents: int
    expense_total_cents: int
    balance_cents: int


class EmergencyReserveSummary(BaseModel):
    balance_cents: int
    average_monthly_expense_cents: int
    months_covered: float | None


class FinancialSummary(BaseModel):
    monthly: MonthlyFinancialTotals
    yearly: YearlyFinancialTotals
    emergency_reserve: EmergencyReserveSummary
    category_card_breakdown: list[CategoryCardBreakdown]


def _expense_total_cents(
    fixed_expenses: list[FixedExpense],
    variable_expenses: list[VariableExpense],
    transactions: list[Transaction],
) -> int:
    return (
        sum(expense.amount_cents for expense in fixed_expenses)
        + sum(expense.amount_cents for expense in variable_expenses)
        + sum(transaction.amount_cents for transaction in transactions)
    )


def calculate_monthly_totals(
    year: int,
    month: int,
    incomes: list[Income],
    fixed_expenses: list[FixedExpense],
    variable_expenses: list[VariableExpense],
    transactions: list[Transaction],
    contributions: list[Contribution],
) -> MonthlyFinancialTotals:
    income_total_cents = sum(income.amount_cents for income in incomes)
    expense_total_cents = _expense_total_cents(fixed_expenses, variable_expenses, transactions)
    contribution_total_cents = round(
        sum(contribution.quantity * contribution.unit_price_cents for contribution in contributions)
    )

    return MonthlyFinancialTotals(
        year=year,
        month=month,
        income_total_cents=income_total_cents,
        expense_total_cents=expense_total_cents,
        contribution_total_cents=contribution_total_cents,
        balance_cents=income_total_cents - expense_total_cents - contribution_total_cents,
    )


def calculate_yearly_totals(
    year: int,
    incomes: list[Income],
    fixed_expenses: list[FixedExpense],
    variable_expenses: list[VariableExpense],
    transactions: list[Transaction],
) -> YearlyFinancialTotals:
    income_total_cents = sum(income.amount_cents for income in incomes)
    expense_total_cents = _expense_total_cents(fixed_expenses, variable_expenses, transactions)

    return YearlyFinancialTotals(
        year=year,
        income_total_cents=income_total_cents,
        expense_total_cents=expense_total_cents,
        balance_cents=income_total_cents - expense_total_cents,
    )


def calculate_emergency_reserve_summary(
    reserves: list[EmergencyReserve],
    recent_months_expense_cents: list[int],
) -> EmergencyReserveSummary:
    """Meses cobertos pela despesa média dos últimos N meses informados pelo
    chamador (RESERVE_AVERAGE_EXPENSE_MONTHS), sem dado de despesa = None."""
    balance_cents = sum(reserve.balance_cents for reserve in reserves)

    if not recent_months_expense_cents:
        return EmergencyReserveSummary(
            balance_cents=balance_cents,
            average_monthly_expense_cents=0,
            months_covered=None,
        )

    average_monthly_expense_cents = round(
        sum(recent_months_expense_cents) / len(recent_months_expense_cents)
    )
    months_covered = (
        balance_cents / average_monthly_expense_cents if average_monthly_expense_cents > 0 else None
    )

    return EmergencyReserveSummary(
        balance_cents=balance_cents,
        average_monthly_expense_cents=average_monthly_expense_cents,
        months_covered=months_covered,
    )


def calculate_category_card_breakdown(
    transactions: list[Transaction],
    cards: list[Card],
    categories: list[Category],
) -> list[CategoryCardBreakdown]:
    card_name_by_id = {card.id: card.name for card in cards}
    category_name_by_id = {category.id: category.name for category in categories}

    totals: dict[tuple[int | None, int], int] = {}
    for transaction in transactions:
        key = (transaction.category_id, transaction.card_id)
        totals[key] = totals.get(key, 0) + transaction.amount_cents

    return [
        CategoryCardBreakdown(
            category_id=category_id,
            category_name=category_name_by_id.get(category_id, "Sem categoria")
            if category_id is not None
            else "Sem categoria",
            card_id=card_id,
            card_name=card_name_by_id.get(card_id, "Desconhecido"),
            total_cents=total_cents,
        )
        for (category_id, card_id), total_cents in totals.items()
    ]


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


async def _transactions_between(session: AsyncSession, start: date, end: date) -> list[Transaction]:
    result = await session.exec(
        select(Transaction).where(Transaction.date >= start, Transaction.date < end)
    )
    return list(result.all())


async def fetch_financial_summary(session: AsyncSession, year: int, month: int) -> FinancialSummary:
    """Monta o resumo financeiro completo (mensal, anual, reserva, breakdown
    categoria x cartao) consultando o banco. Usado pelo endpoint do dashboard
    e pela tool do analista IA."""
    month_start, month_end = _month_bounds(year, month)

    incomes_result = await session.exec(
        select(Income).where(Income.year == year, Income.month == month)
    )
    fixed_expenses_result = await session.exec(
        select(FixedExpense).where(FixedExpense.year == year, FixedExpense.month == month)
    )
    variable_expenses_result = await session.exec(
        select(VariableExpense).where(VariableExpense.year == year, VariableExpense.month == month)
    )
    month_transactions = await _transactions_between(session, month_start, month_end)
    contributions_result = await session.exec(
        select(Contribution).where(Contribution.date >= month_start, Contribution.date < month_end)
    )

    monthly = calculate_monthly_totals(
        year=year,
        month=month,
        incomes=list(incomes_result.all()),
        fixed_expenses=list(fixed_expenses_result.all()),
        variable_expenses=list(variable_expenses_result.all()),
        transactions=month_transactions,
        contributions=list(contributions_result.all()),
    )

    year_incomes_result = await session.exec(select(Income).where(Income.year == year))
    year_fixed_expenses_result = await session.exec(
        select(FixedExpense).where(FixedExpense.year == year)
    )
    year_variable_expenses_result = await session.exec(
        select(VariableExpense).where(VariableExpense.year == year)
    )
    year_start, _ = _month_bounds(year, 1)
    year_end, _ = _month_bounds(year + 1, 1)
    year_transactions = await _transactions_between(session, year_start, year_end)

    yearly = calculate_yearly_totals(
        year=year,
        incomes=list(year_incomes_result.all()),
        fixed_expenses=list(year_fixed_expenses_result.all()),
        variable_expenses=list(year_variable_expenses_result.all()),
        transactions=year_transactions,
    )

    recent_months_expense_cents: list[int] = []
    for offset in range(RESERVE_AVERAGE_EXPENSE_MONTHS):
        ref_month = month - offset
        ref_year = year
        while ref_month < 1:
            ref_month += 12
            ref_year -= 1
        ref_start, ref_end = _month_bounds(ref_year, ref_month)

        ref_fixed_result = await session.exec(
            select(FixedExpense).where(
                FixedExpense.year == ref_year, FixedExpense.month == ref_month
            )
        )
        ref_variable_result = await session.exec(
            select(VariableExpense).where(
                VariableExpense.year == ref_year, VariableExpense.month == ref_month
            )
        )
        ref_transactions = await _transactions_between(session, ref_start, ref_end)

        recent_months_expense_cents.append(
            sum(e.amount_cents for e in ref_fixed_result.all())
            + sum(e.amount_cents for e in ref_variable_result.all())
            + sum(t.amount_cents for t in ref_transactions)
        )

    reserves_result = await session.exec(select(EmergencyReserve))
    emergency_reserve = calculate_emergency_reserve_summary(
        list(reserves_result.all()), recent_months_expense_cents
    )

    cards_result = await session.exec(select(Card).where(Card.is_active.is_(True)))
    categories_result = await session.exec(select(Category))
    category_card_breakdown = calculate_category_card_breakdown(
        month_transactions, list(cards_result.all()), list(categories_result.all())
    )

    return FinancialSummary(
        monthly=monthly,
        yearly=yearly,
        emergency_reserve=emergency_reserve,
        category_card_breakdown=category_card_breakdown,
    )
