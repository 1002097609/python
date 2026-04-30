from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from backend.database import Base


class Material(Base):
    __tablename__ = "material"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="素材标题")
    content = Column(Text, nullable=False, comment="原始素材内容")
    platform = Column(String(50), comment="平台：抖音/小红书/快手")
    category = Column(String(50), comment="品类：护肤/彩妆/零食/母婴")
    media_type = Column(String(20), comment="类型：video/image/text")
    source_url = Column(String(500), comment="原始链接")
    status = Column(Integer, default=0, comment="0=未拆解 1=已拆解 2=已归档")
    created_by = Column(String(50), comment="录入人")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_platform", "platform"),
        Index("idx_category", "category"),
        Index("idx_status", "status"),
    )
