from pydantic import BaseModel


class FireResult(BaseModel):
    annualized_dividend_yield_pct: float
    safe_withdrawal_rate_pct: float
    sustainable_monthly_income_cents: int
    has_reached_target: bool
    required_portfolio_cents: int | None
    missing_portfolio_cents: int | None


def calculate_dividend_yield_pct(
    dividends_last_12m_cents: int, portfolio_value_cents: int
) -> float:
    if portfolio_value_cents == 0:
        return 0.0
    return dividends_last_12m_cents / portfolio_value_cents * 100


def calculate_fire(
    portfolio_value_cents: int,
    dividend_yield_pct: float,
    ipca_pct: float,
    target_monthly_expense_cents: int,
) -> FireResult:
    """Taxa de retirada segura = yield - inflação (CLAUDE.md). Renda mensal
    sustentável = patrimônio × taxa de retirada segura / 12.

    Quando a taxa de retirada segura é positiva, calcula o patrimônio
    necessário pra sustentar o gasto mensal alvo e quanto falta hoje. Não
    projeta "em quantos meses" — isso exigiria taxa de aporte/retorno
    esperado que não é input deste simulador (ver simulador de Projeção)."""
    safe_withdrawal_rate_pct = dividend_yield_pct - ipca_pct
    sustainable_monthly_income_cents = round(
        portfolio_value_cents * (safe_withdrawal_rate_pct / 100) / 12
    )

    required_portfolio_cents = None
    missing_portfolio_cents = None
    has_reached_target = sustainable_monthly_income_cents >= target_monthly_expense_cents

    if safe_withdrawal_rate_pct > 0:
        required_portfolio_cents = round(
            target_monthly_expense_cents * 12 / (safe_withdrawal_rate_pct / 100)
        )
        missing_portfolio_cents = max(0, required_portfolio_cents - portfolio_value_cents)

    return FireResult(
        annualized_dividend_yield_pct=dividend_yield_pct,
        safe_withdrawal_rate_pct=safe_withdrawal_rate_pct,
        sustainable_monthly_income_cents=sustainable_monthly_income_cents,
        has_reached_target=has_reached_target,
        required_portfolio_cents=required_portfolio_cents,
        missing_portfolio_cents=missing_portfolio_cents,
    )
