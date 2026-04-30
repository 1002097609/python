from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MaterialCreate(BaseModel):
    title: str
    content: str
    platform: Optional[str] = None
    category: Optional[str] = None
    media_type: Optional[str] = None
    source_url: Optional[str] = None
    created_by: Optional[str] = None


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None
    media_type: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[int] = None


class MaterialResponse(BaseModel):
    id: int
    title: str
    content: str
    platform: Optional[str]
    category: Optional[str]
    media_type: Optional[str]
    source_url: Optional[str]
    status: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
