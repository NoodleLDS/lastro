from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.db import get_session
from lastro.main import app
from lastro.services.auth.security import create_access_token
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.provider import VisionExtractedItem


class NullCategorizationProvider:
    """Stub usado por padrão nos testes: nunca resolve categoria via IA, sem rede."""

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return None

    async def complete(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()
    transport = ASGITransport(app=app)
    token = create_access_token("admin")
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client

    app.dependency_overrides.clear()
