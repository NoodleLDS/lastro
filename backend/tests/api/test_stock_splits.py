from httpx import AsyncClient


async def _create_position(client: AsyncClient, quantity: float = 100) -> dict:
    response = await client.post(
        "/positions",
        json={
            "ticker": "CPTS11",
            "name": "Capitania Securities II",
            "asset_type": "fii",
        },
    )
    position = response.json()
    if quantity:
        await client.post(
            "/contributions",
            json={
                "position_id": position["id"],
                "date": "2026-01-01",
                "quantity": quantity,
                "unit_price_cents": 4000,
            },
        )
    return position


async def test_create_stock_split_dobra_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=100)

    created = await client.post(
        "/stock-splits",
        json={
            "position_id": position["id"],
            "date": "2026-03-01",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )
    assert created.status_code == 201

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 200


async def test_delete_stock_split_reverte_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=100)

    created = (
        await client.post(
            "/stock-splits",
            json={
                "position_id": position["id"],
                "date": "2026-03-01",
                "ratio_from": 1,
                "ratio_to": 2,
            },
        )
    ).json()

    await client.delete(f"/stock-splits/{created['id']}")

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 100


async def test_average_price_ajustado_apos_split(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=0)

    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 100,
            "unit_price_cents": 4000,
        },
    )
    await client.post(
        "/stock-splits",
        json={
            "position_id": position["id"],
            "date": "2026-02-01",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 200
    assert positions[0]["average_price_cents"] == 2000


async def test_list_stock_splits_filtra_por_position_id(client: AsyncClient) -> None:
    position = await _create_position(client)

    await client.post(
        "/stock-splits",
        json={
            "position_id": position["id"],
            "date": "2026-03-01",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )

    response = await client.get("/stock-splits", params={"position_id": position["id"]})
    assert len(response.json()) == 1


async def test_create_stock_split_rejeita_ratio_nao_positivo(client: AsyncClient) -> None:
    position = await _create_position(client)

    response = await client.post(
        "/stock-splits",
        json={
            "position_id": position["id"],
            "date": "2026-03-01",
            "ratio_from": 0,
            "ratio_to": 2,
        },
    )
    assert response.status_code == 422


async def test_create_stock_split_rejeita_position_id_inexistente(client: AsyncClient) -> None:
    response = await client.post(
        "/stock-splits",
        json={
            "position_id": 9999,
            "date": "2026-03-01",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )
    assert response.status_code == 422


async def test_delete_stock_split_not_found(client: AsyncClient) -> None:
    response = await client.delete("/stock-splits/999")
    assert response.status_code == 404


async def test_history_inclui_evento_de_stock_split(client: AsyncClient) -> None:
    position = await _create_position(client)

    await client.post(
        "/stock-splits",
        json={
            "position_id": position["id"],
            "date": "2026-03-01",
            "ratio_from": 1,
            "ratio_to": 2,
        },
    )

    history = (await client.get(f"/positions/{position['id']}/history")).json()
    split_events = [e for e in history["events"] if e["type"] == "stock_split"]
    assert len(split_events) == 1
    assert split_events[0]["ratio_from"] == 1
    assert split_events[0]["ratio_to"] == 2
