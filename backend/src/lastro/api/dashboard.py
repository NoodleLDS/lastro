from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.models.allocation_target import AllocationTarget
from lastro.models.contribution import Contribution
from lastro.models.dividend import Dividend
from lastro.models.position import Position
from lastro.models.price_snapshot import PriceSnapshot
from lastro.schemas.dashboard import EvolutionResponse, ProjectionResponse
from lastro.services.analytics.allocation import AllocationBreakdown, calculate_allocation
from lastro.services.analytics.evolution import (
    calculate_benchmark_comparison,
    calculate_portfolio_evolution,
)
from lastro.services.analytics.fire import FireResult, calculate_dividend_yield_pct, calculate_fire
from lastro.services.analytics.projection import project_portfolio_value
from lastro.services.quotes.bcb import BCBProvider

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_CDI_SERIES_CODE = 12


@router.get("/evolution", response_model=EvolutionResponse)
async def get_evolution(session: AsyncSession = Depends(get_session)) -> EvolutionResponse:
    result = await session.exec(select(PriceSnapshot))
    snapshots = result.all()
    points = calculate_portfolio_evolution(snapshots)

    comparison = None
    if len(snapshots) >= 2:
        ordered = sorted(snapshots, key=lambda s: s.month)
        bcb = BCBProvider()
        cdi_accumulated_pct = await bcb.get_accumulated_rate(
            series_code=_CDI_SERIES_CODE, start=ordered[0].month, end=ordered[-1].month
        )

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
    ipca_pct = await bcb.get_ipca_rate()

    return calculate_fire(
        portfolio_value_cents, dividend_yield_pct, ipca_pct, target_monthly_expense_cents
    )
