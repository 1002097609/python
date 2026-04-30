from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DismantleCreate(BaseModel):
    material_id: int
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None
    l3_structure: Optional[list] = None
    l3_summary: Optional[str] = None
    l4_elements: Optional[dict] = None
    l5_expressions: Optional[dict] = None


class DismantleUpdate(BaseModel):
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None
    l3_structure: Optional[list] = None
    l3_summary: Optional[str] = None
    l4_elements: Optional[dict] = None
    l5_expressions: Optional[dict] = None
    skeleton_id: Optional[int] = None


class DismantleResponse(BaseModel):
    id: int
    material_id: int
    l1_topic: Optional[str]
    l1_core_point: Optional[str]
    l2_strategy: Optional[list]
    l2_emotion: Optional[str]
    l3_structure: Optional[list]
    l3_summary: Optional[str]
    l4_elements: Optional[dict]
    l5_expressions: Optional[dict]
    skeleton_id: Optional[int]
    dismantled_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
