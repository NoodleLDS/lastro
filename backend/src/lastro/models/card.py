from sqlmodel import Field, SQLModel


class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    color: str = Field(default="#c084fc")
    closing_day: int | None = Field(default=None)
    is_active: bool = Field(default=True)
