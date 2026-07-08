from httpx import AsyncClient


async def test_create_and_list_income(client: AsyncClient) -> None:
    response = await client.post(
        "/incomes",
        json={"description": "Salário", "amount_cents": 654_071, "year": 2026, "month": 6},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["description"] == "Salário"

    response = await client.get("/incomes", params={"year": 2026, "month": 6})
    assert response.status_code == 200
    assert [i["id"] for i in response.json()] == [created["id"]]


async def test_update_and_delete_income(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/incomes",
            json={"description": "Salário", "amount_cents": 100_000, "year": 2026, "month": 6},
        )
    ).json()

    response = await client.patch(f"/incomes/{created['id']}", json={"amount_cents": 120_000})
    assert response.status_code == 200
    assert response.json()["amount_cents"] == 120_000

    response = await client.delete(f"/incomes/{created['id']}")
    assert response.status_code == 204

    response = await client.get("/incomes", params={"year": 2026, "month": 6})
    assert response.json() == []


async def test_update_income_not_found(client: AsyncClient) -> None:
    response = await client.patch("/incomes/999", json={"amount_cents": 1})
    assert response.status_code == 404


async def test_delete_income_not_found(client: AsyncClient) -> None:
    response = await client.delete("/incomes/999")
    assert response.status_code == 404


async def test_create_fixed_expense_com_categoria_inexistente_retorna_422(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/fixed-expenses",
        json={
            "description": "Plano de saúde",
            "amount_cents": 12_300,
            "year": 2026,
            "month": 6,
            "category_id": 999,
        },
    )
    assert response.status_code == 422


async def test_create_and_list_fixed_expense(client: AsyncClient) -> None:
    response = await client.post(
        "/fixed-expenses",
        json={"description": "Colégio", "amount_cents": 12_900, "year": 2026, "month": 6},
    )
    assert response.status_code == 201
    assert response.json()["is_paid"] is False

    response = await client.get("/fixed-expenses", params={"year": 2026, "month": 6})
    assert len(response.json()) == 1


async def test_create_and_list_variable_expense(client: AsyncClient) -> None:
    response = await client.post(
        "/variable-expenses",
        json={"description": "Luz", "amount_cents": 20_000, "year": 2026, "month": 6},
    )
    assert response.status_code == 201
    assert response.json()["is_paid"] is False

    response = await client.get("/variable-expenses", params={"year": 2026, "month": 6})
    assert len(response.json()) == 1


async def test_mark_fixed_expense_as_paid(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/fixed-expenses",
            json={"description": "Colégio", "amount_cents": 12_900, "year": 2026, "month": 6},
        )
    ).json()

    response = await client.patch(f"/fixed-expenses/{created['id']}", json={"is_paid": True})
    assert response.status_code == 200
    assert response.json()["is_paid"] is True

    response = await client.patch(f"/fixed-expenses/{created['id']}", json={"is_paid": False})
    assert response.status_code == 200
    assert response.json()["is_paid"] is False


async def test_mark_variable_expense_as_paid(client: AsyncClient) -> None:
    created = (
        await client.post(
            "/variable-expenses",
            json={"description": "Luz", "amount_cents": 20_000, "year": 2026, "month": 6},
        )
    ).json()

    response = await client.patch(f"/variable-expenses/{created['id']}", json={"is_paid": True})
    assert response.status_code == 200
    assert response.json()["is_paid"] is True


async def test_monthly_summary_end_to_end(client: AsyncClient) -> None:
    await client.post(
        "/incomes",
        json={"description": "Salário", "amount_cents": 654_071, "year": 2026, "month": 6},
    )
    await client.post(
        "/fixed-expenses",
        json={"description": "Plano de saúde", "amount_cents": 12_300, "year": 2026, "month": 6},
    )
    await client.post(
        "/variable-expenses",
        json={"description": "Luz", "amount_cents": 20_000, "year": 2026, "month": 6},
    )
    card = (await client.post("/cards", json={"name": "PicPay"})).json()
    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "mercado 100", "date": "2026-06-10"},
    )

    response = await client.get("/monthly-summary", params={"year": 2026, "month": 6})
    assert response.status_code == 200
    body = response.json()

    assert body["income_total_cents"] == 654_071
    assert body["fixed_expense_total_cents"] == 12_300
    assert body["variable_expense_total_cents"] == 20_000
    assert body["card_spending"] == [
        {"card_id": card["id"], "card_name": "PicPay", "total_cents": 10_000, "is_paid": False}
    ]
    assert body["card_spending_total_cents"] == 10_000
    assert body["balance_cents"] == 654_071 - 12_300 - 20_000 - 10_000


async def test_monthly_summary_reflete_fatura_marcada_como_paga(client: AsyncClient) -> None:
    card = (await client.post("/cards", json={"name": "PicPay"})).json()
    await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "mercado 100", "date": "2026-06-10"},
    )
    await client.put(
        f"/cards/{card['id']}/invoice-payment", params={"year": 2026, "month": 6}
    )

    response = await client.get("/monthly-summary", params={"year": 2026, "month": 6})
    assert response.status_code == 200
    assert response.json()["card_spending"][0]["is_paid"] is True

    response = await client.get("/monthly-summary", params={"year": 2026, "month": 7})
    assert response.json()["card_spending"][0]["is_paid"] is False


async def test_monthly_summary_sem_lancamentos_retorna_zeros(client: AsyncClient) -> None:
    response = await client.get("/monthly-summary", params={"year": 2030, "month": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["income_total_cents"] == 0
    assert body["balance_cents"] == 0
    assert body["card_spending"] == []
