from httpx import AsyncClient


async def _create_position(client: AsyncClient) -> dict:
    response = await client.post(
        "/positions",
        json={"ticker": "BBAS3", "name": "Banco do Brasil", "asset_type": "stock", "quantity": 311},
    )
    return response.json()


async def test_create_list_delete_contribution(client: AsyncClient) -> None:
    position = await _create_position(client)

    created = await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": 200,
            "unit_price_cents": 1800,
        },
    )
    assert created.status_code == 201
    contribution = created.json()

    response = await client.get("/contributions", params={"position_id": position["id"]})
    assert len(response.json()) == 1

    response = await client.delete(f"/contributions/{contribution['id']}")
    assert response.status_code == 204

    response = await client.get("/contributions", params={"position_id": position["id"]})
    assert response.json() == []


async def test_delete_contribution_not_found(client: AsyncClient) -> None:
    response = await client.delete("/contributions/999")
    assert response.status_code == 404


async def test_distribute_retorna_preview_sem_gravar_nada(client: AsyncClient) -> None:
    await client.post(
        "/positions",
        json={
            "ticker": "CPTS11",
            "name": "Capitania Securities II",
            "asset_type": "fii",
            "quantity": 100,
        },
    )

    response = await client.post("/contributions/distribute", json={"total_cents": 100_000})

    assert response.status_code == 200
    body = response.json()
    assert body["total_cents"] == 100_000
    assert any(a["ticker"] == "CPTS11" for a in body["allocations"])

    contributions = (await client.get("/contributions")).json()
    assert contributions == []


async def test_distribute_rejeita_valor_nao_positivo(client: AsyncClient) -> None:
    response = await client.post("/contributions/distribute", json={"total_cents": 0})

    assert response.status_code == 422


async def test_create_contribution_rejeita_quantity_negativa(client: AsyncClient) -> None:
    position = await _create_position(client)

    response = await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": "2026-01-01",
            "quantity": -10,
            "unit_price_cents": 1800,
        },
    )
    assert response.status_code == 422


async def test_create_contribution_rejeita_unit_price_cents_nao_positivo(
    client: AsyncClient,
) -> None:
    position = await _create_position(client)

    for unit_price_cents in (0, -100):
        response = await client.post(
            "/contributions",
            json={
                "position_id": position["id"],
                "date": "2026-01-01",
                "quantity": 10,
                "unit_price_cents": unit_price_cents,
            },
        )
        assert response.status_code == 422


async def test_create_contribution_rejeita_position_id_inexistente(client: AsyncClient) -> None:
    response = await client.post(
        "/contributions",
        json={
            "position_id": 9999,
            "date": "2026-01-01",
            "quantity": 10,
            "unit_price_cents": 1800,
        },
    )
    assert response.status_code == 422
