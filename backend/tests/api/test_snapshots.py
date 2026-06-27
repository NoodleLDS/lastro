import pytest
from httpx import AsyncClient

from lastro.services.quotes.provider import Quote


class _FakeQuoteProvider:
    def __init__(self, price_cents: int) -> None:
        self._price_cents = price_cents

    async def get_quote(self, ticker: str) -> Quote:
        return Quote(ticker=ticker, price_cents=self._price_cents)


async def test_create_snapshot_inclui_carteira_e_reserva(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    position = (
        await client.post(
            "/positions",
            json={"ticker": "BBAS3", "name": "Banco do Brasil", "asset_type": "stock"},
        )
    ).json()
    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 311,
            "unit_price_cents": 1000,
        },
    )

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1986),
    )
    await client.post("/positions/refresh-quotes")

    response = await client.post("/snapshots")
    assert response.status_code == 201
    body = response.json()
    assert body["portfolio_value_cents"] == round(311 * 1986)
    assert body["emergency_reserve_value_cents"] == 0


async def test_create_snapshot_no_mesmo_mes_atualiza_em_vez_de_duplicar(
    client: AsyncClient,
) -> None:
    await client.post(
        "/positions",
        json={"ticker": "BBAS3", "name": "Banco do Brasil", "asset_type": "stock", "quantity": 311},
    )

    first = await client.post("/snapshots")
    second = await client.post("/snapshots")

    assert first.json()["id"] == second.json()["id"]

    listed = await client.get("/snapshots")
    assert len(listed.json()) == 1
