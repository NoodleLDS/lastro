from httpx import AsyncClient


async def _create_card(client: AsyncClient, name: str) -> dict:
    return (await client.post("/cards", json={"name": name})).json()


async def _quick_entry(client: AsyncClient, card_id: int, raw: str, date: str) -> dict:
    return (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card_id, "raw": raw, "date": date},
        )
    ).json()


async def test_lista_apenas_confirmadas_por_padrao(client: AsyncClient) -> None:
    card = await _create_card(client, "Nubank")
    await _quick_entry(client, card["id"], "zebu 22", "2026-06-10")

    response = await client.get("/transactions")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_filtra_por_card_id(client: AsyncClient) -> None:
    nubank = await _create_card(client, "Nubank")
    inter = await _create_card(client, "Inter")
    await _quick_entry(client, nubank["id"], "zebu 22", "2026-06-10")
    await _quick_entry(client, inter["id"], "posto 35", "2026-06-10")

    response = await client.get("/transactions", params={"card_id": nubank["id"]})
    body = response.json()
    assert len(body) == 1
    assert body[0]["card_id"] == nubank["id"]


async def test_filtra_por_ano_e_mes(client: AsyncClient) -> None:
    card = await _create_card(client, "Nubank")
    await _quick_entry(client, card["id"], "zebu 22", "2026-06-10")
    await _quick_entry(client, card["id"], "posto 35", "2026-07-10")

    response = await client.get("/transactions", params={"year": 2026, "month": 6})
    body = response.json()
    assert len(body) == 1
    assert body[0]["description"] == "zebu"


async def test_lista_inclui_parcelas_projetadas(client: AsyncClient) -> None:
    card = await _create_card(client, "Nubank")
    await _quick_entry(client, card["id"], "tablet 335,98 3/9", "2026-06-10")

    response = await client.get("/transactions", params={"card_id": card["id"]})
    body = response.json()
    assert len(body) == 7
    assert sorted(t["installment_current"] for t in body) == [3, 4, 5, 6, 7, 8, 9]
