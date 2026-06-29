from datetime import date as date_
from typing import Protocol, TypedDict

from pydantic import BaseModel


class ChatMessage(TypedDict):
    role: str
    content: str


class VisionExtractedItem(BaseModel):
    description: str
    amount_cents: int
    date: date_ | None = None
    suggested_category: str | None = None


class LLMProvider(Protocol):
    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]: ...

    async def categorize(self, description: str, category_names: list[str]) -> str | None: ...

    async def complete(
        self, system_prompt: str, user_message: str, history: list[ChatMessage] | None = None
    ) -> str: ...
