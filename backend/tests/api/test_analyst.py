from httpx import AsyncClient

from lastro.main import app
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.provider import VisionExtractedItem
from tests.conftest import NullCategorizationProvider


class _StubLLM:
    def __init__(self, answer: str) -> None:
        self._answer = answer
        self.last_system_prompt: str | None = None
        self.last_user_message: str | None = None

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return None

    async def complete(self, system_prompt: str, user_message: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_message = user_message
        return self._answer


async def test_ask_analyst_retorna_resposta_do_llm(client: AsyncClient) -> None:
    stub = _StubLLM("Recomendo manter a posição.")
    app.dependency_overrides[get_ollama_provider] = lambda: stub
    try:
        response = await client.post("/analyst/ask", json={"question": "Devo vender BBAS3?"})
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert response.status_code == 200
    assert response.json()["answer"] == "Recomendo manter a posição."
    assert stub.last_user_message == "Devo vender BBAS3?"
    assert "ANALISTA FINANCEIRO" in stub.last_system_prompt
    assert "Carteira atual" in stub.last_system_prompt


async def test_ask_analyst_rejeita_pergunta_vazia(client: AsyncClient) -> None:
    response = await client.post("/analyst/ask", json={"question": "   "})

    assert response.status_code == 422
