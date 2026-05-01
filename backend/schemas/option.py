"""
选项数据校验模式模块（schemas/option.py）。

定义下拉框选项（Option）相关的 Pydantic Schema 类，用于选项数据的创建、更新和响应时的校验与序列化。
选项数据用于前端页面的各种可配置下拉选择器，如投放平台列表、素材品类列表、风格标签列表等。
选项按 group_key 分组管理，每个分组下的选项可独立排序。

包含的 Schema：
  - OptionCreate  : 创建选项时的请求参数模型
  - OptionUpdate  : 更新选项时的请求参数模型（所有字段可选）
  - OptionResponse: 响应时的选项数据模型
"""

from pydantic import BaseModel
from typing import Optional


class OptionCreate(BaseModel):
    """
    创建选项的请求参数模型。

    字段说明：
        group_key (str):    必填。分组标识，用于将选项归类，如 "platform"（平台）、"category"（品类）、"style"（风格）。
        label (str):        必填。显示文本，前端下拉框中用户看到的选项名称，如"抖音"、"快手"。
        value (str):        必填。实际值，后端存储和逻辑处理使用的值，如 "douyin"、"kuaishou"。
        sort_order (int):   排序权重，数值越小排序越靠前。默认值为 0。
    """
    group_key: str                  # 分组标识（必填），如 platform / category / style
    label: str                      # 显示文本（必填），用户看到的选项名称
    value: str                      # 实际值（必填），后端使用的值
    sort_order: int = 0             # 排序权重，越小越靠前


class OptionUpdate(BaseModel):
    """
    更新选项的请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        label (str):        显示文本。
        value (str):        实际值。
        sort_order (int):   排序权重。
        is_active (int):    启用状态，1=启用（前端可见），0=禁用（前端不可见）。
    """
    label: Optional[str] = None      # 显示文本
    value: Optional[str] = None      # 实际值
    sort_order: Optional[int] = None  # 排序权重
    is_active: Optional[int] = None   # 启用状态（1=启用，0=禁用）


class OptionResponse(BaseModel):
    """
    选项响应数据模型，用于 API 返回的选项数据结构。

    字段说明：
        id (int):         选项唯一标识 ID。
        group_key (str):  分组标识。
        label (str):      显示文本。
        value (str):      实际值。
        sort_order (int): 排序权重。
        is_active (int):  启用状态，1=启用，0=禁用。
    """
    id: int                          # 选项 ID
    group_key: str                   # 分组标识
    label: str                       # 显示文本
    value: str                       # 实际值
    sort_order: int                  # 排序权重
    is_active: int                   # 启用状态

    class Config:
        # 允许从 SQLAlchemy ORM 对象属性中读取数据
        from_attributes = True
