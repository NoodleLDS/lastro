from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from lastro.services.auth.bootstrap import ensure_admin_user
from lastro.services.auth.security import decode_access_token


async def test_login_com_credenciais_corretas_retorna_token(
    client: AsyncClient, session: AsyncSession
) -> None:
    await ensure_admin_user(session)

    response = await client.post("/auth/login", json={"username": "admin", "password": "admin"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert decode_access_token(body["access_token"]) == "admin"


async def test_login_com_senha_errada_retorna_401(
    client: AsyncClient, session: AsyncSession
) -> None:
    await ensure_admin_user(session)

    response = await client.post("/auth/login", json={"username": "admin", "password": "errada"})

    assert response.status_code == 401


async def test_login_com_usuario_inexistente_retorna_401(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={"username": "ninguem", "password": "x"})

    assert response.status_code == 401


async def test_rota_protegida_sem_token_retorna_401(client: AsyncClient) -> None:
    response = await client.get("/cards", headers={"Authorization": ""})

    assert response.status_code == 401


async def test_health_nao_exige_autenticacao(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"Authorization": ""})

    assert response.status_code == 200
