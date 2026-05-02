"""
素材数据校验模式模块（schemas/material.py）。

定义素材相关的 Pydantic Schema 类，用于素材创建、更新和响应时的数据校验与序列化。
素材（Material）是系统中最基础的数据单元，代表一条原始营销素材。

包含的 Schema：
  - MaterialCreate   : 创建素材时的请求参数模型
  - MaterialUpdate   : 更新素材时的请求参数模型（所有字段可选）
  - MaterialResponse : 响应时的素材数据模型
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MaterialCreate(BaseModel):
    """
    创建素材的请求参数模型。

    字段说明：
        title (str):         必填。素材标题，用于标识和检索。
        content (str):       必填。素材正文内容，可以是台词、描述等。
        platform (str):      可选。投放平台，如 "抖音"、"快手"。
        category (str):      可选。素材品类，如 "护肤"、"零食"。
        media_type (str):    可选。媒体类型，如 "video"（视频）、"image"（图片）、"text"（文本）。
        source_url (str):    可选。原始素材的来源 URL。
        created_by (str):    可选。创建人标识。
    """
    title: str                          # 素材标题（必填）
    content: str                        # 素材正文内容（必填）
    platform: Optional[str] = None      # 投放平台
    category: Optional[str] = None      # 素材品类
    media_type: Optional[str] = None    # 媒体类型
    source_url: Optional[str] = None    # 来源链接
    created_by: Optional[str] = None    # 创建人


class MaterialUpdate(BaseModel):
    """
    更新素材的请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        title (str):      素材标题。
        content (str):    素材正文内容。
        platform (str):   投放平台。
        category (str):   素材品类。
        media_type (str): 媒体类型。
        source_url (str): 来源链接。
        status (int):     素材状态，0=未拆解，1=已拆解。
    """
    title: Optional[str] = None         # 素材标题
    content: Optional[str] = None       # 素材正文
    platform: Optional[str] = None      # 投放平台
    category: Optional[str] = None      # 素材品类
    media_type: Optional[str] = None    # 媒体类型
    source_url: Optional[str] = None    # 来源链接
    status: Optional[int] = None         # 素材状态（0=未拆解，1=已拆解）


class BatchStatusUpdate(BaseModel):
    """
    批量更新素材状态的请求参数模型。

    字段说明：
        ids (list[int]):   要更新的素材 ID 列表，至少包含一个。
        status (int):      目标状态值（0=未拆解，1=已拆解，2=已归档）。
    """
    ids: list[int]
    status: int


class MaterialResponse(BaseModel):
    """
    素材响应数据模型，用于 API 返回的素材数据结构。

    字段说明：
        id (int):            素材唯一标识 ID（数据库自动生成）。
        title (str):         素材标题。
        content (str):       素材正文内容。
        platform (str):      投放平台。
        category (str):      素材品类。
        media_type (str):    媒体类型。
        source_url (str):    来源链接。
        status (int):        素材状态，0=未拆解，1=已拆解。
        created_by (str):    创建人。
        created_at (datetime): 创建时间戳。
        updated_at (datetime): 最后更新时间戳（可能为空）。
    """
    id: int                              # 素材 ID
    title: str                           # 素材标题
    content: str                         # 素材正文
    platform: Optional[str]              # 投放平台
    category: Optional[str]              # 素材品类
    media_type: Optional[str]            # 媒体类型
    source_url: Optional[str]            # 来源链接
    status: int                          # 素材状态
    created_by: Optional[str]            # 创建人
    created_at: datetime                 # 创建时间
    updated_at: Optional[datetime]       # 更新时间

    class Config:
        # 允许从 SQLAlchemy ORM 对象属性中读取数据（兼容 ORM 模式）
        from_attributes = True
