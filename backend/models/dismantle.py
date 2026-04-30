from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from backend.database import Base


class Dismantle(Base):
    __tablename__ = "dismantle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, nullable=False, comment="关联素材ID")
    # L1 主题层
    l1_topic = Column(String(200), comment="主题：素材讲什么")
    l1_core_point = Column(String(500), comment="核心卖点")
    # L2 策略层
    l2_strategy = Column(JSON, comment='策略标签：["共鸣型","成分党","对比测评"]')
    l2_emotion = Column(String(200), comment="情绪策略描述")
    # L3 结构层
    l3_structure = Column(JSON, comment="结构段落：[{name, function, ratio, template},...]")
    l3_summary = Column(String(500), comment="结构一句话描述")
    # L4 元素层
    l4_elements = Column(JSON, comment='元素模块：{"title_formula":"...","hook":"..."}')
    # L5 表达层
    l5_expressions = Column(JSON, comment='具体表达：{"golden_sentences":[],"data_refs":[]}')
    # 关联骨架
    skeleton_id = Column(Integer, comment="提取出的骨架ID")
    dismantled_by = Column(String(50), comment="拆解人")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_dismantle_material", "material_id"),
        Index("idx_dismantle_skeleton", "skeleton_id"),
    )
