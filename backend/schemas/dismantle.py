"""
拆解数据校验模式模块（schemas/dismantle.py）。

定义素材拆解（L1-L5）相关的 Pydantic Schema 类，用于拆解数据的创建、更新和响应时的校验与序列化。
拆解是将营销素材从抽象到具体拆分为五层结构化数据的过程。

包含的 Schema：
  - DismantleCreate  : 创建拆解记录时的请求参数模型
  - DismantleUpdate  : 更新拆解记录时的请求参数模型（所有字段可选）
  - DismantleResponse: 响应时的拆解数据模型

五层拆解模型（L1-L5）：
  L1 主题层 -- 素材讲什么（枝干，可复用）
  L2 策略层 -- 用什么策略/情绪打动用户（枝干，可复用）
  L3 结构层 -- 内容骨架/段落逻辑（枝干，可复用）
  L4 元素层 -- 标题公式、钩子句式、过渡方式等（枝杈，可插拔）
  L5 表达层 -- 具体文字/视觉表达（叶子，可替换）
"""

from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime


class DismantleCreate(BaseModel):
    """
    创建拆解记录的请求参数模型。

    字段说明：
        material_id (int):   必填。关联的素材 ID，拆解操作必须基于已有素材。

        # L1 主题层
        l1_topic (str):      必填。主题，素材的核心讲述内容，如"护肤流程"。
        l1_core_point (str): 核心观点，素材最想传达的一句话。

        # L2 策略层
        l2_strategy (list):  策略列表，如 ["反差对比", "痛点切入", "情感共鸣"]。
        l2_emotion (str):    情绪基调，如"轻松幽默"、"焦虑共鸣"。

        # L3 结构层
        l3_structure (list): 必填。结构列表，描述素材的段落逻辑，如 [{"name": "开头", "function": "痛点共鸣"}, ...]。
        l3_summary (str):    结构摘要，对整体内容骨架的文字描述。

        # L4 元素层
        l4_elements (dict):  元素字典，包含标题公式、钩子句式、过渡方式等可插拔元素。

        # L5 表达层
        l5_expressions (dict): 表达字典，包含具体的文字表达、视觉元素描述等可替换内容。

    校验规则：
        - l1_topic 和 l3_structure 为必填（核心骨架来源），缺失返回 400。
        - l3_structure 每个元素必须包含 name 和 function 字段。
    """
    material_id: int                    # 关联素材 ID（必填）

    # L1 主题层
    l1_topic: Optional[str] = None       # 主题内容（必填，骨架提取必需）
    l1_core_point: Optional[str] = None  # 核心观点

    # L2 策略层
    l2_strategy: Optional[list] = None   # 策略列表
    l2_emotion: Optional[str] = None     # 情绪基调

    # L3 结构层
    l3_structure: Optional[list] = None  # 结构列表（必填，骨架提取必需）
    l3_summary: Optional[str] = None     # 结构摘要

    # L4 元素层
    l4_elements: Optional[dict] = None   # 可插拔元素集合

    # L5 表达层
    l5_expressions: Optional[dict] = None  # 可替换的具体表达内容

    @model_validator(mode="after")
    def validate_core_fields(self):
        """校验核心骨架字段完整性：l1_topic 和 l3_structure 为必填。"""
        errors = []
        if not self.l1_topic or not str(self.l1_topic).strip():
            errors.append("l1_topic 为必填字段，是骨架提取的核心来源")
        if not self.l3_structure:
            errors.append("l3_structure 为必填字段，是骨架提取的核心来源")
        elif isinstance(self.l3_structure, list):
            for i, sec in enumerate(self.l3_structure):
                if not isinstance(sec, dict):
                    errors.append(f"l3_structure[{i}] 必须为对象")
                    continue
                if not sec.get("name"):
                    errors.append(f"l3_structure[{i}].name 为必填字段")
                if not sec.get("function"):
                    errors.append(f"l3_structure[{i}].function 为必填字段")
        if errors:
            raise ValueError("; ".join(errors))
        return self


class DismantleUpdate(BaseModel):
    """
    更新拆解记录的请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        各字段含义同 DismantleCreate，均为可选。

        skeleton_id (int): 关联骨架 ID，在从拆解记录提取骨架后回填此字段。
        updated_by (str): 最后编辑人。
    """
    # L1 主题层
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None

    # L2 策略层
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None

    # L3 结构层
    l3_structure: Optional[list] = None
    l3_summary: Optional[str] = None

    # L4 元素层
    l4_elements: Optional[dict] = None

    # L5 表达层
    l5_expressions: Optional[dict] = None

    # 关联骨架（提取骨架后回填）
    skeleton_id: Optional[int] = None

    # 编辑人
    updated_by: Optional[str] = None


class DismantleResponse(BaseModel):
    """
    拆解响应数据模型，用于 API 返回的拆解数据结构。

    字段说明：
        id (int):               拆解记录唯一标识 ID。
        material_id (int):      关联素材 ID。

        # L1-L5 各层数据
        l1_topic (str):         主题层 - 主题。
        l1_core_point (str):    主题层 - 核心观点。
        l2_strategy (list):     策略层 - 策略列表。
        l2_emotion (str):       策略层 - 情绪基调。
        l3_structure (list):    结构层 - 结构列表。
        l3_summary (str):       结构层 - 结构摘要。
        l4_elements (dict):     元素层 - 可插拔元素。
        l5_expressions (dict):  表达层 - 可替换表达。

        skeleton_id (int):      已提取的骨架 ID（可能为空）。
        dismantled_by (str):    拆解人标识。
        created_at (datetime):  拆解时间戳。
    """
    id: int                              # 拆解记录 ID
    material_id: int                     # 关联素材 ID

    # L1 主题层
    l1_topic: Optional[str]
    l1_core_point: Optional[str]

    # L2 策略层
    l2_strategy: Optional[list]
    l2_emotion: Optional[str]

    # L3 结构层
    l3_structure: Optional[list]
    l3_summary: Optional[str]

    # L4 元素层
    l4_elements: Optional[dict]

    # L5 表达层
    l5_expressions: Optional[dict]

    skeleton_id: Optional[int]           # 关联骨架 ID
    dismantled_by: Optional[str]         # 拆解人
    version: int = 1                     # 版本号
    updated_by: Optional[str]            # 最后编辑人
    created_at: datetime                 # 创建时间
    updated_at: Optional[datetime] = None  # 最后更新时间

    class Config:
        # 允许从 SQLAlchemy ORM 对象属性中读取数据
        from_attributes = True
