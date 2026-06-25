from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class DividendCreate(BaseModel):
    position_id: int
    date: date_
    amount_cents: int


class DividendRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position_id: int
    date: date_
    amount_cents: int
