from pydantic import BaseModel


class CardCreate(BaseModel):
    name: str
    color: str = "#c084fc"
    closing_day: int | None = None


class CardUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    closing_day: int | None = None
    is_active: bool | None = None


class CardRead(BaseModel):
    id: int
    name: str
    color: str
    closing_day: int | None
    is_active: bool
