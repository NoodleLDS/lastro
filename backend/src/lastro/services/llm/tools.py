from collections.abc import Awaitable, Callable

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.transaction import Transaction, TransactionStatus
from lastro.services.analytics.analyst_context import build_portfolio_context
from lastro.services.analytics.financial_summary import fetch_financial_summary
from lastro.services.analytics.monthly_summary import fetch_monthly_summary

ToolExecutor = Callable[[AsyncSession, dict], Awaitable[str]]

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio",
            "description": (
                "Retorna a carteira de investimentos atual: posições ativas, preço médio, "
                "preço atual, total return, número mágico, preço-teto e alocação real vs meta."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": (
                "Retorna o resumo financeiro de um mês: receita, despesas fixas e variáveis, "
                "gasto por cartão de crédito, e saldo do mês."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Ano, ex.: 2026"},
                    "month": {"type": "integer", "description": "Mês de 1 a 12"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_summary",
            "description": (
                "Retorna o resumo financeiro completo de um mês e do ano correspondente: "
                "totais mensais e anuais de receita/despesa/saldo, reserva de emergência "
                "(saldo, despesa média dos últimos 3 meses, meses cobertos) e o gasto por "
                "categoria em cada cartão naquele mês."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Ano, ex.: 2026"},
                    "month": {"type": "integer", "description": "Mês de 1 a 12"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_emergency_reserve",
            "description": (
                "Retorna as reservas de emergência cadastradas (instituição, saldo, % do CDI)."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": (
                "Lista transações de cartão confirmadas, com filtro opcional por ano, mês, "
                "card_id ou busca textual na descrição. Use para responder perguntas sobre "
                "gastos específicos que não estão cobertos pelo resumo mensal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                    "card_id": {"type": "integer"},
                    "search": {"type": "string", "description": "busca na descrição"},
                },
            },
        },
    },
]


def _format_cents(cents: int) -> str:
    return f"R$ {cents / 100:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


async def _exec_get_portfolio(session: AsyncSession, _args: dict) -> str:
    return await build_portfolio_context(session)


async def _exec_get_monthly_summary(session: AsyncSession, args: dict) -> str:
    summary = await fetch_monthly_summary(session, args["year"], args["month"])
    lines = [
        f"Resumo de {summary.month:02d}/{summary.year}:",
        f"Receita: {_format_cents(summary.income_total_cents)}",
        f"Despesas fixas: {_format_cents(summary.fixed_expense_total_cents)}",
        f"Despesas variáveis: {_format_cents(summary.variable_expense_total_cents)}",
        f"Gasto em cartões: {_format_cents(summary.card_spending_total_cents)}",
    ]
    for card in summary.card_spending:
        lines.append(f"  - {card.card_name}: {_format_cents(card.total_cents)}")
    lines.append(f"Saldo do mês: {_format_cents(summary.balance_cents)}")
    return "\n".join(lines)


async def _exec_get_financial_summary(session: AsyncSession, args: dict) -> str:
    summary = await fetch_financial_summary(session, args["year"], args["month"])
    lines = [
        f"Resumo financeiro de {args['month']:02d}/{args['year']}:",
        f"Mês — receita {_format_cents(summary.monthly.income_total_cents)}, "
        f"despesas {_format_cents(summary.monthly.expense_total_cents)}, "
        f"aportado {_format_cents(summary.monthly.contribution_total_cents)}, "
        f"saldo {_format_cents(summary.monthly.balance_cents)}",
        f"Ano — receita {_format_cents(summary.yearly.income_total_cents)}, "
        f"despesas {_format_cents(summary.yearly.expense_total_cents)}, "
        f"saldo {_format_cents(summary.yearly.balance_cents)}",
        f"Reserva de emergência — saldo {_format_cents(summary.emergency_reserve.balance_cents)}, "
        "despesa média/mês "
        f"{_format_cents(summary.emergency_reserve.average_monthly_expense_cents)}, "
        "meses cobertos "
        + (
            f"{summary.emergency_reserve.months_covered:.1f}"
            if summary.emergency_reserve.months_covered is not None
            else "indisponível"
        ),
    ]
    if summary.category_card_breakdown:
        lines.append("Gasto por categoria e cartão no mês:")
        for item in summary.category_card_breakdown:
            lines.append(
                f"  - {item.category_name} em {item.card_name}: {_format_cents(item.total_cents)}"
            )
    return "\n".join(lines)


async def _exec_get_emergency_reserve(session: AsyncSession, _args: dict) -> str:
    result = await session.exec(select(EmergencyReserve))
    reserves = result.all()
    if not reserves:
        return "Nenhuma reserva de emergência cadastrada."
    lines = [
        f"- {reserve.institution}: {_format_cents(reserve.balance_cents)} "
        f"({reserve.cdi_percentage:.0f}% do CDI)"
        for reserve in reserves
    ]
    return "\n".join(lines)


async def _exec_get_transactions(session: AsyncSession, args: dict) -> str:
    statement = select(Transaction).where(Transaction.status == TransactionStatus.CONFIRMED)
    if args.get("year") is not None:
        statement = statement.where(func.strftime("%Y", Transaction.date) == f"{args['year']:04d}")
    if args.get("month") is not None:
        statement = statement.where(func.strftime("%m", Transaction.date) == f"{args['month']:02d}")
    if args.get("card_id") is not None:
        statement = statement.where(Transaction.card_id == args["card_id"])
    if args.get("search"):
        statement = statement.where(
            func.lower(Transaction.description).contains(args["search"].strip().lower())
        )
    statement = statement.order_by(Transaction.date).limit(100)

    result = await session.exec(statement)
    transactions = result.all()
    if not transactions:
        return "Nenhuma transação encontrada com esses filtros."
    lines = [
        f"- {t.date.isoformat()}: {t.description} — {_format_cents(t.amount_cents)}"
        for t in transactions
    ]
    return "\n".join(lines)


_EXECUTORS: dict[str, ToolExecutor] = {
    "get_portfolio": _exec_get_portfolio,
    "get_monthly_summary": _exec_get_monthly_summary,
    "get_financial_summary": _exec_get_financial_summary,
    "get_emergency_reserve": _exec_get_emergency_reserve,
    "get_transactions": _exec_get_transactions,
}


async def execute_tool(session: AsyncSession, name: str, arguments: dict) -> str:
    executor = _EXECUTORS.get(name)
    if executor is None:
        return f"Ferramenta desconhecida: {name}"
    try:
        return await executor(session, arguments)
    except (KeyError, ValueError, TypeError) as exc:
        return f"Erro ao executar {name}: {exc}"
