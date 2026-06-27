from httpx import AsyncClient


async def test_create_and_list_emergency_reserve(client: AsyncClient) -> None:
    response = await client.post(
        "/emergency-reserve",
        json={"institution": "Inter", "balance_cents": 1_200_000, "cdi_percentage": 100.0},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["institution"] == "Inter"

    response = await client.get("/emergency-reserve")
    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == [created["id"]]


async def test_update_and_delete_emergency_reserve(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/emergency-reserve",
            json={"institution": "Inter", "balance_cents": 1_200_000, "cdi_percentage": 100.0},
        )
    ).json()

    response = await client.patch(
        f"/emergency-reserve/{created['id']}", json={"balance_cents": 1_300_000}
    )
    assert response.status_code == 200
    assert response.json()["balance_cents"] == 1_300_000

    response = await client.delete(f"/emergency-reserve/{created['id']}")
    assert response.status_code == 204

    response = await client.get("/emergency-reserve")
    assert response.json() == []


async def test_update_emergency_reserve_not_found(client: AsyncClient) -> None:
    response = await client.patch("/emergency-reserve/999", json={"balance_cents": 1})
    assert response.status_code == 404


async def test_delete_emergency_reserve_not_found(client: AsyncClient) -> None:
    response = await client.delete("/emergency-reserve/999")
    assert response.status_code == 404
