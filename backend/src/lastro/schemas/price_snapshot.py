from datetime import date as date_

from pydantic import BaseModel, ConfigDict


class SnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: date_
    portfolio_value_cents: int
    emergency_reserve_value_cents: int
