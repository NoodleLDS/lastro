from pydantic import BaseModel

from lastro.models.position import AssetType


class AllocationTargetCreate(BaseModel):
    asset_type: AssetType
    target_percentage: float


class AllocationTargetUpdate(BaseModel):
    target_percentage: float | None = None


class AllocationTargetRead(BaseModel):
    id: int
    asset_type: AssetType
    target_percentage: float
