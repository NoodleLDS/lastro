from datetime import datetime

from pydantic import BaseModel

from lastro.models.conversation import MessageRole


class ConversationRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationUpdate(BaseModel):
    title: str


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    model: str | None
    tokens_per_second: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
