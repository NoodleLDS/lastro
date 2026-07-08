from pydantic import BaseModel, ConfigDict


class IncomeCreate(BaseModel):
    description: str
    amount_cents: int
    year: int
    month: int


class IncomeUpdate(BaseModel):
    description: str | None = None
    amount_cents: int | None = None
    year: int | None = None
    month: int | None = None


class IncomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    amount_cents: int
    year: int
    month: int


class FixedExpenseCreate(BaseModel):
    description: str
    amount_cents: int
    year: int
    month: int
    category_id: int | None = None


class FixedExpenseUpdate(BaseModel):
    description: str | None = None
    amount_cents: int | None = None
    year: int | None = None
    month: int | None = None
    category_id: int | None = None
    is_paid: bool | None = None


class FixedExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    amount_cents: int
    year: int
    month: int
    category_id: int | None
    is_paid: bool


class VariableExpenseCreate(BaseModel):
    description: str
    amount_cents: int
    year: int
    month: int
    category_id: int | None = None


class VariableExpenseUpdate(BaseModel):
    description: str | None = None
    amount_cents: int | None = None
    year: int | None = None
    month: int | None = None
    category_id: int | None = None
    is_paid: bool | None = None


class VariableExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    amount_cents: int
    year: int
    month: int
    category_id: int | None
    is_paid: bool
