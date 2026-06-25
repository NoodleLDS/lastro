from httpx import AsyncClient


async def test_create_and_list_card(client: AsyncClient) -> None:
    response = await client.post("/cards", json={"name": "Nubank", "color": "#820ad1"})
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Nubank"
    assert created["is_active"] is True

    response = await client.get("/cards")
    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Nubank"]


async def test_update_card(client: AsyncClient) -> None:
    created = (await client.post("/cards", json={"name": "Inter"})).json()

    response = await client.put(f"/cards/{created['id']}", json={"color": "#ff7a00"})
    assert response.status_code == 200
    assert response.json()["color"] == "#ff7a00"
    assert response.json()["name"] == "Inter"


async def test_update_card_not_found(client: AsyncClient) -> None:
    response = await client.put("/cards/999", json={"name": "X"})
    assert response.status_code == 404


async def test_deactivate_card_is_soft_delete(client: AsyncClient) -> None:
    created = (await client.post("/cards", json={"name": "Santander"})).json()

    response = await client.delete(f"/cards/{created['id']}")
    assert response.status_code == 204

    response = await client.get("/cards")
    assert created["id"] not in [c["id"] for c in response.json()]

    response = await client.get("/cards", params={"include_inactive": True})
    assert created["id"] in [c["id"] for c in response.json()]


async def test_deactivate_card_not_found(client: AsyncClient) -> None:
    response = await client.delete("/cards/999")
    assert response.status_code == 404
