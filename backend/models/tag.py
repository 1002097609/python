from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from backend.database import Base


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20), comment="标签类型：platform/category/style/strategy")

    __table_args__ = (
        UniqueConstraint("name", "type", name="uk_name_type"),
    )


class MaterialTag(Base):
    __tablename__ = "material_tag"

    material_id = Column(Integer, ForeignKey("material.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True)
