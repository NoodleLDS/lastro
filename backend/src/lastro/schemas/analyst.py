from pydantic import BaseModel


class AskAnalystRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class AskAnalystResponse(BaseModel):
    answer: str
    conversation_id: int


class AnalystInstructionsRead(BaseModel):
    content: str


class AnalystInstructionsUpdate(BaseModel):
    content: str


class AnalystMemoryRead(BaseModel):
    master_prompt: str
    portfolio_context: str
