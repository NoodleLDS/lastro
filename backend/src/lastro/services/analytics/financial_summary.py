from pydantic import BaseModel

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
