from pydantic import BaseModel
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.card import Card
from lastro.models.card_invoice_payment import CardInvoicePayment
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense


class CardSpendingBreakdown(BaseModel):
    card_id: int
    card_name: str
    total_cents: int
    is_paid: bool


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
    invoice_payments: list[CardInvoicePayment] | None = None,
) -> MonthlySummary:
    """Resumo mensal estilo planilha: cartões já filtrados por ativos pelo
    chamador, transações e pagamentos de fatura já filtrados pelo mês/ano pedido."""
    income_total_cents = sum(income.amount_cents for income in incomes)
    fixed_expense_total_cents = sum(expense.amount_cents for expense in fixed_expenses)
    variable_expense_total_cents = sum(expense.amount_cents for expense in variable_expenses)

    spending_by_card_id: dict[int, int] = {}
    for transaction in transactions:
        spending_by_card_id[transaction.card_id] = (
            spending_by_card_id.get(transaction.card_id, 0) + transaction.amount_cents
        )

    paid_card_ids = {payment.card_id for payment in invoice_payments or []}

    card_spending = [
        CardSpendingBreakdown(
            card_id=card.id,
            card_name=card.name,
            total_cents=spending_by_card_id.get(card.id, 0),
            is_paid=card.id in paid_card_ids,
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


async def fetch_monthly_summary(session: AsyncSession, year: int, month: int) -> MonthlySummary:
    """Consulta o banco e monta o resumo mensal estilo planilha. Usado pelo
    endpoint /monthly-summary e pela tool do analista IA."""
    incomes_result = await session.exec(
        select(Income).where(Income.year == year, Income.month == month)
    )
    fixed_expenses_result = await session.exec(
        select(FixedExpense).where(FixedExpense.year == year, FixedExpense.month == month)
    )
    variable_expenses_result = await session.exec(
        select(VariableExpense).where(VariableExpense.year == year, VariableExpense.month == month)
    )
    cards_result = await session.exec(select(Card).where(Card.is_active.is_(True)))

    cards = list(cards_result.all())
    transactions: list[Transaction] = []
    invoice_payments: list[CardInvoicePayment] = []
    if cards:
        card_ids = [card.id for card in cards]
        transactions_result = await session.exec(
            select(Transaction).where(
                Transaction.card_id.in_(card_ids),
                func.strftime("%Y", Transaction.date) == f"{year:04d}",
                func.strftime("%m", Transaction.date) == f"{month:02d}",
            )
        )
        transactions = list(transactions_result.all())

        invoice_payments_result = await session.exec(
            select(CardInvoicePayment).where(
                CardInvoicePayment.card_id.in_(card_ids),
                CardInvoicePayment.year == year,
                CardInvoicePayment.month == month,
            )
        )
        invoice_payments = list(invoice_payments_result.all())

    return calculate_monthly_summary(
        year=year,
        month=month,
        incomes=list(incomes_result.all()),
        fixed_expenses=list(fixed_expenses_result.all()),
        variable_expenses=list(variable_expenses_result.all()),
        cards=cards,
        transactions=transactions,
        invoice_payments=invoice_payments,
    )
