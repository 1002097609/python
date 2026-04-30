from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class Skeleton(Base):
    __tablename__ = "skeleton"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="骨架名称：测评对比型/红黑榜型...")
    skeleton_type = Column(String(50), comment="骨架类型")
    source_material_id = Column(Integer, comment="来源素材ID")
    strategy_desc = Column(String(500), comment="L2策略描述")
    structure_json = Column(JSON, nullable=False, comment="L3结构模板：段落名称、功能、占比")
    elements_json = Column(JSON, comment="L4元素模块模板")
    style_tags = Column(JSON, comment="适用风格标签")
    usage_count = Column(Integer, default=0, comment="被使用次数")
    avg_roi = Column(DECIMAL(5, 2), comment="平均ROI")
    avg_ctr = Column(DECIMAL(5, 2), comment="平均CTR%")
    suitable_for = Column(JSON, comment='适用场景：["产品对比","红黑榜","横向评测"]')
    platform = Column(String(50), comment="适用平台")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_skeleton_type", "skeleton_type"),
        Index("idx_skeleton_usage", "usage_count"),
        Index("idx_skeleton_roi", "avg_roi"),
    )
