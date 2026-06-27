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


async def test_create_merchant_rule_rejeita_pattern_duplicado_ativo(
    client: AsyncClient,
) -> None:
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    first = await client.post(
        "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
    )
    assert first.status_code == 201

    second = await client.post(
        "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
    )
    assert second.status_code == 422

    response = await client.get("/merchant-rules")
    assert len(response.json()) == 1


async def test_create_merchant_rule_permite_pattern_repetido_se_anterior_inativo(
    client: AsyncClient,
) -> None:
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    first = (
        await client.post(
            "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
        )
    ).json()
    await client.put(f"/merchant-rules/{first['id']}", json={"is_active": False})

    second = await client.post(
        "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
    )
    assert second.status_code == 201


async def test_create_merchant_rule_rejeita_category_id_inexistente(client: AsyncClient) -> None:
    response = await client.post("/merchant-rules", json={"pattern": "uber", "category_id": 9999})
    assert response.status_code == 422

    response = await client.get("/merchant-rules")
    assert response.json() == []


async def test_update_merchant_rule_rejeita_category_id_inexistente(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "transporte"})).json()
    rule = (
        await client.post(
            "/merchant-rules", json={"pattern": "uber", "category_id": category["id"]}
        )
    ).json()

    response = await client.put(f"/merchant-rules/{rule['id']}", json={"category_id": 9999})
    assert response.status_code == 422


async def test_update_merchant_rule_rejeita_pattern_duplicado_ativo(
    client: AsyncClient,
) -> None:
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    await client.post("/merchant-rules", json={"pattern": "uber", "category_id": category["id"]})
    rule_99 = (
        await client.post(
            "/merchant-rules", json={"pattern": "99pop", "category_id": category["id"]}
        )
    ).json()

    response = await client.put(f"/merchant-rules/{rule_99['id']}", json={"pattern": "uber"})
    assert response.status_code == 422
