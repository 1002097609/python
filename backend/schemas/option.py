from pydantic import BaseModel
from typing import Optional


class OptionCreate(BaseModel):
    group_key: str
    label: str
    value: str
    sort_order: int = 0


class OptionUpdate(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None


class OptionResponse(BaseModel):
    id: int
    group_key: str
    label: str
    value: str
    sort_order: int
    is_active: int

    class Config:
        from_attributes = True
