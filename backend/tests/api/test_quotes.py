import pytest
from httpx import AsyncClient

from lastro.services.quotes.provider import Quote


class _FakeQuoteProvider:
    def __init__(
        self,
        price_cents: int,
        price_earnings: float | None = None,
        earnings_per_share: float | None = None,
    ) -> None:
        self._price_cents = price_cents
        self._price_earnings = price_earnings
        self._earnings_per_share = earnings_per_share

    async def get_quote(self, ticker: str) -> Quote:
        return Quote(
            ticker=ticker,
            price_cents=self._price_cents,
            price_earnings=self._price_earnings,
            earnings_per_share=self._earnings_per_share,
        )


async def _create_position(client: AsyncClient, asset_type: str = "stock") -> dict:
    response = await client.post(
        "/positions",
        json={
            "ticker": "BBAS3",
            "name": "Banco do Brasil",
            "asset_type": asset_type,
            "quantity": 311,
        },
    )
    return response.json()


async def test_refresh_quotes_atualiza_preco_e_calcula_total_return(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    position = await _create_position(client)
    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 311,
            "unit_price_cents": 1800,
        },
    )

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1986),
    )

    response = await client.post("/positions/refresh-quotes")
    assert response.status_code == 200
    body = response.json()[0]
    assert body["last_price_cents"] == 1986
    assert body["last_price_fetched_at"] is not None
    assert body["total_return"]["current_value_cents"] == 617646


async def test_refresh_quotes_pula_renda_fixa(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _create_position(client, asset_type="fixed_income")

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1986),
    )

    response = await client.post("/positions/refresh-quotes")
    assert response.status_code == 200
    assert response.json()[0]["last_price_cents"] is None


async def test_refresh_quotes_sem_token_retorna_400(client: AsyncClient) -> None:
    await _create_position(client)

    response = await client.post("/positions/refresh-quotes")
    assert response.status_code == 400


async def test_refresh_quotes_captura_price_earnings_e_lps(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _create_position(client)

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1986, price_earnings=9.03, earnings_per_share=2.22),
    )

    response = await client.post("/positions/refresh-quotes")
    body = response.json()[0]
    assert body["price_earnings"] == 9.03
    assert body["earnings_per_share"] == 2.22


async def test_refresh_quotes_calcula_magic_number_com_dividendos_recentes(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    position = await _create_position(client)
    await client.post(
        "/dividends",
        json={"position_id": position["id"], "date": "2026-06-01", "amount_cents": 1000},
    )

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1000),
    )

    response = await client.post("/positions/refresh-quotes")
    body = response.json()[0]
    assert body["magic_number"]["is_achieved"] is True


async def test_refresh_quotes_magic_number_none_sem_dividendo(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _create_position(client)

    monkeypatch.setattr(
        "lastro.api.positions.get_quote_provider",
        lambda asset_type: _FakeQuoteProvider(1986),
    )

    response = await client.post("/positions/refresh-quotes")
    body = response.json()[0]
    assert body["magic_number"] is None
