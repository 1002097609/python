from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class EffectData(Base):
    __tablename__ = "effect_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, comment="关联素材ID")
    fission_id = Column(Integer, comment="关联裂变素材ID")
    platform = Column(String(50), comment="投放平台")
    impressions = Column(Integer, comment="展示量")
    clicks = Column(Integer, comment="点击量")
    ctr = Column(DECIMAL(5, 2), comment="点击率%")
    conversions = Column(Integer, comment="转化量")
    cvr = Column(DECIMAL(5, 2), comment="转化率%")
    cost = Column(DECIMAL(10, 2), comment="花费（元）")
    revenue = Column(DECIMAL(10, 2), comment="收入（元）")
    roi = Column(DECIMAL(5, 2), comment="ROI")
    cpa = Column(DECIMAL(10, 2), comment="单次转化成本")
    stat_date = Column(Date, comment="数据日期")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_effect_material", "material_id"),
        Index("idx_effect_fission", "fission_id"),
        Index("idx_effect_date", "stat_date"),
    )
