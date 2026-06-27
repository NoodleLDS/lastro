from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lastro.api.allocation_targets import router as allocation_targets_router
from lastro.api.analyst import router as analyst_router
from lastro.api.cards import router as cards_router
from lastro.api.categories import router as categories_router
from lastro.api.contributions import router as contributions_router
from lastro.api.dashboard import router as dashboard_router
from lastro.api.dividends import router as dividends_router
from lastro.api.emergency_reserve import router as emergency_reserve_router
from lastro.api.health import router as health_router
from lastro.api.merchant_rules import router as merchant_rules_router
from lastro.api.monthly_summary import router as monthly_summary_router
from lastro.api.positions import router as positions_router
from lastro.api.reports import router as reports_router
from lastro.api.sales import router as sales_router
from lastro.api.snapshots import router as snapshots_router
from lastro.api.stock_splits import router as stock_splits_router
from lastro.api.transactions import router as transactions_router
from lastro.core.logging import configure_logging
from lastro.db import get_session
from lastro.services.analytics.snapshot import record_monthly_snapshot


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    async for session in get_session():
        await record_monthly_snapshot(session)
    yield


app = FastAPI(title="Lastro", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(cards_router)
app.include_router(categories_router)
app.include_router(merchant_rules_router)
app.include_router(transactions_router)
app.include_router(positions_router)
app.include_router(contributions_router)
app.include_router(sales_router)
app.include_router(stock_splits_router)
app.include_router(dividends_router)
app.include_router(emergency_reserve_router)
app.include_router(snapshots_router)
app.include_router(allocation_targets_router)
app.include_router(dashboard_router)
app.include_router(analyst_router)
app.include_router(monthly_summary_router)
app.include_router(reports_router)
