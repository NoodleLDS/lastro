from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lastro.api.admin import router as admin_router
from lastro.api.allocation_targets import router as allocation_targets_router
from lastro.api.analyst import router as analyst_router
from lastro.api.auth import router as auth_router
from lastro.api.cards import router as cards_router
from lastro.api.categories import router as categories_router
from lastro.api.contributions import router as contributions_router
from lastro.api.dashboard import router as dashboard_router
from lastro.api.demo import router as demo_router
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
from lastro.core.config import settings
from lastro.core.logging import configure_logging
from lastro.db import get_session
from lastro.services.analytics.snapshot import record_monthly_snapshot
from lastro.services.auth.bootstrap import ensure_admin_user
from lastro.services.auth.security import decode_access_token
from lastro.services.demo import seed as demo_seed

PUBLIC_PATHS = {"/health", "/auth/login", "/docs", "/openapi.json", "/demo/reset"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    async for session in get_session():
        await ensure_admin_user(session)
        if settings.demo_mode and await demo_seed.is_empty(session):
            await demo_seed.run(session)
        await record_monthly_snapshot(session)
    yield


app = FastAPI(title="Lastro", lifespan=lifespan)


@app.middleware("http")
async def require_auth(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    username = decode_access_token(token) if token else None
    if username is None:
        return JSONResponse(status_code=401, content={"detail": "não autenticado"})

    return await call_next(request)


_CORS_ORIGINS = [
    "http://localhost:5180",
    "https://noodlelds.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(demo_router)
app.include_router(admin_router)
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
