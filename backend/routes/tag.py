"""
标签管理路由模块（routes/tag.py）。

提供标签的 CRUD 操作和素材标签关联管理接口。
标签支持按类型（type）分类：
  - platform: 平台标签（抖音/小红书/快手等）
  - category: 品类标签（护肤/彩妆/零食/母婴等）
  - style: 风格标签（专业感/亲和力/紧迫感等）
  - strategy: 策略标签（共鸣型/成分党/对比测评等）

路由列表（注册在 /api/tag/ 下）：
  GET    /api/tag/                        - 标签列表（支持按 type 筛选）
  POST   /api/tag/                        - 创建标签
  PUT    /api/tag/{id}                    - 更新标签
  DELETE /api/tag/{id}                    - 删除标签
  GET    /api/tag/{id}                    - 标签详情
  GET    /api/tag/material/{material_id}          - 获取素材的标签列表
  POST   /api/tag/material/{material_id}/tags     - 给素材打标签
  DELETE /api/tag/material/{material_id}/tags/{tag_id} - 移除素材标签
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.tag import Tag, MaterialTag
from ..models.material import Material

# 创建标签管理专用路由器
router = APIRouter()


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class TagCreate(BaseModel):
    """
    标签创建请求参数模型。

    字段说明：
        name (str): 标签名称，如"抖音"、"护肤"、"专业感"等。
        type (str): 标签类型，取值：platform / category / style / strategy。
    """
    name: str
    type: str


class TagUpdate(BaseModel):
    """
    标签更新请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        name (str): 标签名称。
        type (str): 标签类型。
    """
    name: Optional[str] = None
    type: Optional[str] = None


class TagResponse(BaseModel):
    """
    标签响应数据模型。

    字段说明：
        id (int): 标签唯一标识 ID。
        name (str): 标签名称。
        type (str): 标签类型。
    """
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


class MaterialTagCreate(BaseModel):
    """
    素材标签关联创建请求参数模型。

    字段说明：
        tag_id (int): 要关联的标签 ID。
    """
    tag_id: int


# ============================================================
# 标签 CRUD
# ============================================================

@router.get("/", response_model=list[TagResponse])
def list_tags(
    tag_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    查询标签列表，支持按类型筛选。

    请求参数：
        tag_type (str): 按标签类型筛选（可选），如 platform / category / style / strategy。

    返回值：
        list[TagResponse]: 标签列表，按类型和名称排序。
    """
    query = db.query(Tag)

    # 按标签类型筛选
    if tag_type:
        query = query.filter(Tag.type == tag_type)

    # 先按类型排序，再按名称排序
    items = query.order_by(Tag.type, Tag.name).all()
    return items


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    查询单个标签的详细信息。

    请求参数：
        tag_id (int): 标签 ID。

    返回值：
        TagResponse: 标签详情。

    异常：
        HTTP 404: 当标签不存在时抛出。
    """
    item = db.query(Tag).filter(Tag.id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="标签不存在")
    return item


@router.post("/", response_model=TagResponse, status_code=201)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    """
    创建新标签。

    同一 type 下的 name 不能重复（由数据库联合唯一约束保证）。

    请求参数：
        data (TagCreate): 标签创建模型，包含 name 和 type。

    返回值：
        TagResponse: 创建成功的标签对象。

    异常：
        HTTP 409: 当同类型下已存在同名标签时抛出。
    """
    # 检查同类型下是否已存在同名标签
    existing = db.query(Tag).filter(Tag.name == data.name, Tag.type == data.type).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"标签「{data.name}」在类型「{data.type}」下已存在")

    tag = Tag(name=data.name, type=data.type)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    """
    更新标签信息。支持部分更新（仅传入需要修改的字段）。

    请求参数：
        tag_id (int): 要更新的标签 ID。
        data (TagUpdate): 更新模型，所有字段均为可选。

    返回值：
        TagResponse: 更新后的标签对象。

    异常：
        HTTP 404: 当标签不存在时抛出。
    """
    item = db.query(Tag).filter(Tag.id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 仅更新传入的字段
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    删除指定标签。

    同时会级联删除该标签与所有素材的关联记录（material_tag 表中对应行）。

    请求参数：
        tag_id (int): 要删除的标签 ID。

    返回值：
        无返回体，HTTP 状态码 204 表示删除成功。

    异常：
        HTTP 404: 当标签不存在时抛出。
    """
    item = db.query(Tag).filter(Tag.id == tag_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 级联删除关联表中的记录
    db.query(MaterialTag).filter(MaterialTag.tag_id == tag_id).delete()
    db.delete(item)
    db.commit()


# ============================================================
# 素材标签关联
# ============================================================

@router.get("/material/{material_id}", response_model=list[TagResponse])
def get_material_tags(material_id: int, db: Session = Depends(get_db)):
    """
    获取指定素材的所有标签。

    请求参数：
        material_id (int): 素材 ID。

    返回值：
        list[TagResponse]: 该素材关联的所有标签列表。

    异常：
        HTTP 404: 当素材不存在时抛出。
    """
    # 先检查素材是否存在
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 通过关联表查询素材的所有标签
    tags = db.query(Tag).join(MaterialTag, MaterialTag.tag_id == Tag.id).filter(
        MaterialTag.material_id == material_id
    ).order_by(Tag.type, Tag.name).all()
    return tags


@router.post("/material/{material_id}/tags", response_model=TagResponse, status_code=201)
def add_material_tag(material_id: int, data: MaterialTagCreate, db: Session = Depends(get_db)):
    """
    给素材打上标签。

    如果该素材已经打了此标签，则返回 409 冲突。

    请求参数：
        material_id (int): 素材 ID。
        data (MaterialTagCreate): 包含 tag_id。

    返回值：
        TagResponse: 关联成功的标签对象。

    异常：
        HTTP 404: 当素材或标签不存在时抛出。
        HTTP 409: 当该素材已打上此标签时抛出。
    """
    # 检查素材是否存在
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 检查标签是否存在
    tag = db.query(Tag).filter(Tag.id == data.tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 检查是否已关联
    existing = db.query(MaterialTag).filter(
        MaterialTag.material_id == material_id,
        MaterialTag.tag_id == data.tag_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="该素材已打上此标签")

    # 创建关联
    mt = MaterialTag(material_id=material_id, tag_id=data.tag_id)
    db.add(mt)
    db.commit()
    return tag


@router.delete("/material/{material_id}/tags/{tag_id}", status_code=204)
def remove_material_tag(material_id: int, tag_id: int, db: Session = Depends(get_db)):
    """
    移除素材上的标签。

    请求参数：
        material_id (int): 素材 ID。
        tag_id (int): 标签 ID。

    返回值：
        无返回体，HTTP 状态码 204 表示移除成功。

    异常：
        HTTP 404: 当素材、标签或关联不存在时抛出。
    """
    # 检查素材是否存在
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 检查标签是否存在
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 查找并删除关联
    mt = db.query(MaterialTag).filter(
        MaterialTag.material_id == material_id,
        MaterialTag.tag_id == tag_id,
    ).first()
    if not mt:
        raise HTTPException(status_code=404, detail="该素材未打此标签")

    db.delete(mt)
    db.commit()
