from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    name: str
    color: str = "#c084fc"
    closing_day: int | None = Field(default=None, ge=1, le=31)


class CardUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    closing_day: int | None = Field(default=None, ge=1, le=31)
    is_active: bool | None = None


class CardRead(BaseModel):
    id: int
    name: str
    color: str
    closing_day: int | None
    is_active: bool
