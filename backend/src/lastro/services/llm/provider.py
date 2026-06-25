from datetime import date as date_
from typing import Protocol

from pydantic import BaseModel


class VisionExtractedItem(BaseModel):
    description: str
    amount_cents: int
    date: date_ | None = None
    suggested_category: str | None = None


class LLMProvider(Protocol):
    async def vision(self, image_bytes: bytes, mime_type: str) -> list[VisionExtractedItem]: ...

    async def categorize(self, description: str, category_names: list[str]) -> str | None: ...

    async def complete(self, system_prompt: str, user_message: str) -> str: ...
