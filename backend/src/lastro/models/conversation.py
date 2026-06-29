from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default="Nova conversa")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: MessageRole
    content: str
    model: str | None = Field(default=None)
    tokens_per_second: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
