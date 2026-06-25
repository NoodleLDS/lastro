from sqlmodel import Field, SQLModel

from lastro.models.position import AssetType


class AllocationTarget(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    asset_type: AssetType = Field(unique=True, index=True)
    target_percentage: float
