from httpx import AsyncClient


async def _create_card(client: AsyncClient, name: str = "Nubank") -> dict:
    response = await client.post("/cards", json={"name": name})
    return response.json()


async def test_quick_entry_sem_categoria_sem_parcela(client: AsyncClient) -> None:
    card = await _create_card(client)

    response = await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "zebu 22", "date": "2026-06-10"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["transaction"]["description"] == "zebu"
    assert body["transaction"]["amount_cents"] == 2200
    assert body["transaction"]["category_id"] is None
    assert body["installments"] == []


async def test_quick_entry_com_categoria_explicita_cria_categoria(client: AsyncClient) -> None:
    card = await _create_card(client)

    response = await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "posto 35 #transporte", "date": "2026-06-10"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["transaction"]["category_id"] is not None

    categories = (await client.get("/categories")).json()
    assert any(c["name"] == "transporte" for c in categories)


async def test_quick_entry_com_parcela_projeta_transacoes_futuras(client: AsyncClient) -> None:
    card = await _create_card(client)

    response = await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "tablet 335,98 3/9", "date": "2026-06-10"},
    )
    assert response.status_code == 201
    body = response.json()

    assert body["transaction"]["installment_current"] == 3
    assert len(body["installments"]) == 6
    assert [i["installment_current"] for i in body["installments"]] == [4, 5, 6, 7, 8, 9]
    assert all(i["parent_id"] == body["transaction"]["id"] for i in body["installments"])


async def test_quick_entry_raw_invalido_retorna_422(client: AsyncClient) -> None:
    card = await _create_card(client)

    response = await client.post(
        "/transactions/quick-entry",
        json={"card_id": card["id"], "raw": "zebu", "date": "2026-06-10"},
    )
    assert response.status_code == 422


async def test_delete_transaction(client: AsyncClient) -> None:
    card = await _create_card(client)
    created = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "zebu 22", "date": "2026-06-10"},
        )
    ).json()

    response = await client.delete(f"/transactions/{created['transaction']['id']}")
    assert response.status_code == 204


async def test_delete_transaction_not_found(client: AsyncClient) -> None:
    response = await client.delete("/transactions/999")
    assert response.status_code == 404


async def test_quick_entry_rejeita_card_id_inexistente(client: AsyncClient) -> None:
    response = await client.post(
        "/transactions/quick-entry",
        json={"card_id": 9999, "raw": "zebu 22", "date": "2026-06-10"},
    )
    assert response.status_code == 422


async def test_delete_transacao_raiz_parcelada_remove_parcelas_filhas_em_cascata(
    client: AsyncClient,
) -> None:
    card = await _create_card(client)
    created = (
        await client.post(
            "/transactions/quick-entry",
            json={"card_id": card["id"], "raw": "tablet 335,98 3/9", "date": "2026-06-10"},
        )
    ).json()

    root_id = created["transaction"]["id"]
    installment_ids = [i["id"] for i in created["installments"]]
    assert installment_ids

    response = await client.delete(f"/transactions/{root_id}")
    assert response.status_code == 204

    remaining = (await client.get("/transactions")).json()
    remaining_ids = {t["id"] for t in remaining}
    assert root_id not in remaining_ids
    for installment_id in installment_ids:
        assert installment_id not in remaining_ids
