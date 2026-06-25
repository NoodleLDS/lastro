from httpx import AsyncClient


async def test_create_list_update_delete_allocation_target(client: AsyncClient) -> None:
    created = await client.post(
        "/allocation-targets", json={"asset_type": "stock", "target_percentage": 30.0}
    )
    assert created.status_code == 201
    target = created.json()
    assert target["asset_type"] == "stock"
    assert target["target_percentage"] == 30.0

    response = await client.get("/allocation-targets")
    assert len(response.json()) == 1

    response = await client.put(
        f"/allocation-targets/{target['id']}", json={"target_percentage": 40.0}
    )
    assert response.status_code == 200
    assert response.json()["target_percentage"] == 40.0

    response = await client.delete(f"/allocation-targets/{target['id']}")
    assert response.status_code == 204

    response = await client.get("/allocation-targets")
    assert response.json() == []


async def test_update_allocation_target_not_found(client: AsyncClient) -> None:
    response = await client.put("/allocation-targets/999", json={"target_percentage": 10.0})
    assert response.status_code == 404


async def test_delete_allocation_target_not_found(client: AsyncClient) -> None:
    response = await client.delete("/allocation-targets/999")
    assert response.status_code == 404
