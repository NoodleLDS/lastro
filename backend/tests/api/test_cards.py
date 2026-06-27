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


async def test_create_card_com_nome_duplicado_retorna_409_json(client: AsyncClient) -> None:
    await client.post("/cards", json={"name": "Nubank"})

    response = await client.post("/cards", json={"name": "Nubank"})

    assert response.status_code == 409
    body = response.json()
    assert "detail" in body


async def test_create_card_rejeita_closing_day_fora_do_range(client: AsyncClient) -> None:
    for closing_day in (0, 35, -5):
        response = await client.post(
            "/cards", json={"name": f"Card{closing_day}", "closing_day": closing_day}
        )
        assert response.status_code == 422


async def test_create_card_aceita_closing_day_nos_limites(client: AsyncClient) -> None:
    response = await client.post("/cards", json={"name": "Nubank", "closing_day": 1})
    assert response.status_code == 201

    response = await client.post("/cards", json={"name": "Inter", "closing_day": 31})
    assert response.status_code == 201


async def test_update_card_rejeita_closing_day_fora_do_range(client: AsyncClient) -> None:
    created = (await client.post("/cards", json={"name": "Inter"})).json()

    response = await client.put(f"/cards/{created['id']}", json={"closing_day": 35})
    assert response.status_code == 422


async def test_billing_cycle_com_closing_day_calcula_janela_da_fatura(
    client: AsyncClient,
) -> None:
    created = (
        await client.post("/cards", json={"name": "PicPay", "closing_day": 7, "due_day": 15})
    ).json()

    response = await client.get(
        f"/cards/{created['id']}/billing-cycle", params={"year": 2026, "month": 6}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["date_from"] == "2026-05-08"
    assert body["date_to"] == "2026-06-07"
    assert body["is_calendar_month"] is False


async def test_billing_cycle_sem_closing_day_cai_no_mes_calendario(
    client: AsyncClient,
) -> None:
    created = (await client.post("/cards", json={"name": "Nubank"})).json()

    response = await client.get(
        f"/cards/{created['id']}/billing-cycle", params={"year": 2026, "month": 6}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["date_from"] == "2026-06-01"
    assert body["date_to"] == "2026-06-30"
    assert body["is_calendar_month"] is True


async def test_billing_cycle_card_not_found(client: AsyncClient) -> None:
    response = await client.get("/cards/999/billing-cycle", params={"year": 2026, "month": 6})
    assert response.status_code == 404
