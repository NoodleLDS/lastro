import pytest
from httpx import AsyncClient

from lastro.services.quotes.provider import Quote


class _FakeQuoteProvider:
    def __init__(self, price_cents: int) -> None:
        self._price_cents = price_cents

    async def get_quote(self, ticker: str) -> Quote:
        return Quote(ticker=ticker, price_cents=self._price_cents)


async def _create_position(
    client: AsyncClient, ticker: str, asset_type: str, quantity: float
) -> dict:
    response = await client.post(
        "/positions",
        json={"ticker": ticker, "name": ticker, "asset_type": asset_type, "quantity": quantity},
    )
    return response.json()


async def test_allocation_endpoint_retorna_breakdown_com_desvio(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _create_position(client, "BBAS3", "stock", 1)
    await _create_position(client, "HGLG11", "fii", 1)

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(3_000_000 if asset_type == "stock" else 5_000_000),
    )
    await client.post("/positions/refresh-quotes")

    await client.post(
        "/allocation-targets", json={"asset_type": "stock", "target_percentage": 30.0}
    )
    await client.post("/allocation-targets", json={"asset_type": "fii", "target_percentage": 70.0})

    response = await client.get("/dashboard/allocation")
    assert response.status_code == 200
    body = {item["asset_type"]: item for item in response.json()}
    assert body["stock"]["current_percentage"] == pytest.approx(37.5)
    assert body["stock"]["is_deviation_alert"] is True


async def test_projection_endpoint(client: AsyncClient) -> None:
    response = await client.get(
        "/dashboard/projection",
        params={"monthly_contribution_cents": 300_000, "monthly_return_rate": 0.008, "months": 12},
    )
    assert response.status_code == 200
    values = response.json()["values_cents"]
    assert len(values) == 13
    assert values[0] == 0


async def test_evolution_endpoint_sem_snapshots(client: AsyncClient) -> None:
    response = await client.get("/dashboard/evolution")
    assert response.status_code == 200
    body = response.json()
    assert body["points"] == []
    assert body["comparison"] is None


async def test_fire_simulator_endpoint(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get_ipca_rate(self) -> float:
        return 4.0

    monkeypatch.setattr("lastro.services.quotes.bcb.BCBProvider.get_ipca_rate", fake_get_ipca_rate)

    response = await client.get(
        "/dashboard/fire-simulator", params={"target_monthly_expense_cents": 500_00}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["safe_withdrawal_rate_pct"] == pytest.approx(-4.0)
    assert body["has_reached_target"] is False
