"""
标签模型模块

定义 Tag（标签）和 MaterialTag（素材标签关联）ORM 模型，
对应数据库中的 tag 表和 material_tag 关联表。
实现素材的多维度标签分类体系，支持按平台、品类、风格、策略等维度归类筛选。

Tag 主要字段：
  id: 自增主键
  name: 标签名称
  type: 标签类型（platform/category/style/strategy）

MaterialTag 主要字段：
  material_id: 素材 ID（复合主键之一，外键 -> material.id）
  tag_id: 标签 ID（复合主键之一，外键 -> tag.id）
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from backend.database import Base


class Tag(Base):
    """
    标签表（tag）

    存储系统内所有可用的标签。通过 type 字段区分不同维度的标签：
      - platform: 平台标签（抖音/小红书/快手等）
      - category: 品类标签（护肤/彩妆/零食/母婴等）
      - style: 风格标签（专业感/亲和力/紧迫感等）
      - strategy: 策略标签（共鸣型/成分党/对比测评等）

    同一名称在不同 type 下可存在不同记录（如 name="抖音" type="platform"
    和 name="抖音" type="style" 可以共存），通过联合唯一约束保证
    同 type 下不出现重复名称。
    """

    __tablename__ = "tag"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 标签显示名称，如"抖音"、"护肤"、"专业感"等
    name = Column(String(50), nullable=False)

    # 标签类型分类，用于区分不同维度的标签体系
    type = Column(String(20), comment="标签类型：platform/category/style/strategy")

    # 联合唯一约束：同一 type 下的 name 不能重复
    __table_args__ = (
        UniqueConstraint("name", "type", name="uk_name_type"),
    )


class MaterialTag(Base):
    """
    素材标签关联表（material_tag）

    实现素材（Material）与标签（Tag）之间的多对多关系。
    使用 material_id + tag_id 作为复合主键，确保同一素材不会被重复打上相同标签。

    关联关系：
      - material_id -> material.id （关联的素材）
      - tag_id -> tag.id （关联的标签）
    """

    __tablename__ = "material_tag"

    # 素材 ID，作为复合主键的一部分，同时是 material 表的外键
    material_id = Column(Integer, ForeignKey("material.id"), primary_key=True)

    # 标签 ID，作为复合主键的一部分，同时是 tag 表的外键
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True)
