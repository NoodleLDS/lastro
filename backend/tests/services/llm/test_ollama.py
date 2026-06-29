import base64
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

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


async def test_vision_sem_modelo_configurado_retorna_400() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    with pytest.raises(HTTPException) as exc_info:
        await provider.vision(b"fake-image-bytes", "image/png")

    assert exc_info.value.status_code == 400


async def test_vision_extrai_transacoes_da_resposta_do_modelo() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b", "qwen2.5vl:3b")

    response = _chat_response(
        {
            "transactions": [
                {"description": "Zebu", "amount_cents": 2200, "date": "2026-06-01"},
                {"description": "Posto", "amount_cents": 3500},
            ]
        }
    )

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = response

        result = await provider.vision(b"fake-image-bytes", "image/png")

    assert len(result) == 2
    assert result[0].description == "Zebu"
    assert result[0].amount_cents == 2200
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "qwen2.5vl:3b"
    assert call_kwargs["json"]["messages"][0]["images"] == [
        base64.b64encode(b"fake-image-bytes").decode("ascii")
    ]


async def test_vision_ignora_date_e_categoria_vazias_do_modelo() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b", "qwen2.5vl:3b")

    response = _chat_response(
        {
            "transactions": [
                {
                    "description": "Steamgames.Com",
                    "amount_cents": 3098,
                    "date": "",
                    "suggested_category": "",
                }
            ]
        }
    )

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = response

        result = await provider.vision(b"fake-image-bytes", "image/png")

    assert len(result) == 1
    assert result[0].date is None
    assert result[0].suggested_category is None


async def test_vision_levanta_503_quando_ollama_esta_fora_do_ar() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b", "qwen2.5vl:3b")

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.side_effect = httpx.ConnectError("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await provider.vision(b"fake-image-bytes", "image/png")

    assert exc_info.value.status_code == 503


async def test_vision_resposta_invalida_levanta_502() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b", "qwen2.5vl:3b")

    response = httpx.Response(
        200,
        json={"message": {"content": "isso não é JSON válido"}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock()) as mock_post:
        mock_post.return_value = response

        with pytest.raises(HTTPException) as exc_info:
            await provider.vision(b"fake-image-bytes", "image/png")

    assert exc_info.value.status_code == 502


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


async def test_complete_sem_session_nao_envia_tools() -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    response = httpx.Response(
        200,
        json={"message": {"content": "ok"}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )

    with patch.object(httpx.AsyncClient, "post", new=AsyncMock(return_value=response)) as mock_post:
        await provider.complete("system prompt", "pergunta do usuário")

    assert "tools" not in mock_post.call_args.kwargs["json"]


async def test_complete_executa_tool_call_e_devolve_resultado_ao_modelo(
    session: AsyncSession,
) -> None:
    provider = OllamaProvider("http://ollama.local", "llama3.2:3b")

    tool_call_response = httpx.Response(
        200,
        json={
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_emergency_reserve",
                            "arguments": {},
                        }
                    }
                ],
            }
        },
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )
    final_response = httpx.Response(
        200,
        json={"message": {"role": "assistant", "content": "Sua reserva está saudável."}},
        request=httpx.Request("POST", "http://ollama.local/api/chat"),
    )

    with patch.object(
        httpx.AsyncClient, "post", new=AsyncMock(side_effect=[tool_call_response, final_response])
    ) as mock_post:
        result = await provider.complete(
            "system prompt", "como está minha reserva?", session=session
        )

    assert result == "Sua reserva está saudável."
    assert mock_post.call_count == 2
    first_call_json = mock_post.call_args_list[0].kwargs["json"]
    assert first_call_json["tools"][0]["function"]["name"] == "get_portfolio"
    second_call_messages = mock_post.call_args_list[1].kwargs["json"]["messages"]
    tool_messages = [m for m in second_call_messages if m["role"] == "tool"]
    assert len(tool_messages) == 1
    assert "Nenhuma reserva" in tool_messages[0]["content"]
