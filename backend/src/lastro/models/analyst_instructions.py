from sqlmodel import Field, SQLModel


class AnalystInstructions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(default="")
