"""
骨架数据校验模式模块（schemas/skeleton.py）。

定义骨架（Skeleton）相关的 Pydantic Schema 类，用于骨架创建、更新和响应时的数据校验与序列化。
骨架是从拆解结果中提取的可复用内容模板（L2-L4层），代表可跨品类复用的内容框架。

包含的 Schema：
  - SkeletonCreate  : 创建骨架时的请求参数模型
  - SkeletonUpdate  : 更新骨架时的请求参数模型（所有字段可选）
  - SkeletonResponse: 响应时的骨架数据模型
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SkeletonCreate(BaseModel):
    """
    创建骨架的请求参数模型。

    字段说明：
        name (str):                必填。骨架名称，用于标识和检索，如"护肤测评型 — 护肤品推荐"。
        skeleton_type (str):       可选。骨架类型，如 "测评对比型"、"红黑榜型"、"误区纠正型"、"教程步骤型"、"通用型"。
        source_material_id (int):  可选。来源素材 ID，记录骨架是从哪个素材的拆解中提取的。
        strategy_desc (str):       可选。策略描述，记录该骨架的情感基调和说服策略。
        structure_json (list):     可选。结构 JSON，L3 层段落逻辑数据，描述内容骨架。
        elements_json (dict):      可选。元素 JSON，L4 层可插拔元素集合，如标题公式、钩子句式。
        style_tags (list):         可选。风格标签列表，如 ["轻松幽默", "快节奏"]。
        platform (str):            可选。投放平台，如 "抖音"。
    """
    name: str                           # 骨架名称（必填）
    skeleton_type: Optional[str] = None     # 骨架类型
    source_material_id: Optional[int] = None  # 来源素材 ID
    strategy_desc: Optional[str] = None     # 策略描述
    structure_json: Optional[list] = None   # L3 结构层 JSON
    elements_json: Optional[dict] = None    # L4 元素层 JSON
    style_tags: Optional[list] = None       # 风格标签列表
    platform: Optional[str] = None          # 投放平台


class SkeletonUpdate(BaseModel):
    """
    更新骨架的请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        name (str):             骨架名称。
        strategy_desc (str):    策略描述。
        structure_json (list):  结构 JSON（L3 层）。
        elements_json (dict):   元素 JSON（L4 层）。
    """
    name: Optional[str] = None              # 骨架名称
    strategy_desc: Optional[str] = None     # 策略描述
    structure_json: Optional[list] = None   # 结构层 JSON
    elements_json: Optional[dict] = None    # 元素层 JSON


class SkeletonResponse(BaseModel):
    """
    骨架响应数据模型，用于 API 返回的骨架数据结构。

    字段说明：
        id (int):             骨架唯一标识 ID。
        name (str):           骨架名称。
        skeleton_type (str):  骨架类型。
        usage_count (int):    使用次数，记录该骨架已被用于裂变的次数。
        avg_roi (float):       平均 ROI，基于所有裂变素材的实际投放效果计算。
        avg_ctr (float):       平均 CTR，基于所有裂变素材的实际点击率计算。
        created_at (datetime): 创建时间戳。
    """
    id: int                              # 骨架 ID
    name: str                            # 骨架名称
    skeleton_type: Optional[str]         # 骨架类型
    usage_count: int                     # 使用次数
    avg_roi: Optional[float]             # 平均 ROI
    avg_ctr: Optional[float]             # 平均 CTR
    created_at: datetime                 # 创建时间

    class Config:
        # 允许从 SQLAlchemy ORM 对象属性中读取数据
        from_attributes = True
