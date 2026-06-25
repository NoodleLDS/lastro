from pydantic import BaseModel


class AskAnalystRequest(BaseModel):
    question: str


class AskAnalystResponse(BaseModel):
    answer: str
