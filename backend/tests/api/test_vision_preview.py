from datetime import date

import pytest
from httpx import AsyncClient

from lastro.core.config import settings
from lastro.main import app
from lastro.services.llm.dependency import get_llm_provider
from lastro.services.llm.provider import VisionExtractedItem


class _FakeLLMProvider:
    def __init__(self, items: list[VisionExtractedItem]) -> None:
        self._items = items

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        return self._items


@pytest.fixture(autouse=True)
def _clear_llm_override():
    yield
    app.dependency_overrides.pop(get_llm_provider, None)


def _override_llm(items: list[VisionExtractedItem]) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: _FakeLLMProvider(items)


async def _create_card(client: AsyncClient) -> dict:
    return (await client.post("/cards", json={"name": "Nubank"})).json()


async def test_vision_preview_cria_transacoes_pending_review(client: AsyncClient) -> None:
    card = await _create_card(client)
    _override_llm(
        [
            VisionExtractedItem(description="uber viagem", amount_cents=2200),
            VisionExtractedItem(description="ifood almoco", amount_cents=4500),
        ]
    )

    response = await client.post(
        "/transactions/vision-preview",
        params={"card_id": card["id"]},
        files={"file": ("fatura.png", b"fake-image-bytes", "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 2
    assert all(t["status"] == "pending_review" for t in body)
    assert all(t["source"] == "vision_preview" for t in body)


async def test_vision_preview_nao_aparece_na_listagem_default(client: AsyncClient) -> None:
    card = await _create_card(client)
    _override_llm([VisionExtractedItem(description="uber viagem", amount_cents=2200)])

    await client.post(
        "/transactions/vision-preview",
        params={"card_id": card["id"]},
        files={"file": ("fatura.png", b"fake-image-bytes", "image/png")},
    )

    response = await client.get("/transactions", params={"card_id": card["id"]})
    assert response.json() == []

    response = await client.get(
        "/transactions", params={"card_id": card["id"], "status": "pending_review"}
    )
    assert len(response.json()) == 1


async def test_vision_preview_claude_sem_chave_configurada_retorna_400(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    card = await _create_card(client)
    monkeypatch.setattr(settings, "llm_provider", "claude")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    app.dependency_overrides.pop(get_llm_provider, None)

    response = await client.post(
        "/transactions/vision-preview",
        params={"card_id": card["id"]},
        files={"file": ("fatura.png", b"fake-image-bytes", "image/png")},
    )
    assert response.status_code == 400


async def test_confirm_transaction_muda_status_e_projeta_parcela(client: AsyncClient) -> None:
    card = await _create_card(client)
    _override_llm(
        [VisionExtractedItem(description="tablet 3/9", amount_cents=33598, date=date(2026, 6, 10))]
    )

    created = (
        await client.post(
            "/transactions/vision-preview",
            params={"card_id": card["id"]},
            files={"file": ("fatura.png", b"fake-image-bytes", "image/png")},
        )
    ).json()
    transaction_id = created[0]["id"]

    await client.patch(
        f"/transactions/{transaction_id}",
        json={"description": "tablet", "installment_current": 3, "installment_total": 9},
    )

    response = await client.post(f"/transactions/{transaction_id}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    listed = await client.get("/transactions", params={"card_id": card["id"]})
    assert len(listed.json()) == 7


async def test_confirm_batch_confirma_multiplas(client: AsyncClient) -> None:
    card = await _create_card(client)
    _override_llm(
        [
            VisionExtractedItem(description="uber viagem", amount_cents=2200),
            VisionExtractedItem(description="ifood almoco", amount_cents=4500),
        ]
    )

    created = (
        await client.post(
            "/transactions/vision-preview",
            params={"card_id": card["id"]},
            files={"file": ("fatura.png", b"fake-image-bytes", "image/png")},
        )
    ).json()
    ids = [t["id"] for t in created]

    response = await client.post("/transactions/confirm-batch", json={"ids": ids})
    assert response.status_code == 200
    assert all(t["status"] == "confirmed" for t in response.json())

    listed = await client.get("/transactions", params={"card_id": card["id"]})
    assert len(listed.json()) == 2
