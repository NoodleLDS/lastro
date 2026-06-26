from datetime import date as date_
from enum import StrEnum

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.schemas.report import Report, ReportModule
from lastro.services.analytics.report import build_report, render_xlsx

router = APIRouter(prefix="/reports", tags=["reports"])

ALL_MODULES = list(ReportModule)


class ReportFormat(StrEnum):
    JSON = "json"
    XLSX = "xlsx"


@router.get("", response_model=Report)
async def get_report(
    modules: list[ReportModule] | None = Query(default=None),  # noqa: B008
    date_from: date_ | None = None,
    date_to: date_ | None = None,
    category_id: int | None = None,
    format: ReportFormat = ReportFormat.JSON,
    session: AsyncSession = Depends(get_session),
) -> Report | Response:
    report = await build_report(
        session, modules if modules is not None else ALL_MODULES, date_from, date_to, category_id
    )

    if format == ReportFormat.XLSX:
        content = render_xlsx(report)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=relatorio-lastro.xlsx"},
        )

    return report
