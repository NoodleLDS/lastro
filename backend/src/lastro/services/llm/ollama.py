import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
import structlog
from fastapi import HTTPException

from lastro.services.llm.provider import VisionExtractedItem

logger = structlog.get_logger()


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


class OllamaProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        raise NotImplementedError(
            "vision de fatura é opt-in via Claude API, não suportado no Ollama"
        )

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

    async def complete(self, system_prompt: str, user_message: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=150) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                body = response.json()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
            logger.warning("ollama_complete_indisponivel", error=str(exc))
            raise HTTPException(
                status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL
            ) from exc

        return body["message"]["content"]

    async def complete_stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[StreamChunk]:
        try:
            async with httpx.AsyncClient(timeout=150) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "stream": True,
                    },
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
            raise HTTPException(
                status_code=503, detail=_OLLAMA_UNAVAILABLE_DETAIL
            ) from exc


def _parse_category(raw_content: str) -> str | None:
    try:
        parsed = json.loads(raw_content)
    except (json.JSONDecodeError, TypeError):
        return None
    category = parsed.get("category")
    return category if isinstance(category, str) else None
