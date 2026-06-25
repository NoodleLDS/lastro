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


async def test_categorization_stats_vazio_sem_transacoes(client: AsyncClient) -> None:
    stats = (await client.get("/transactions/categorization-stats")).json()

    assert stats == {
        "total": 0,
        "by_rule": 0,
        "by_llm": 0,
        "by_manual": 0,
        "uncategorized": 0,
        "resolved_without_ai_pct": None,
    }


async def test_categorization_stats_conta_cada_origem_corretamente(client: AsyncClient) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    transporte = (await client.post("/categories", json={"name": "transporte"})).json()
    await client.post("/categories", json={"name": "Alimentação"})

    # primeira "uber" sem categoria, depois categorizada via PATCH -> aprende a regra
    first_uber = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "uber 10", "date": "2026-06-10"},
        )
    ).json()
    await client.patch(
        f"/transactions/{first_uber['transaction']['id']}",
        json={"category_id": transporte["id"]},
    )
    # agora "uber" tem uma MerchantRule -> resolvido por RULE
    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "uber 20", "date": "2026-06-11"},
    )

    # resolvido por LLM
    app.dependency_overrides[get_ollama_provider] = lambda: _StubLLM("Alimentação")
    try:
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "zebu 22", "date": "2026-06-12"},
        )
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    # sem categoria (LLM não decide)
    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "mercado xyz 5", "date": "2026-06-13"},
    )

    # categorizado manualmente via PATCH
    created = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "posto raro 30", "date": "2026-06-14"},
        )
    ).json()
    await client.patch(
        f"/transactions/{created['transaction']['id']}",
        json={"category_id": transporte["id"]},
    )

    stats = (await client.get("/transactions/categorization-stats")).json()

    assert stats["total"] == 5
    assert stats["by_manual"] == 2  # "#transporte" + PATCH manual
    assert stats["by_rule"] == 1  # segundo "uber"
    assert stats["by_llm"] == 1  # "zebu"
    assert stats["uncategorized"] == 1  # "mercado xyz"
    assert stats["resolved_without_ai_pct"] == 60.0  # (2 manual + 1 rule) / 5


async def test_categorization_stats_filtra_por_ano_e_mes(client: AsyncClient) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()

    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "mercado 5", "date": "2026-06-10"},
    )
    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "mercado 5", "date": "2026-07-10"},
    )

    stats_junho = (
        await client.get("/transactions/categorization-stats", params={"year": 2026, "month": 6})
    ).json()

    assert stats_junho["total"] == 1
