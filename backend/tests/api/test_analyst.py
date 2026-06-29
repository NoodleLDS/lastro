from fastapi import HTTPException
from httpx import AsyncClient

from lastro.main import app
from lastro.services.llm.dependency import get_ollama_provider
from lastro.services.llm.provider import ChatMessage, VisionExtractedItem
from tests.conftest import NullCategorizationProvider


class _StubLLM:
    def __init__(self, answer: str) -> None:
        self._answer = answer
        self.last_system_prompt: str | None = None
        self.last_user_message: str | None = None
        self.last_history: list[ChatMessage] | None = None

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return None

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        history: list[ChatMessage] | None = None,
        session=None,
    ) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_message = user_message
        self.last_history = history
        return self._answer


async def test_ask_analyst_retorna_resposta_do_llm(client: AsyncClient) -> None:
    stub = _StubLLM("Recomendo manter a posição.")
    app.dependency_overrides[get_ollama_provider] = lambda: stub
    try:
        response = await client.post("/analyst/ask", json={"question": "Devo vender BBAS3?"})
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Recomendo manter a posição."
    assert isinstance(body["conversation_id"], int)
    assert stub.last_user_message == "Devo vender BBAS3?"
    assert "ANALISTA FINANCEIRO" in stub.last_system_prompt
    assert "get_portfolio" in stub.last_system_prompt


async def test_ask_analyst_rejeita_pergunta_vazia(client: AsyncClient) -> None:
    response = await client.post("/analyst/ask", json={"question": "   "})

    assert response.status_code == 422


async def test_ask_analyst_mantem_historico_na_mesma_conversa(client: AsyncClient) -> None:
    stub = _StubLLM("ok")
    app.dependency_overrides[get_ollama_provider] = lambda: stub
    try:
        first = await client.post("/analyst/ask", json={"question": "Quanto tenho investido?"})
        conversation_id = first.json()["conversation_id"]

        second = await client.post(
            "/analyst/ask",
            json={"question": "E em ações?", "conversation_id": conversation_id},
        )
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert second.json()["conversation_id"] == conversation_id
    assert stub.last_history == [
        {"role": "user", "content": "Quanto tenho investido?"},
        {"role": "assistant", "content": "ok"},
    ]


async def test_listar_e_excluir_conversas(client: AsyncClient) -> None:
    stub = _StubLLM("ok")
    app.dependency_overrides[get_ollama_provider] = lambda: stub
    try:
        created = await client.post("/analyst/ask", json={"question": "Pergunta de teste"})
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()
    conversation_id = created.json()["conversation_id"]

    listed = await client.get("/analyst/conversations")
    assert any(c["id"] == conversation_id for c in listed.json())

    messages = await client.get(f"/analyst/conversations/{conversation_id}/messages")
    assert len(messages.json()) == 2

    renamed = await client.patch(
        f"/analyst/conversations/{conversation_id}", json={"title": "Carteira"}
    )
    assert renamed.json()["title"] == "Carteira"

    deleted = await client.delete(f"/analyst/conversations/{conversation_id}")
    assert deleted.status_code == 204

    listed_after = await client.get("/analyst/conversations")
    assert all(c["id"] != conversation_id for c in listed_after.json())


async def test_memory_retorna_master_prompt_e_contexto_da_carteira(client: AsyncClient) -> None:
    response = await client.get("/analyst/memory")
    assert response.status_code == 200
    body = response.json()
    assert len(body["master_prompt"]) > 0
    assert "portfolio_context" in body


async def test_instructions_get_e_update(client: AsyncClient) -> None:
    empty = await client.get("/analyst/instructions")
    assert empty.json()["content"] == ""

    updated = await client.put("/analyst/instructions", json={"content": "Seja direto."})
    assert updated.json()["content"] == "Seja direto."

    fetched_again = await client.get("/analyst/instructions")
    assert fetched_again.json()["content"] == "Seja direto."


async def test_instructions_aparecem_no_system_prompt(client: AsyncClient) -> None:
    await client.put("/analyst/instructions", json={"content": "Responda em até 3 frases."})

    stub = _StubLLM("ok")
    app.dependency_overrides[get_ollama_provider] = lambda: stub
    try:
        await client.post("/analyst/ask", json={"question": "Devo vender BBAS3?"})
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert "Responda em até 3 frases." in stub.last_system_prompt


class _OfflineLLM:
    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        return None

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        history: list[ChatMessage] | None = None,
        session=None,
    ) -> str:
        raise HTTPException(status_code=503, detail="Serviço de IA (Ollama) indisponível.")


async def test_ask_analyst_retorna_503_quando_ollama_indisponivel(client: AsyncClient) -> None:
    app.dependency_overrides[get_ollama_provider] = lambda: _OfflineLLM()
    try:
        response = await client.post("/analyst/ask", json={"question": "Devo vender BBAS3?"})
    finally:
        app.dependency_overrides[get_ollama_provider] = lambda: NullCategorizationProvider()

    assert response.status_code == 503
    assert "detail" in response.json()
