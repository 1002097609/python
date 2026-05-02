"""
骨架模型模块

定义 Skeleton（骨架）ORM 模型，对应数据库中的 skeleton 表。
骨架是从优质素材的拆解（Dismantle）中提取出的可复用模板，包含 L2-L3-L4 层信息。
裂变引擎将骨架与新内容结合，批量产出新的营销素材。

主要字段：
  id: 自增主键
  name: 骨架名称（如"测评对比型"、"红黑榜型"）
  skeleton_type: 骨架分类标签
  source_material_id: 来源素材 ID
  strategy_desc: L2 策略描述
  structure_json: L3 结构模板（段落名称、功能、占比）
  elements_json: L4 元素模块模板
  style_tags: 适用的风格标签
  usage_count / avg_roi / avg_ctr: 效果统计字段，用于指导裂变选材
  suitable_for: 适用场景列表
  platform: 适用平台
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class Skeleton(Base):
    """
    骨架表（skeleton）

    存储从拆解结果中提炼出的可复用内容骨架。骨架本质上是一个模板，
    保留了原素材的策略层（L2）、结构层（L3）和元素层（L4），
    但剥离了具体的主题（L1）和表达（L5），使其可以与新内容组合裂变。

    效果闭环：每次裂变投放后，effect_data 中的实际 CTR/ROI 会
    回写到 avg_ctr 和 avg_roi 字段，指导裂变引擎优先选择高效果骨架。

    关联关系：
      - source_material_id -> material.id （从哪个素材提炼而来）
      - 被 fission 表引用（一次裂变选择一个骨架）
    """

    __tablename__ = "skeleton"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 骨架名称，如"测评对比型"、"红黑榜型"、"闺蜜分享型"等
    name = Column(String(100), nullable=False, comment="骨架名称：测评对比型/红黑榜型...")

    # 骨架分类标签，用于归类筛选
    skeleton_type = Column(String(50), comment="骨架类型")

    # 来源素材 ID，记录本骨架是从哪个素材的拆解中提炼出来的
    source_material_id = Column(Integer, ForeignKey("material.id", ondelete="SET NULL"), comment="来源素材 ID")

    # L2 策略层描述素材来源的营销策略
    strategy_desc = Column(String(500), comment="L2 策略描述")

    # L3 结构层模板（JSON），包含段落名称、功能、时长占比和模板句式
    # 示例：[{"name":"开场钩子","function":"吸引注意","ratio":0.15,"template":"你是否也在为...发愁？"}]
    structure_json = Column(JSON, nullable=False, comment="L3 结构模板：段落名称、功能、占比")

    # L4 元素层模板（JSON），包含标题公式、钩子句式等可插拔元素
    elements_json = Column(JSON, comment="L4 元素模块模板")

    # 适用风格标签（JSON 数组），如 ["专业感", "亲和力", "紧迫感"]
    style_tags = Column(JSON, comment="适用风格标签")

    # 该骨架被裂变引擎使用的次数，次数越多说明验证越充分
    usage_count = Column(Integer, default=0, comment="被使用次数")

    # 平均 ROI（多位小数），基于历史裂变投放数据计算
    avg_roi = Column(DECIMAL(5, 2), comment="平均 ROI")

    # 平均点击率（百分比），基于历史裂变投放数据计算
    avg_ctr = Column(DECIMAL(5, 2), comment="平均 CTR%")

    # 适用场景列表（JSON 数组），如 ["产品对比", "红黑榜", "横向评测"]
    suitable_for = Column(JSON, comment='适用场景：["产品对比","红黑榜","横向评测"]')

    # 适用的投放平台（如"抖音"、"小红书"等）
    platform = Column(String(50), comment="适用平台")

    # 创建时间，自动设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 索引：按骨架类型、使用次数、ROI、来源素材建立索引
    __table_args__ = (
        Index("idx_skeleton_type", "skeleton_type"),          # 按类型筛选骨架
        Index("idx_skeleton_usage", "usage_count"),           # 按使用次数排序（热门程度）
        Index("idx_skeleton_roi", "avg_roi"),                 # 按 ROI 排序（效果优先）
        Index("idx_skeleton_source_material", "source_material_id"),  # 按来源素材查找骨架
        Index("idx_skeleton_platform", "platform"),           # 按平台筛选
    )
