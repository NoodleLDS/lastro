from fastapi import APIRouter, Header, HTTPException
from sqlmodel import SQLModel

from lastro.core.config import settings
from lastro.db import engine, get_session
from lastro.services.demo import seed as demo_seed

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset")
async def reset_demo(x_reset_secret: str = Header(default="")) -> dict[str, str]:
    """Drop all data and re-seed. Protected by X-Reset-Secret header."""
    if not settings.demo_mode:
        raise HTTPException(status_code=404, detail="not found")
    if not settings.demo_reset_secret or x_reset_secret != settings.demo_reset_secret:
        raise HTTPException(status_code=403, detail="forbidden")

    async with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(table.delete())

    async for session in get_session():
        await demo_seed.run(session)

    return {"status": "reset ok"}
