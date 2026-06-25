from sqlmodel import Field, SQLModel


class MerchantRule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    pattern: str = Field(index=True)
    category_id: int = Field(foreign_key="category.id")
    is_active: bool = Field(default=True)
