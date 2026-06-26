from pydantic import BaseModel

from lastro.models.card import Card
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense


class CardSpendingBreakdown(BaseModel):
    card_id: int
    card_name: str
    total_cents: int


class MonthlySummary(BaseModel):
    year: int
    month: int
    income_total_cents: int
    fixed_expense_total_cents: int
    variable_expense_total_cents: int
    card_spending: list[CardSpendingBreakdown]
    card_spending_total_cents: int
    balance_cents: int


def calculate_monthly_summary(
    year: int,
    month: int,
    incomes: list[Income],
    fixed_expenses: list[FixedExpense],
    variable_expenses: list[VariableExpense],
    cards: list[Card],
    transactions: list[Transaction],
) -> MonthlySummary:
    """Resumo mensal estilo planilha: cartões já filtrados por ativos pelo
    chamador, transações já filtradas pelo mês/ano pedido."""
    income_total_cents = sum(income.amount_cents for income in incomes)
    fixed_expense_total_cents = sum(expense.amount_cents for expense in fixed_expenses)
    variable_expense_total_cents = sum(expense.amount_cents for expense in variable_expenses)

    spending_by_card_id: dict[int, int] = {}
    for transaction in transactions:
        spending_by_card_id[transaction.card_id] = (
            spending_by_card_id.get(transaction.card_id, 0) + transaction.amount_cents
        )

    card_spending = [
        CardSpendingBreakdown(
            card_id=card.id,
            card_name=card.name,
            total_cents=spending_by_card_id.get(card.id, 0),
        )
        for card in cards
    ]
    card_spending_total_cents = sum(breakdown.total_cents for breakdown in card_spending)

    balance_cents = (
        income_total_cents
        - fixed_expense_total_cents
        - variable_expense_total_cents
        - card_spending_total_cents
    )

    return MonthlySummary(
        year=year,
        month=month,
        income_total_cents=income_total_cents,
        fixed_expense_total_cents=fixed_expense_total_cents,
        variable_expense_total_cents=variable_expense_total_cents,
        card_spending=card_spending,
        card_spending_total_cents=card_spending_total_cents,
        balance_cents=balance_cents,
    )
