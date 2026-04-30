from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class Fission(Base):
    __tablename__ = "fission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skeleton_id = Column(Integer, nullable=False, comment="使用的骨架ID")
    source_material_id = Column(Integer, comment="母体素材ID")
    fission_mode = Column(String(50), comment="裂变模式：replace_leaf/replace_branch/replace_style")
    new_topic = Column(String(200), comment="新主题")
    new_category = Column(String(50), comment="新品类")
    new_platform = Column(String(50), comment="新平台")
    new_style = Column(String(50), comment="新风格")
    replacement_json = Column(JSON, comment="替换内容映射")
    output_title = Column(String(200), comment="产出素材标题")
    output_content = Column(Text, comment="产出素材内容")
    output_status = Column(Integer, default=0, comment="0=草稿 1=待审核 2=已采用 3=已投放")
    predicted_ctr = Column(String(20), comment="预测CTR范围")
    predicted_roi = Column(String(20), comment="预测ROI范围")
    actual_ctr = Column(DECIMAL(5, 2), comment="实际CTR%")
    actual_roi = Column(DECIMAL(5, 2), comment="实际ROI")
    created_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_fission_skeleton", "skeleton_id"),
        Index("idx_fission_status", "output_status"),
    )
