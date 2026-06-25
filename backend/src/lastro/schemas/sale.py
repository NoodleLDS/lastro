from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class SaleCreate(BaseModel):
    position_id: int
    date: date_
    quantity: float
    unit_price_cents: int


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position_id: int
    date: date_
    quantity: float
    unit_price_cents: int
