from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from backend.database import Base


class Option(Base):
    __tablename__ = "option"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 选项分组，如 platform / category / style / strategy / skeleton_type / golden_sentence / data_ref / visual_desc / fission_mode
    group_key = Column(String(50), nullable=False, comment="选项分组标识")
    label = Column(String(200), nullable=False, comment="显示文本")
    value = Column(String(200), nullable=False, comment="实际值")
    sort_order = Column(Integer, default=0, comment="排序权重，越小越靠前")
    is_active = Column(Integer, default=1, comment="1=启用 0=禁用")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_option_group", "group_key"),
        Index("idx_option_active", "is_active"),
    )
