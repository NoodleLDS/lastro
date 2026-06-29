import base64
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
import structlog
from fastapi import HTTPException

from lastro.services.llm.provider import ChatMessage, VisionExtractedItem
from lastro.services.llm.tools import TOOL_DEFINITIONS, execute_tool

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

logger = structlog.get_logger()

_MAX_TOOL_CALL_ROUNDS = 5


@dataclass
class StreamChunk:
    content: str
    done: bool
    model: str | None = None
    tokens_per_second: float | None = None


_CATEGORIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
    },
    "required": ["category"],
}

_OLLAMA_UNAVAILABLE_DETAIL = (
    "Serviço de IA (Ollama) indisponível. Verifique se está rodando e com o "
    "modelo configurado disponível (`ollama pull <modelo>`)."
)

_VISION_SCHEMA = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount_cents": {"type": "integer"},
                    "date": {"type": "string"},
                    "suggested_category": {"type": "string"},
                },
                "required": ["description", "amount_cents"],
            },
        }
    },
    "required": ["transactions"],
}

_VISION_PROMPT = (
    "Extraia todas as transações desta fatura de cartão de crédito. "
    "Para cada transação, identifique descrição, valor em centavos (sempre "
    "positivo, ex.: R$ 35,90 vira 3590), e a data se estiver visível no "
    "formato YYYY-MM-DD. Responda apenas com o JSON pedido."
)


class OllamaProvider:
    def __init__(self, base_url: str, model: str, vision_model: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._vision_model = vision_model

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        if not self._vision_model:
            raise HTTPException(
                status_code=400,
                detail="modelo de visão do Ollama não configurado (LASTRO_OLLAMA_VISION_MODEL)",
            )

        image_b64 = base64.b64encode(image_bytes).decode("ascii")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._vision_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": _VISION_PROMPT,
                                "images": [image_b64],
                            }
                        ],
                        "format": _VISION_SCHEMA,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("ollama_vision_indisponivel", error=str(exc))
            raise HTTPException(status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL) from exc

        content = body["message"]["content"]
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("ollama_vision_resposta_invalida", content=content)
            raise HTTPException(
                status_code=502, detail="modelo de visão retornou resposta inválida"
            ) from exc

        items = []
        for item in parsed.get("transactions", []):
            if not item.get("date"):
                item.pop("date", None)
            if not item.get("suggested_category"):
                item.pop("suggested_category", None)
            items.append(VisionExtractedItem(**item))
        return items

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        if not category_names:
            return None

        prompt = (
            "Escolha a categoria mais adequada para esta transação financeira.\n"
            f"Descrição: {description!r}\n"
            f"Categorias disponíveis: {', '.join(category_names)}\n"
            "Responda apenas com o nome exato de uma das categorias acima."
        )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [{"role": "user", "content": prompt}],
                        "format": _CATEGORIZE_SCHEMA,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("ollama_categorize_indisponivel", error=str(exc))
            return None

        content = body["message"]["content"]
        category = _parse_category(content)
        if category not in category_names:
            return None
        return category

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        history: list[ChatMessage] | None = None,
        session: "AsyncSession | None" = None,
    ) -> str:
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            *(history or []),
            {"role": "user", "content": user_message},
        ]
        tools = TOOL_DEFINITIONS if session is not None else None

        for _ in range(_MAX_TOOL_CALL_ROUNDS):
            try:
                async with httpx.AsyncClient(timeout=150) as client:
                    payload = {"model": self._model, "messages": messages, "stream": False}
                    if tools:
                        payload["tools"] = tools
                    response = await client.post(f"{self._base_url}/api/chat", json=payload)
                    response.raise_for_status()
                    body = response.json()
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
                logger.warning("ollama_complete_indisponivel", error=str(exc))
                raise HTTPException(status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL) from exc

            message = body["message"]
            tool_calls = message.get("tool_calls")
            if not tool_calls or session is None:
                return message["content"]

            messages.append(message)
            for call in tool_calls:
                function = call["function"]
                arguments = function.get("arguments") or {}
                result = await execute_tool(session, function["name"], arguments)
                messages.append({"role": "tool", "content": result})

        return (
            "Não consegui concluir a consulta às ferramentas a tempo. Tente reformular a pergunta."
        )

    async def complete_stream(
        self,
        system_prompt: str,
        user_message: str,
        history: list[ChatMessage] | None = None,
        session: "AsyncSession | None" = None,
    ) -> AsyncIterator[StreamChunk]:
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            *(history or []),
            {"role": "user", "content": user_message},
        ]
        tools = TOOL_DEFINITIONS if session is not None else None

        for _ in range(_MAX_TOOL_CALL_ROUNDS):
            tool_calls = await self._resolve_tool_calls(messages, tools, session)
            if not tool_calls:
                break
            for call in tool_calls:
                function = call["function"]
                arguments = function.get("arguments") or {}
                result = await execute_tool(session, function["name"], arguments)
                messages.append({"role": "tool", "content": result})

        async for chunk in self._stream_final_answer(messages):
            yield chunk

    async def _resolve_tool_calls(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        session: "AsyncSession | None",
    ) -> list[dict]:
        """Chamada não-streaming só para checar se a LLM quer usar uma tool.
        Se não quiser, não modifica `messages` (a resposta final é streamada
        de fato em `_stream_final_answer`); se quiser, anexa a mensagem do
        assistant com `tool_calls` e devolve a lista para execução."""
        if not tools or session is None:
            return []
        try:
            async with httpx.AsyncClient(timeout=150) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": messages,
                        "tools": tools,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("ollama_complete_stream_indisponivel", error=str(exc))
            raise HTTPException(status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL) from exc

        message = body["message"]
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return []
        messages.append(message)
        return tool_calls

    async def _stream_final_answer(self, messages: list[dict]) -> AsyncIterator[StreamChunk]:
        try:
            async with httpx.AsyncClient(timeout=150) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json={"model": self._model, "messages": messages, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        done = chunk.get("done", False)
                        tokens_per_second = None
                        if done:
                            eval_count = chunk.get("eval_count")
                            eval_duration = chunk.get("eval_duration")
                            if eval_count and eval_duration:
                                tokens_per_second = eval_count / (eval_duration / 1e9)
                        yield StreamChunk(
                            content=chunk.get("message", {}).get("content", ""),
                            done=done,
                            model=chunk.get("model"),
                            tokens_per_second=tokens_per_second,
                        )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("ollama_complete_stream_indisponivel", error=str(exc))
            raise HTTPException(status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL) from exc


def _parse_category(raw_content: str) -> str | None:
    try:
        parsed = json.loads(raw_content)
    except (json.JSONDecodeError, TypeError):
        return None
    category = parsed.get("category")
    return category if isinstance(category, str) else None
