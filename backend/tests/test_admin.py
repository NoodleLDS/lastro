from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from lastro.main import app
from lastro.services.auth.security import create_access_token

AUTH_HEADERS = {"Authorization": f"Bearer {create_access_token('admin')}"}


async def test_restart_triggers_launcher_and_returns_immediately() -> None:
    with patch("lastro.api.admin._trigger_launcher", new_callable=AsyncMock) as mock_trigger:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/admin/restart", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {"status": "restarting"}
    mock_trigger.assert_called_once_with("/restart")


async def test_shutdown_triggers_launcher_and_returns_immediately() -> None:
    with patch("lastro.api.admin._trigger_launcher", new_callable=AsyncMock) as mock_trigger:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/admin/shutdown", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json() == {"status": "shutting down"}
    mock_trigger.assert_called_once_with("/shutdown")
