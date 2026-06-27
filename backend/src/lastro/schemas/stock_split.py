from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class StockSplitCreate(BaseModel):
    position_id: int
    date: date_
    ratio_from: float
    ratio_to: float


class StockSplitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position_id: int
    date: date_
    ratio_from: float
    ratio_to: float
