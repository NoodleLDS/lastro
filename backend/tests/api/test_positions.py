from httpx import AsyncClient


async def _create_position(
    client: AsyncClient, ticker: str = "BBAS3", asset_type: str = "stock", quantity: float = 311
) -> dict:
    response = await client.post(
        "/positions",
        json={
            "ticker": ticker,
            "name": "Banco do Brasil",
            "asset_type": asset_type,
            "quantity": quantity,
        },
    )
    return response.json()


async def test_create_and_list_position(client: AsyncClient) -> None:
    created = await _create_position(client)
    assert created["ticker"] == "BBAS3"
    assert created["average_price_cents"] == 0
    assert created["total_return"] is None

    response = await client.get("/positions")
    assert response.status_code == 200
    assert [p["ticker"] for p in response.json()] == ["BBAS3"]


async def test_average_price_calculado_apos_aportes(client: AsyncClient) -> None:
    position = await _create_position(client)

    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 200,
            "unit_price_cents": 1800,
        },
    )
    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-02-01",
            "quantity": 111,
            "unit_price_cents": 2000,
        },
    )

    response = await client.get("/positions")
    body = response.json()[0]
    assert body["average_price_cents"] == 1871


async def test_deactivate_position_is_soft_delete(client: AsyncClient) -> None:
    position = await _create_position(client)

    response = await client.delete(f"/positions/{position['id']}")
    assert response.status_code == 204

    response = await client.get("/positions")
    assert response.json() == []


async def test_deactivate_position_not_found(client: AsyncClient) -> None:
    response = await client.delete("/positions/999")
    assert response.status_code == 404


async def test_contribution_aumenta_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=0)

    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 50,
            "unit_price_cents": 1800,
        },
    )

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 50


async def test_delete_contribution_reverte_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=0)

    created = (
        await client.post(
            "/contributions",
            json={
                "position_id": position["id"],
                "date": "2026-01-01",
                "quantity": 50,
                "unit_price_cents": 1800,
            },
        )
    ).json()

    await client.delete(f"/contributions/{created['id']}")

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 0


async def test_history_combina_contribution_sale_e_dividend_ordenado_por_data(
    client: AsyncClient,
) -> None:
    position = await _create_position(client, quantity=0)

    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-10",
            "quantity": 100,
            "unit_price_cents": 1800,
        },
    )
    await client.post(
        "/sales",
        json={
            "position_id": position["id"],
            "date": "2026-02-15",
            "quantity": 30,
            "unit_price_cents": 2000,
        },
    )
    await client.post(
        "/dividends",
        json={"position_id": position["id"], "date": "2026-03-01", "amount_cents": 500},
    )

    response = await client.get(f"/positions/{position['id']}/history")
    assert response.status_code == 200
    body = response.json()

    assert [e["type"] for e in body["events"]] == ["contribution", "sale", "dividend"]
    assert [e["date"] for e in body["events"]] == ["2026-01-10", "2026-02-15", "2026-03-01"]

    # cada Contribution/Sale gera um ponto no histórico de preço
    assert len(body["price_history"]) == 2
    assert body["price_history"][0]["price_cents"] == 1800
    assert body["price_history"][1]["price_cents"] == 2000


async def test_history_position_not_found(client: AsyncClient) -> None:
    response = await client.get("/positions/999/history")
    assert response.status_code == 404
