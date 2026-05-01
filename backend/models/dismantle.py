"""
拆解模型模块

定义 Dismantle（拆解）ORM 模型，对应数据库中的 dismantle 表。
实现素材的五层拆解模型（L1-L5），将一个完整素材从抽象到具体逐层拆分：
  L1 主题层 -> L2 策略层 -> L3 结构层 -> L4 元素层 -> L5 表达层

主要字段：
  id: 自增主键
  material_id: 关联的素材 ID（material 表外键）
  l1_topic / l1_core_point: L1 主题层和核心卖点
  l2_strategy / l2_emotion: L2 策略标签和情绪策略
  l3_structure / l3_summary: L3 结构段落模板和一句话描述
  l4_elements: L4 元素模块（标题公式、钩子句式等）
  l5_expressions: L5 具体表达（金句、数据引用等）
  skeleton_id: 从拆解中提取出的骨架 ID
  dismantled_by: 拆解人
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from backend.database import Base


class Dismantle(Base):
    """
    拆解表（dismantle）

    存储素材的五层拆解结果。每条记录对应一个素材的完整拆解分析。
    L2/L3/L4/L5 使用 JSON 字段存储结构化数据，便于灵活扩展。
    拆解完成后，可从 L2-L4 提炼出可复用的骨架（Skeleton），存入 skeleton 表。

    关联关系：
      - material_id -> material.id （多对一，一个素材对应一个拆解记录）
      - skeleton_id -> skeleton.id （可选，拆解提炼出的骨架）
    """

    __tablename__ = "dismantle"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联的素材 ID，非空，指明本次拆解是针对哪个素材的
    material_id = Column(Integer, nullable=False, comment="关联素材 ID")

    # ==================== L1 主题层（素材讲什么） ====================
    # 主题描述，如"黄褐斑的瓦解过程见证"
    l1_topic = Column(String(200), comment="主题：素材讲什么")

    # 核心卖点提炼，如"成分党+实测验证+闺蜜分享"
    l1_core_point = Column(String(500), comment="核心卖点")

    # ==================== L2 策略层（用什么策略打动用户） ====================
    # 策略标签数组，如 ["共鸣型", "成分党", "对比测评"]
    l2_strategy = Column(JSON, comment='策略标签：["共鸣型","成分党","对比测评"]')

    # 情绪策略描述文案
    l2_emotion = Column(String(200), comment="情绪策略描述")

    # ==================== L3 结构层（内容骨架/段落逻辑） ====================
    # 结构段落 JSON，包含段落名称、功能、时长占比和模板
    # 示例：[{"name":"开场钩子","function":"吸引注意","ratio":0.15,"template":"你是否也在为...发愁？"}, ...]
    l3_structure = Column(JSON, comment="结构段落：[{name, function, ratio, template},...]")

    # 结构的一句话概述，便于快速了解该素材的骨架
    l3_summary = Column(String(500), comment="结构一句话描述")

    # ==================== L4 元素层（可插拔的元素模块） ====================
    # 元素模块 JSON，包含标题公式、钩子句式、过渡方式等
    # 示例：{"title_formula":"数字+痛点+承诺","hook":"反向提问式","transition":"自然转折"}
    l4_elements = Column(JSON, comment='元素模块：{"title_formula":"...","hook":"..."}')

    # ==================== L5 表达层（具体文字/视觉表达） ====================
    # 具体表达 JSON，包含金句列表和数据引用等
    # 示例：{"golden_sentences":["这是我用过最好的..."],"data_refs":["87%用户反馈有效"]}
    l5_expressions = Column(JSON, comment='具体表达：{"golden_sentences":[],"data_refs":[]}')

    # ==================== 元数据 ====================
    # 从本拆解中提炼出的骨架 ID，关联 skeleton 表
    skeleton_id = Column(Integer, comment="提取出的骨架 ID")

    # 执行拆解的用户标识
    dismantled_by = Column(String(50), comment="拆解人")

    # 创建时间，自动设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 索引：加速按素材 ID 和骨架 ID 的查询
    __table_args__ = (
        Index("idx_dismantle_material", "material_id"),  # 按素材查找拆解记录
        Index("idx_dismantle_skeleton", "skeleton_id"),  # 按骨架查找拆解决录
    )
