from datetime import date, timedelta

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.allocation_target import AllocationTarget
from lastro.models.card import Card
from lastro.models.category import Category
from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.emergency_reserve import EmergencyReserve
from lastro.models.fixed_expense import FixedExpense
from lastro.models.income import Income
from lastro.models.position import Position
from lastro.models.price_snapshot import PriceSnapshot
from lastro.models.transaction import Transaction
from lastro.models.variable_expense import VariableExpense
from lastro.schemas.dashboard import EvolutionResponse, ProjectionResponse
from lastro.services.analytics.allocation import AllocationBreakdown, calculate_allocation
from lastro.services.analytics.evolution import (
    calculate_benchmark_comparison,
    calculate_portfolio_evolution,
)
from lastro.services.analytics.financial_summary import (
    RESERVE_AVERAGE_EXPENSE_MONTHS,
    FinancialSummary,
    calculate_category_card_breakdown,
    calculate_emergency_reserve_summary,
    calculate_monthly_totals,
    calculate_yearly_totals,
)
from lastro.services.analytics.fire import FireResult, calculate_dividend_yield_pct, calculate_fire
from lastro.services.analytics.projection import project_portfolio_value
from lastro.services.quotes.bcb import BCBProvider

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = structlog.get_logger()

_CDI_SERIES_CODE = 12
_BCB_UNAVAILABLE_DETAIL = (
    "Serviço de cotações do Banco Central (BCB) indisponível, tente novamente em breve."
)


@router.get("/evolution", response_model=EvolutionResponse)
async def get_evolution(session: AsyncSession = Depends(get_session)) -> EvolutionResponse:
    result = await session.exec(select(PriceSnapshot))
    snapshots = result.all()
    points = calculate_portfolio_evolution(snapshots)

    comparison = None
    if len(snapshots) >= 2:
        ordered = sorted(snapshots, key=lambda s: s.month)
        bcb = BCBProvider()
        try:
            cdi_accumulated_pct = await bcb.get_accumulated_rate(
                series_code=_CDI_SERIES_CODE, start=ordered[0].month, end=ordered[-1].month
            )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("bcb_indisponivel", error=str(exc))
            raise HTTPException(status_code=503, detail=_BCB_UNAVAILABLE_DETAIL) from exc

        ivvb11_result = await session.exec(
            select(Position).where(Position.ticker == "IVVB11", Position.is_active.is_(True))
        )
        ivvb11 = ivvb11_result.first()

        ivvb11_first_price_cents = None
        ivvb11_current_price_cents = None
        if ivvb11 is not None:
            contributions_result = await session.exec(
                select(Contribution)
                .where(Contribution.position_id == ivvb11.id)
                .order_by(Contribution.date)
            )
            contributions = contributions_result.all()
            if contributions:
                ivvb11_first_price_cents = contributions[0].unit_price_cents
            ivvb11_current_price_cents = ivvb11.last_price_cents

        comparison = calculate_benchmark_comparison(
            snapshots, cdi_accumulated_pct, ivvb11_first_price_cents, ivvb11_current_price_cents
        )

    return EvolutionResponse(points=points, comparison=comparison)


@router.get("/allocation", response_model=list[AllocationBreakdown])
async def get_allocation(
    session: AsyncSession = Depends(get_session),
) -> list[AllocationBreakdown]:
    positions_result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = positions_result.all()

    targets_result = await session.exec(select(AllocationTarget))
    targets = targets_result.all()

    return calculate_allocation(positions, targets)


@router.get("/projection", response_model=ProjectionResponse)
async def get_projection(
    monthly_contribution_cents: int,
    monthly_return_rate: float,
    months: int,
    session: AsyncSession = Depends(get_session),
) -> ProjectionResponse:
    positions_result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = positions_result.all()
    current_value_cents = sum(
        round(position.quantity * position.last_price_cents)
        for position in positions
        if position.last_price_cents is not None
    )

    values = project_portfolio_value(
        current_value_cents, monthly_contribution_cents, monthly_return_rate, months
    )
    return ProjectionResponse(values_cents=values)


@router.get("/fire-simulator", response_model=FireResult)
async def get_fire_simulator(
    target_monthly_expense_cents: int,
    session: AsyncSession = Depends(get_session),
) -> FireResult:
    positions_result = await session.exec(select(Position).where(Position.is_active.is_(True)))
    positions = positions_result.all()
    portfolio_value_cents = sum(
        round(position.quantity * position.last_price_cents)
        for position in positions
        if position.last_price_cents is not None
    )

    one_year_ago = date.today() - timedelta(days=365)
    dividends_result = await session.exec(select(Dividend).where(Dividend.date >= one_year_ago))
    dividends = dividends_result.all()
    dividends_last_12m_cents = sum(d.amount_cents for d in dividends)

    dividend_yield_pct = calculate_dividend_yield_pct(
        dividends_last_12m_cents, portfolio_value_cents
    )

    bcb = BCBProvider()
    try:
        ipca_pct = await bcb.get_ipca_rate()
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
        logger.warning("bcb_indisponivel", error=str(exc))
        raise HTTPException(status_code=503, detail=_BCB_UNAVAILABLE_DETAIL) from exc

    return calculate_fire(
        portfolio_value_cents, dividend_yield_pct, ipca_pct, target_monthly_expense_cents
    )


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


async def _transactions_between(session: AsyncSession, start: date, end: date) -> list[Transaction]:
    result = await session.exec(
        select(Transaction).where(Transaction.date >= start, Transaction.date < end)
    )
    return list(result.all())


@router.get("/financial-summary", response_model=FinancialSummary)
async def get_financial_summary(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
) -> FinancialSummary:
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
