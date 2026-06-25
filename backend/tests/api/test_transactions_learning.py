from httpx import AsyncClient


async def test_patch_categoria_em_transacao_sem_categoria_cria_regra(
    client: AsyncClient,
) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    created = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "uber viagem 22", "date": "2026-06-10"},
        )
    ).json()
    transaction_id = created["transaction"]["id"]
    assert created["transaction"]["category_id"] is None

    response = await client.patch(
        f"/transactions/{transaction_id}", json={"category_id": category["id"]}
    )
    assert response.status_code == 200
    assert response.json()["category_id"] == category["id"]

    rules = (await client.get("/merchant-rules")).json()
    assert any(r["pattern"] == "uber viagem" for r in rules)


async def test_proxima_entrada_parecida_e_categorizada_automaticamente(
    client: AsyncClient,
) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    category = (await client.post("/categories", json={"name": "transporte"})).json()

    first = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "uber viagem 22", "date": "2026-06-10"},
        )
    ).json()
    await client.patch(
        f"/transactions/{first['transaction']['id']}", json={"category_id": category["id"]}
    )

    second = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "uber viagem 18", "date": "2026-06-15"},
        )
    ).json()

    assert second["transaction"]["category_id"] == category["id"]


async def test_patch_nao_cria_regra_quando_ja_tinha_categoria(client: AsyncClient) -> None:
    card = (await client.post("/cards", json={"name": "Nubank"})).json()
    category_a = (await client.post("/categories", json={"name": "transporte"})).json()
    category_b = (await client.post("/categories", json={"name": "lazer"})).json()

    created = (
        await client.post(
            "/transactions/quick-entry",
            json={
                "card_id": card["id"],
                "raw": f"zebu 22 #{category_a['name']}",
                "date": "2026-06-10",
            },
        )
    ).json()

    await client.patch(
        f"/transactions/{created['transaction']['id']}",
        json={"category_id": category_b["id"]},
    )

    rules = (await client.get("/merchant-rules")).json()
    assert rules == []
