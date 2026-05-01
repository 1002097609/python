"""
素材模型模块

定义 Material（素材）ORM 模型，对应数据库中的 material 表。
素材是系统的核心数据实体，是拆解和裂变的起点。
每条素材记录代表一个待拆解或已拆解的营销内容（视频/图文/文字）。

主要字段：
  id: 自增主键
  title/content: 素材标题和原始内容
  platform: 投放平台（抖音/小红书/快手等）
  category: 所属品类（护肤/彩妆/零食/母婴等）
  media_type: 素材类型（video/image/text）
  source_url: 原始素材链接
  status: 拆解状态（0=未拆解 1=已拆解 2=已归档）
  created_by/created_at/updated_at: 审计字段
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from backend.database import Base


class Material(Base):
    """
    素材表（material）

    存储从各平台采集的原始营销素材，是拆解引擎的输入来源。
    通过 status 字段跟踪素材的生命周期：未拆解 -> 已拆解 -> 已归档。
    通过 platform 和 category 建立索引，支持按平台和品类筛选素材。

    关联关系：
      - 一个素材对应一个拆解记录（Dismantle），通过 dismantle 表关联
      - 一个素材可关联多个标签（Tag），通过 material_tag 关联表建立多对多关系
    """

    __tablename__ = "material"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 素材标题，最多 200 字符，非空
    title = Column(String(200), nullable=False, comment="素材标题")

    # 原始素材内容（脚本/文案等），Text 类型支持长文本
    content = Column(Text, nullable=False, comment="原始素材内容")

    # 投放平台：如"抖音"、"小红书"、"快手"等
    platform = Column(String(50), comment="平台：抖音/小红书/快手")

    # 业务品类，如"护肤"、"彩妆"、"零食"等，从数据库 option 表 category 分组动态加载
    category = Column(String(50), comment="业务品类，动态从 option 表加载")

    # 素材类型：video（视频）/ image（图文）/ text（纯文字）
    media_type = Column(String(20), comment="类型：video/image/text")

    # 原始素材的外部链接，最多 500 字符
    source_url = Column(String(500), comment="原始链接")

    # 拆解状态：0=待拆解 1=已拆解（关联 dismantle 记录） 2=已归档
    status = Column(Integer, default=0, comment="0=未拆解 1=已拆解 2=已归档")

    # 录入人标识
    created_by = Column(String(50), comment="录入人")

    # 创建时间，自动由数据库设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 更新时间，创建时自动设置，修改时由数据库自动更新
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 建立复合索引，加速按平台、品类、状态的查询
    __table_args__ = (
        Index("idx_platform", "platform"),   # 按平台筛选
        Index("idx_category", "category"),   # 按品类筛选
        Index("idx_status", "status"),       # 按拆分状态筛选
    )
