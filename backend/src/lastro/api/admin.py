import httpx
import structlog
from fastapi import APIRouter

from lastro.core.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])


async def _trigger_launcher(path: str) -> None:
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{settings.launcher_url}{path}", timeout=5)
        except httpx.HTTPError as exc:
            logger.warning("admin.launcher_unreachable", path=path, error=str(exc))


@router.post("/restart")
async def restart_containers() -> dict[str, str]:
    await _trigger_launcher("/restart")
    return {"status": "restarting"}


@router.post("/shutdown")
async def shutdown_containers() -> dict[str, str]:
    await _trigger_launcher("/shutdown")
    return {"status": "shutting down"}
