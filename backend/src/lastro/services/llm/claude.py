import base64

import httpx

from lastro.services.llm.provider import VisionExtractedItem

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_MODEL = "claude-sonnet-4-6"

_EXTRACT_TOOL = {
    "name": "extract_transactions",
    "description": "Extrai a lista de transações visíveis numa fatura de cartão de crédito.",
    "input_schema": {
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount_cents": {
                            "type": "integer",
                            "description": "valor em centavos, sempre positivo",
                        },
                        "date": {
                            "type": "string",
                            "description": "data no formato YYYY-MM-DD, se visível",
                        },
                        "suggested_category": {"type": "string"},
                    },
                    "required": ["description", "amount_cents"],
                },
            }
        },
        "required": ["transactions"],
    },
}


class ClaudeVisionProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]:
        image_b64 = base64.b64encode(image_bytes).decode("ascii")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                _ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": _MODEL,
                    "max_tokens": 4096,
                    "tools": [_EXTRACT_TOOL],
                    "tool_choice": {"type": "tool", "name": "extract_transactions"},
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": image_b64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Extraia todas as transações desta fatura de cartão "
                                        "de crédito."
                                    ),
                                },
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            body = response.json()

        tool_use = next(block for block in body["content"] if block["type"] == "tool_use")
        raw_transactions = tool_use["input"]["transactions"]

        return [VisionExtractedItem(**item) for item in raw_transactions]

    async def categorize(self, description: str, category_names: list[str]) -> str | None:
        raise NotImplementedError("categorização de texto usa o provider Ollama, não Claude")

    async def complete(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError("chat do analista usa o provider Ollama, não Claude")
