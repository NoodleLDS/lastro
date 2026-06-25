from pydantic import BaseModel, Field

from lastro.models.position import AssetType


class AllocationTargetCreate(BaseModel):
    asset_type: AssetType
    target_percentage: float = Field(ge=0, le=100)


class AllocationTargetUpdate(BaseModel):
    target_percentage: float | None = Field(default=None, ge=0, le=100)


class AllocationTargetRead(BaseModel):
    id: int
    asset_type: AssetType
    target_percentage: float
