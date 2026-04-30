from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SkeletonCreate(BaseModel):
    name: str
    skeleton_type: Optional[str] = None
    source_material_id: Optional[int] = None
    strategy_desc: Optional[str] = None
    structure_json: Optional[list] = None
    elements_json: Optional[dict] = None
    style_tags: Optional[list] = None
    platform: Optional[str] = None


class SkeletonUpdate(BaseModel):
    name: Optional[str] = None
    strategy_desc: Optional[str] = None
    structure_json: Optional[list] = None
    elements_json: Optional[dict] = None


class SkeletonResponse(BaseModel):
    id: int
    name: str
    skeleton_type: Optional[str]
    usage_count: int
    avg_roi: Optional[float]
    avg_ctr: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
