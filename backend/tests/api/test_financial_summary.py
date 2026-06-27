from httpx import AsyncClient


async def _create_position(client: AsyncClient, ticker: str, quantity: float, date: str) -> dict:
    position = (
        await client.post(
            "/positions", json={"ticker": ticker, "name": ticker, "asset_type": "stock"}
        )
    ).json()
    await client.post(
        "/contributions",
        json={
            "position_id": position["id"],
            "date": date,
            "quantity": quantity,
            "unit_price_cents": 1000,
        },
    )
    return position


async def test_financial_summary_end_to_end(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "Alimentação"})).json()
    card = (await client.post("/cards", json={"name": "PicPay"})).json()

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
    quick_entry = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "mercado 100", "date": "2026-06-10"},
        )
    ).json()
    await client.patch(
        f"/transactions/{quick_entry['transaction']['id']}",
        json={"category_id": category["id"]},
    )
    await _create_position(client, "BBAS3", 10, "2026-06-05")

    await client.post(
        "/emergency-reserve",
        json={"institution": "Inter", "balance_cents": 1_200_000, "cdi_percentage": 100.0},
    )

    response = await client.get("/dashboard/financial-summary", params={"year": 2026, "month": 6})
    assert response.status_code == 200
    body = response.json()

    assert body["monthly"]["income_total_cents"] == 654_071
    assert body["monthly"]["expense_total_cents"] == 12_300 + 20_000 + 10_000
    assert body["monthly"]["contribution_total_cents"] == 10 * 1000
    assert body["monthly"]["balance_cents"] == 654_071 - (12_300 + 20_000 + 10_000) - 10 * 1000

    assert body["yearly"]["income_total_cents"] == 654_071
    assert body["yearly"]["expense_total_cents"] == 12_300 + 20_000 + 10_000

    assert body["emergency_reserve"]["balance_cents"] == 1_200_000
    assert body["emergency_reserve"]["average_monthly_expense_cents"] > 0
    assert body["emergency_reserve"]["months_covered"] is not None

    assert body["category_card_breakdown"] == [
        {
            "category_id": category["id"],
            "category_name": "Alimentação",
            "card_id": card["id"],
            "card_name": "PicPay",
            "total_cents": 10_000,
        }
    ]


async def test_financial_summary_sem_lancamentos_retorna_zeros(client: AsyncClient) -> None:
    response = await client.get("/dashboard/financial-summary", params={"year": 2030, "month": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["monthly"]["income_total_cents"] == 0
    assert body["monthly"]["balance_cents"] == 0
    assert body["emergency_reserve"]["balance_cents"] == 0
    assert body["emergency_reserve"]["months_covered"] is None
    assert body["category_card_breakdown"] == []
