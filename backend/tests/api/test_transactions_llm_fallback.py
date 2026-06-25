from httpx import AsyncClient

from lastro.main import app
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.provider import VisionExtractedItem
from tests.conftest import NullCategorizationProvider


class _StubLLM:
    def __init__(self, category_name: str | None) -> None:
        self._category_name = category_name

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return self._category_name


async def test_quick_entry_usa_fallback_llm_quando_nenhuma_regra_combina(
    client: AsyncClient,
) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    category = (await client.post("/categories", json={"name": "Alimentação"})).json()

    app.dependency_overrides[get_ollama_provider] = lambda: _StubLLM("Alimentação")
    try:
        created = (
            await client.post(
                "/transactions/quick-entry",
                json={"card_id": card["id"], "raw": "zebu 22", "date": "2026-06-10"},
            )
        ).json()
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert created["transaction"]["category_id"] == category["id"]

    rules = (await client.get("/merchant-rules")).json()
    assert any(r["pattern"] == "zebu" for r in rules)


async def test_quick_entry_sem_categoria_quando_llm_nao_decide(client: AsyncClient) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    await client.post("/categories", json={"name": "Alimentação"})

    created = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "mercado xyz 22", "date": "2026-06-10"},
        )
    ).json()

    assert created["transaction"]["category_id"] is None
