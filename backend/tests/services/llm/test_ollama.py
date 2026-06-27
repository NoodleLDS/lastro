import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from lastro.services.llm.ollama import OllamaProvider


def _chat_response(content: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={"message": {"content": json.dumps(content)}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )


async def test_categorize_retorna_categoria_escolhida_pelo_modelo() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = _chat_response({"category": "Alimentação"})

        result = await provider.categorize("zebu 22", ["Alimentação", "Transporte"])

    assert result == "Alimentação"


async def test_categorize_retorna_none_quando_modelo_escolhe_categoria_inexistente() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = _chat_response({"category": "Categoria Inventada"})

        result = await provider.categorize("zebu 22", ["Alimentação", "Transporte"])

    assert result is None


async def test_categorize_sem_categorias_disponiveis_nao_chama_o_modelo() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        result = await provider.categorize("zebu 22", [])

    mock_post.assert_not_called()
    assert result is None


async def test_vision_nao_e_suportado_no_ollama() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with pytest.raises(NotImplementedError):
        await provider.vision(b"", "image/png")


async def test_categorize_retorna_none_quando_ollama_esta_fora_do_ar() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")

        result = await provider.categorize("zebu 22", ["Alimentação", "Transporte"])

    assert result is None


async def test_categorize_retorna_none_quando_ollama_demora_demais() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.side_effect = httpx.ReadTimeout("timed out")

        result = await provider.categorize("zebu 22", ["Alimentação", "Transporte"])

    assert result is None


async def test_categorize_retorna_none_quando_modelo_nao_esta_pulled() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")
    request = httpx.Request("POST", "http://ollama.local/api/chat")
    not_found = httpx.Response(404, request=request)

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = not_found

        result = await provider.categorize("zebu 22", ["Alimentação", "Transporte"])

    assert result is None


async def test_complete_levanta_503_quando_ollama_esta_fora_do_ar() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", "pergunta do usuário")

    assert exc_info.value.status_code == 503


async def test_complete_levanta_503_quando_modelo_nao_esta_pulled() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")
    request = httpx.Request("POST", "http://ollama.local/api/chat")
    not_found = httpx.Response(404, request=request)

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = not_found

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", "pergunta do usuário")

    assert exc_info.value.status_code == 503


async def test_complete_levanta_503_quando_timeout() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.side_effect = httpx.ReadTimeout("timed out")

        with pytest.raises(HTTPException) as exc_info:
            await provider.complete("system prompt", "pergunta do usuário")

    assert exc_info.value.status_code == 503


async def test_complete_usa_timeout_estendido_para_master_prompt() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")
    captured_timeouts: list[object] = []
    original_init = httpx.AsyncClient.__init__

    def capturing_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        captured_timeouts.append(kwargs.get("timeout"))
        original_init(self, *args, **kwargs)

    response = httpx.Response(
        200,
        json={"message": {"content": "ok"}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )

    with (
        patch.object(httpx.AsyncClient, "__init__", new=capturing_init),
        patch.object(httpx.AsyncClient, "post", new=AsyncMock(return_value=response)),
    ):
        await provider.complete("system prompt", "pergunta do usuário")

    assert captured_timeouts and captured_timeouts[0] >= 120


async def test_complete_retorna_texto_livre_da_resposta() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    response = httpx.Response(
        200,
        json={"message": {"content": "Resposta do analista em texto livre."}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = response

        result = await provider.complete("system prompt", "pergunta do usuário")

    assert result == "Resposta do analista em texto livre."
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "pergunta do usuário"},
    ]
    assert "format" not in call_kwargs["json"]
