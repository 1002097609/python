"""
选项配置模型模块

定义 Option（选项配置）ORM 模型，对应数据库中的 option 表。
用于管理系统中的各类枚举选项，如平台列表、品类列表、风格列表、
策略标签、骨架类型、金句模板等。

通过 group_key 字段对不同类别的选项进行分组管理，
支持前端下拉菜单、复选框等 UI 组件的数据源动态加载。

常见 group_key 包括：
  - platform: 投放平台选项（抖音/小红书/快手等）
  - category: 业务品类选项（护肤/彩妆/零食/母婴等）
  - style: 内容风格选项
  - strategy: 营销策略选项
  - skeleton_type: 骨架类型选项
  - golden_sentence: 金句模板
  - data_ref: 数据引用模板
  - visual_desc: 视觉描述模板
  - fission_mode: 裂变模式选项
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from backend.database import Base


class Option(Base):
    """
    选项配置表（option）

    存储系统中所有可配置的下拉选项和枚举值。
    前端通过 group_key 请求对应分组的所有选项，用于渲染下拉菜单、
    复选框、单选按钮等交互组件。

    设计要点：
      - sort_order 控制同组内选项的显示顺序（越小越靠前）
      - is_active 支持软删除/禁用选项，无需从数据库中物理删除
      - label（显示文本）和 value（实际值）分离，支持国际化或多前端适配
    """

    __tablename__ = "option"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 选项分组标识，如 "platform"、"category"、"style"、"strategy"、
    # "skeleton_type"、"golden_sentence"、"data_ref"、"visual_desc"、"fission_mode" 等
    group_key = Column(String(50), nullable=False, comment="选项分组标识")

    # 前端显示给用户看的文本（如"抖音"、"小红书"等）
    label = Column(String(200), nullable=False, comment="显示文本")

    # 后端实际使用的值（如"douyin"、"xiaohongshu"等，或与前段显示文本相同）
    value = Column(String(200), nullable=False, comment="实际值")

    # 排序权重值，数值越小在同组内的显示位置越靠前，默认 0
    sort_order = Column(Integer, default=0, comment="排序权重，越小越靠前")

    # 启用状态：1=启用（前端可见），0=禁用（前端不显示，但数据不删除）
    is_active = Column(Integer, default=1, comment="1=启用 0=禁用")

    # 创建时间，自动设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 索引：按分组和启用状态加速查询，前端请求时最常见的查询模式
    __table_args__ = (
        Index("idx_option_group", "group_key"),    # 按分组获取所有选项（如获取全部平台列表）
        Index("idx_option_active", "is_active"),   # 过滤禁用选项（通常只查启用的）
    )
