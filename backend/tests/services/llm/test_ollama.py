import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

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
