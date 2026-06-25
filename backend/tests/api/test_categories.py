from httpx import AsyncClient


async def test_create_and_list_category(client: AsyncClient) -> None:
    response = await client.post("/categories", json={"name": "transporte"})
    assert response.status_code == 201
    assert response.json()["name"] == "transporte"

    response = await client.get("/categories")
    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["transporte"]
