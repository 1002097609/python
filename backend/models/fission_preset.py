"""
裂变预设模型模块

定义 FissionPreset（裂变预设）ORM 模型，对应数据库中的 fission_preset 表。
预设是预先配置好的裂变模板，包含默认的品类、风格、替换内容等，
用户可在裂变页面快速加载预设，避免重复填写。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON
from sqlalchemy.sql import func
from backend.database import Base


class FissionPreset(Base):
    """
    裂变预设表（fission_preset）

    存储预配置的裂变模板，用户可在裂变页面一键加载预设配置。
    config_json 字段存储完整的预设配置，包括：
      - new_category: 默认品类
      - new_style: 默认风格
      - new_platform: 默认平台
      - replacement: 默认替换内容（L5 金句/数据/视觉，L4 钩子/转折/互动）
    """

    __tablename__ = "fission_preset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="预设名称")
    description = Column(String(500), comment="预设描述")
    config_json = Column(JSON, nullable=False, comment="预设配置 JSON")
    sort_order = Column(Integer, default=0, comment="排序权重，越小越靠前")
    is_active = Column(Integer, default=1, comment="1=启用 0=禁用")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_fission_preset_active", "is_active"),
        Index("idx_fission_preset_sort", "sort_order"),
    )
