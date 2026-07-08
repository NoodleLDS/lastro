from sqlmodel import Field, SQLModel


class VariableExpense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    amount_cents: int
    year: int = Field(index=True)
    month: int = Field(index=True)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    is_paid: bool = Field(default=False)
