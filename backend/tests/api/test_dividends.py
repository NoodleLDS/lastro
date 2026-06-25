from httpx import AsyncClient


async def _create_position(client: AsyncClient) -> dict:
    response = await client.post(
        "/positions",
        json={"ticker": "BBAS3", "name": "Banco do Brasil", "asset_type": "stock", "quantity": 311},
    )
    return response.json()


async def test_create_list_delete_dividend(client: AsyncClient) -> None:
    position = await _create_position(client)

    created = await client.post(
        "/dividends",
        json={"position_id": position["id"], "date": "2026-01-01", "amount_cents": 15550},
    )
    assert created.status_code == 201
    dividend = created.json()

    response = await client.get("/dividends", params={"position_id": position["id"]})
    assert len(response.json()) == 1

    response = await client.delete(f"/dividends/{dividend['id']}")
    assert response.status_code == 204

    response = await client.get("/dividends", params={"position_id": position["id"]})
    assert response.json() == []


async def test_delete_dividend_not_found(client: AsyncClient) -> None:
    response = await client.delete("/dividends/999")
    assert response.status_code == 404


async def test_create_dividend_rejeita_position_id_inexistente(client: AsyncClient) -> None:
    response = await client.post(
        "/dividends", json={"position_id": 9999, "date": "2026-01-01", "amount_cents": 100}
    )
    assert response.status_code == 422
