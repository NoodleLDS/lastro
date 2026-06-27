from lastro.models.card import Card
from lastro.models.category import Category
from lastro.models.contribution import Contribution
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense
from lastro.services.analytics.financial_summary import (
    calculate_category_card_breakdown,
    calculate_emergency_reserve_summary,
    calculate_monthly_totals,
    calculate_yearly_totals,
)


def test_totais_mensais_sem_lancamentos_retorna_zeros() -> None:
    totals = calculate_monthly_totals(2026, 6, [], [], [], [], [])

    assert totals.income_total_cents == 0
    assert totals.expense_total_cents == 0
    assert totals.contribution_total_cents == 0
    assert totals.balance_cents == 0


def test_totais_mensais_soma_receita_despesas_cartao_e_aportes() -> None:
    incomes = [Income(description="Salário", amount_cents=654_071, year=2026, month=6)]
    fixed_expenses = [
        FixedExpense(description="Plano de saúde", amount_cents=12_300, year=2026, month=6)
    ]
    variable_expenses = [
        VariableExpense(description="Luz", amount_cents=20_000, year=2026, month=6)
    ]
    transactions = [
        Transaction(date="2026-06-10", description="mercado", amount_cents=10_000, card_id=1)
    ]
    contributions = [
        Contribution(position_id=1, date="2026-06-05", quantity=10, unit_price_cents=1_000)
    ]

    totals = calculate_monthly_totals(
        2026, 6, incomes, fixed_expenses, variable_expenses, transactions, contributions
    )

    assert totals.income_total_cents == 654_071
    assert totals.expense_total_cents == 12_300 + 20_000 + 10_000
    assert totals.contribution_total_cents == 10_000
    assert totals.balance_cents == 654_071 - (12_300 + 20_000 + 10_000) - 10_000


def test_totais_anuais_soma_receita_e_despesas_do_ano() -> None:
    incomes = [
        Income(description="Salário", amount_cents=654_071, year=2026, month=1),
        Income(description="Salário", amount_cents=654_071, year=2026, month=2),
    ]
    fixed_expenses = [FixedExpense(description="Fixas", amount_cents=12_300, year=2026, month=1)]

    totals = calculate_yearly_totals(2026, incomes, fixed_expenses, [], [])

    assert totals.income_total_cents == 654_071 * 2
    assert totals.expense_total_cents == 12_300
    assert totals.balance_cents == 654_071 * 2 - 12_300


def test_reserva_sem_despesa_recente_retorna_meses_cobertos_none() -> None:
    reserves = [
        EmergencyReserve(institution="Inter", balance_cents=1_200_000, cdi_percentage=100.0)
    ]

    summary = calculate_emergency_reserve_summary(reserves, [])

    assert summary.balance_cents == 1_200_000
    assert summary.months_covered is None


def test_reserva_calcula_meses_cobertos_pela_media_de_despesa() -> None:
    reserves = [EmergencyReserve(institution="Inter", balance_cents=600_000, cdi_percentage=100.0)]

    summary = calculate_emergency_reserve_summary(reserves, [300_000, 200_000, 100_000])

    assert summary.average_monthly_expense_cents == 200_000
    assert summary.months_covered == 3.0


def test_reserva_meses_cobertos_none_quando_media_e_zero() -> None:
    reserves = [EmergencyReserve(institution="Inter", balance_cents=600_000, cdi_percentage=100.0)]

    summary = calculate_emergency_reserve_summary(reserves, [0, 0])

    assert summary.average_monthly_expense_cents == 0
    assert summary.months_covered is None


def test_breakdown_categoria_cartao_agrupa_corretamente() -> None:
    cards = [Card(id=1, name="PicPay")]
    categories = [Category(id=1, name="Alimentação")]
    transactions = [
        Transaction(
            date="2026-06-10", description="mercado", amount_cents=10_000, card_id=1, category_id=1
        ),
        Transaction(
            date="2026-06-15", description="padaria", amount_cents=5_000, card_id=1, category_id=1
        ),
    ]

    breakdown = calculate_category_card_breakdown(transactions, cards, categories)

    assert len(breakdown) == 1
    assert breakdown[0].category_name == "Alimentação"
    assert breakdown[0].card_name == "PicPay"
    assert breakdown[0].total_cents == 15_000


def test_breakdown_categoria_cartao_trata_sem_categoria() -> None:
    cards = [Card(id=1, name="PicPay")]
    transactions = [
        Transaction(
            date="2026-06-10",
            description="mercado",
            amount_cents=10_000,
            card_id=1,
            category_id=None,
        ),
    ]

    breakdown = calculate_category_card_breakdown(transactions, cards, [])

    assert breakdown[0].category_name == "Sem categoria"
    assert breakdown[0].category_id is None
