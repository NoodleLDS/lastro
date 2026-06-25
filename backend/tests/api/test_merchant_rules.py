from httpx import AsyncClient


async def test_create_update_delete_merchant_rule(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    created = await client.post(
        "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
    )
    assert created.status_code == 201
    rule = created.json()
    assert rule["pattern"] == "uber"
    assert rule["is_active"] is True

    response = await client.get("/merchant-rules")
    assert [r["pattern"] for r in response.json()] == ["uber"]

    response = await client.put(f"/merchant-rules/{rule['id']}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    response = await client.delete(f"/merchant-rules/{rule['id']}")
    assert response.status_code == 204

    response = await client.get("/merchant-rules")
    assert response.json() == []


async def test_update_merchant_rule_not_found(client: AsyncClient) -> None:
    response = await client.put("/merchant-rules/999", json={"pattern": "x"})
    assert response.status_code == 404


async def test_delete_merchant_rule_not_found(client: AsyncClient) -> None:
    response = await client.delete("/merchant-rules/999")
    assert response.status_code == 404
