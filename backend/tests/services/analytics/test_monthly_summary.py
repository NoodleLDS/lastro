from lastro.models.card import Card
from lastro.models.card_invoice_payment import CardInvoicePayment
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense
from lastro.services.analytics.monthly_summary import calculate_monthly_summary


def _card(card_id: int, name: str, is_active: bool = True) -> Card:
    return Card(id=card_id, name=name, is_active=is_active)


def _transaction(card_id: int, amount_cents: int, year: int = 2026, month: int = 6) -> Transaction:
    return Transaction(
        date=f"{year:04d}-{month:02d}-15",
        description="teste",
        amount_cents=amount_cents,
        card_id=card_id,
    )


def test_resumo_mes_sem_nenhum_lancamento_retorna_zeros() -> None:
    summary = calculate_monthly_summary(2026, 6, [], [], [], [], [])

    assert summary.income_total_cents == 0
    assert summary.fixed_expense_total_cents == 0
    assert summary.variable_expense_total_cents == 0
    assert summary.card_spending == []
    assert summary.card_spending_total_cents == 0
    assert summary.balance_cents == 0


def test_resumo_com_apenas_receita() -> None:
    incomes = [Income(description="Salário", amount_cents=654_071, year=2026, month=6)]

    summary = calculate_monthly_summary(2026, 6, incomes, [], [], [], [])

    assert summary.income_total_cents == 654_071
    assert summary.balance_cents == 654_071


def test_resumo_soma_multiplas_linhas_de_receita_despesa_fixa_e_variavel() -> None:
    incomes = [
        Income(description="Salário", amount_cents=654_071, year=2026, month=6),
        Income(description="Outros", amount_cents=10_000, year=2026, month=6),
    ]
    fixed_expenses = [
        FixedExpense(description="Plano de saúde", amount_cents=12_300, year=2026, month=6),
        FixedExpense(description="Colégio", amount_cents=12_900, year=2026, month=6),
    ]
    variable_expenses = [
        VariableExpense(description="Luz", amount_cents=20_000, year=2026, month=6),
        VariableExpense(description="Água", amount_cents=9_000, year=2026, month=6),
    ]

    summary = calculate_monthly_summary(2026, 6, incomes, fixed_expenses, variable_expenses, [], [])

    assert summary.income_total_cents == 664_071
    assert summary.fixed_expense_total_cents == 25_200
    assert summary.variable_expense_total_cents == 29_000


def test_resumo_agrega_gasto_por_cartao_multiplos_cartoes() -> None:
    cards = [_card(1, "PicPay"), _card(2, "Inter")]
    transactions = [
        _transaction(card_id=1, amount_cents=10_000),
        _transaction(card_id=1, amount_cents=5_000),
        _transaction(card_id=2, amount_cents=3_000),
    ]

    summary = calculate_monthly_summary(2026, 6, [], [], [], cards, transactions)

    by_card = {breakdown.card_id: breakdown for breakdown in summary.card_spending}
    assert by_card[1].total_cents == 15_000
    assert by_card[2].total_cents == 3_000
    assert summary.card_spending_total_cents == 18_000


def test_resumo_inclui_cartao_ativo_sem_transacao_no_mes_com_total_zero() -> None:
    cards = [_card(1, "PicPay")]

    summary = calculate_monthly_summary(2026, 6, [], [], [], cards, [])

    assert len(summary.card_spending) == 1
    assert summary.card_spending[0].card_id == 1
    assert summary.card_spending[0].total_cents == 0
    assert summary.card_spending[0].is_paid is False


def test_resumo_marca_fatura_paga_quando_ha_invoice_payment_do_cartao_e_mes() -> None:
    cards = [_card(1, "PicPay"), _card(2, "Inter")]
    invoice_payments = [CardInvoicePayment(card_id=1, year=2026, month=6)]

    summary = calculate_monthly_summary(2026, 6, [], [], [], cards, [], invoice_payments)

    by_card = {breakdown.card_id: breakdown for breakdown in summary.card_spending}
    assert by_card[1].is_paid is True
    assert by_card[2].is_paid is False


def test_resumo_so_agrega_cartoes_recebidos_pelo_chamador() -> None:
    """Filtrar cartões inativos é responsabilidade do router (query),
    não do service — aqui só confirmamos que o service agrega exatamente
    a lista de cards recebida, sem lógica própria de ativo/inativo."""
    cards = [_card(1, "PicPay", is_active=False)]

    summary = calculate_monthly_summary(2026, 6, [], [], [], cards, [])

    assert len(summary.card_spending) == 1
    assert summary.card_spending[0].card_id == 1


def test_resumo_ignora_transacoes_de_outros_meses_anos() -> None:
    cards = [_card(1, "PicPay")]
    transactions_do_mes = [_transaction(card_id=1, amount_cents=10_000, year=2026, month=6)]

    summary = calculate_monthly_summary(2026, 6, [], [], [], cards, transactions_do_mes)

    assert summary.card_spending[0].total_cents == 10_000


def test_resumo_calcula_saldo_subtraindo_fixas_variaveis_e_cartoes_da_receita() -> None:
    incomes = [Income(description="Salário", amount_cents=989_337, year=2026, month=5)]
    fixed_expenses = [FixedExpense(description="Fixas", amount_cents=70_976, year=2026, month=5)]
    variable_expenses = [
        VariableExpense(description="Variáveis", amount_cents=102_659, year=2026, month=5)
    ]
    cards = [_card(1, "PicPay")]
    transactions = [_transaction(card_id=1, amount_cents=331_285, year=2026, month=5)]

    summary = calculate_monthly_summary(
        2026, 5, incomes, fixed_expenses, variable_expenses, cards, transactions
    )

    assert summary.balance_cents == 989_337 - 70_976 - 102_659 - 331_285


def test_resumo_saldo_negativo_quando_despesas_excedem_receita() -> None:
    incomes = [Income(description="Salário", amount_cents=100_000, year=2026, month=6)]
    fixed_expenses = [FixedExpense(description="Fixas", amount_cents=200_000, year=2026, month=6)]

    summary = calculate_monthly_summary(2026, 6, incomes, fixed_expenses, [], [], [])

    assert summary.balance_cents == -100_000
