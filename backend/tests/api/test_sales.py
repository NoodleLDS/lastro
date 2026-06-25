from httpx import AsyncClient


async def _create_position(client: AsyncClient, quantity: float = 100) -> dict:
    response = await client.post(
        "/positions",
        json={
            "ticker": "CPTS11",
            "name": "Capitania Securities II",
            "asset_type": "fii",
            "quantity": quantity,
        },
    )
    return response.json()


async def test_create_sale_reduz_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=100)

    created = await client.post(
        "/sales",
        json={
            "position_id": position["id"],
            "date": "2026-02-01",
            "quantity": 30,
            "unit_price_cents": 950,
        },
    )
    assert created.status_code == 201

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 70


async def test_delete_sale_devolve_quantity_da_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=100)

    created = (
        await client.post(
            "/sales",
            json={
                "position_id": position["id"],
                "date": "2026-02-01",
                "quantity": 30,
                "unit_price_cents": 950,
            },
        )
    ).json()

    await client.delete(f"/sales/{created['id']}")

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 100


async def test_list_sales_filtra_por_position_id(client: AsyncClient) -> None:
    position = await _create_position(client)

    await client.post(
        "/sales",
        json={
            "position_id": position["id"],
            "date": "2026-02-01",
            "quantity": 10,
            "unit_price_cents": 950,
        },
    )

    response = await client.get("/sales", params={"position_id": position["id"]})
    assert len(response.json()) == 1


async def test_delete_sale_not_found(client: AsyncClient) -> None:
    response = await client.delete("/sales/999")
    assert response.status_code == 404


async def test_create_sale_rejeita_quantity_maior_que_posicao(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=25)

    response = await client.post(
        "/sales",
        json={
            "position_id": position["id"],
            "date": "2026-02-01",
            "quantity": 1000,
            "unit_price_cents": 950,
        },
    )
    assert response.status_code == 422

    positions = (await client.get("/positions")).json()
    assert positions[0]["quantity"] == 25


async def test_create_sale_rejeita_quantity_zero_ou_negativa(client: AsyncClient) -> None:
    position = await _create_position(client, quantity=25)

    for quantity in (0, -5):
        response = await client.post(
            "/sales",
            json={
                "position_id": position["id"],
                "date": "2026-02-01",
                "quantity": quantity,
                "unit_price_cents": 950,
            },
        )
        assert response.status_code == 422


async def test_create_sale_rejeita_position_id_inexistente(client: AsyncClient) -> None:
    response = await client.post(
        "/sales",
        json={
            "position_id": 9999,
            "date": "2026-02-01",
            "quantity": 1,
            "unit_price_cents": 950,
        },
    )
    assert response.status_code == 422
