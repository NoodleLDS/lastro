from pydantic import BaseModel


class MerchantRuleCreate(BaseModel):
    pattern: str
    category_id: int


class MerchantRuleUpdate(BaseModel):
    pattern: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


class MerchantRuleRead(BaseModel):
    id: int
    pattern: str
    category_id: int
    is_active: bool
