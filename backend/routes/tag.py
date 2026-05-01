"""
标签管理路由模块（routes/tag.py）。

提供标签的 CRUD 操作和素材标签关联管理接口。
标签支持按类型（type）分类：
  - platform: 平台标签（抖音/小红书/快手等）
  - category: 品类标签（护肤/彩妆/零食/母婴等）
  - style: 风格标签（专业感/亲和力/紧迫感等）
  - strategy: 策略标签（共鸣型/成分党/对比测评等）

数据模型：
  - tag 表通过 option_id 外键关联 option 表
  - option_id 不为空时，name 和 type 从 option 冗余存储
  - option_id 为空时，为纯用户自定义标签

路由列表（注册在 /api/tag/ 下）：
  GET    /api/tag/                        - 标签列表（支持按 type 筛选）
  POST   /api/tag/                        - 创建标签
  PUT    /api/tag/{id}                    - 更新标签
  DELETE /api/tag/{id}                    - 删除标签
  GET    /api/tag/{id}                    - 标签详情
  POST   /api/tag/from-option             - 从已有 option 创建标签
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
from ..models.option import Option

# 创建标签管理专用路由器
router = APIRouter()


# ============================================================
# Pydantic 请求/响应模型
# ============================================================

class TagCreate(BaseModel):
    """
    标签创建请求参数模型。

    字段说明：
        name (str):       标签名称，如"抖音"、"护肤"、"专业感"等。
        type (str):       标签类型，取值：platform / category / style / strategy。
        option_id (int):  可选。关联的 option 表记录 ID。
                          若传入，则 name 和 type 从 option 自动填充（忽略传入的 name/type）。
    """
    name: str
    type: str
    option_id: Optional[int] = None


class TagUpdate(BaseModel):
    """
    标签更新请求参数模型。所有字段均为可选，支持部分更新。

    字段说明：
        name (str):       标签名称。
        type (str):       标签类型。
        option_id (int):  关联的 option 表记录 ID。
                          若传入且非空，则 name 和 type 从 option 自动填充。
    """
    name: Optional[str] = None
    type: Optional[str] = None
    option_id: Optional[int] = None


class TagResponse(BaseModel):
    """
    标签响应数据模型。

    字段说明：
        id (int):         标签唯一标识 ID。
        name (str):       标签名称。
        type (str):       标签类型。
        option_id (int):  关联的 option 记录 ID（可为空）。
    """
    id: int
    name: str
    type: str
    option_id: Optional[int] = None

    class Config:
        from_attributes = True


class MaterialTagCreate(BaseModel):
    """
    素材标签关联创建请求参数模型。

    字段说明：
        tag_id (int): 要关联的标签 ID。
    """
    tag_id: int


class TagFromOption(BaseModel):
    """
    从 option 创建标签的请求参数模型。

    字段说明：
        option_id (int): 必填。要关联的 option 表记录 ID。
    """
    option_id: int


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

    支持两种方式：
    1. 直接传入 name + type 创建（option_id 为空）
    2. 传入 option_id，自动从 option 表读取 name 和 type

    同一 type 下的 name 不能重复（由数据库联合唯一约束保证）。

    请求参数：
        data (TagCreate): 标签创建模型，包含 name、type 和可选的 option_id。

    返回值：
        TagResponse: 创建成功的标签对象。

    异常：
        HTTP 409: 当同类型下已存在同名标签时抛出。
        HTTP 404: 当指定的 option_id 不存在时抛出。
    """
    # 如果传了 option_id，从 option 表获取 name 和 type
    if data.option_id:
        opt = db.query(Option).filter(Option.id == data.option_id).first()
        if not opt:
            raise HTTPException(status_code=404, detail=f"选项 ID {data.option_id} 不存在")
        tag_name = opt.label
        tag_type = opt.group_key
    else:
        tag_name = data.name
        tag_type = data.type

    # 检查同类型下是否已存在同名标签
    existing = db.query(Tag).filter(Tag.name == tag_name, Tag.type == tag_type).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"标签「{tag_name}」在类型「{tag_type}」下已存在")

    tag = Tag(name=tag_name, type=tag_type, option_id=data.option_id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.post("/from-option", response_model=TagResponse, status_code=201)
def create_tag_from_option(data: TagFromOption, db: Session = Depends(get_db)):
    """
    从已有的 option 记录创建标签。

    这是一个便捷接口，用于将 option 表中的选项快速创建为标签，
    确保 option 和 tag 数据一致。

    请求参数：
        data (TagFromOption): 包含 option_id。

    返回值：
        TagResponse: 创建成功的标签对象。

    异常：
        HTTP 404: 当指定的 option_id 不存在时抛出。
        HTTP 409: 当对应的标签已存在时抛出。
    """
    opt = db.query(Option).filter(Option.id == data.option_id).first()
    if not opt:
        raise HTTPException(status_code=404, detail=f"选项 ID {data.option_id} 不存在")

    # 检查是否已存在对应的标签
    existing = db.query(Tag).filter(Tag.name == opt.label, Tag.type == opt.group_key).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"标签「{opt.label}」在类型「{opt.group_key}」下已存在")

    tag = Tag(name=opt.label, type=opt.group_key, option_id=opt.id)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    """
    更新标签信息。支持部分更新（仅传入需要修改的字段）。

    特殊逻辑：
    - 如果更新了 option_id，则自动从关联的 option 读取 name 和 type
    - 如果清除了 option_id（传入 null），则保持原有 name/type 不变

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

    # 如果更新了 option_id，从关联的 option 自动填充 name 和 type
    if data.option_id is not None:
        opt = db.query(Option).filter(Option.id == data.option_id).first()
        if not opt:
            raise HTTPException(status_code=404, detail=f"选项 ID {data.option_id} 不存在")
        item.name = opt.label
        item.type = opt.group_key
        item.option_id = data.option_id
    else:
        # 仅更新传入的字段（name 或 type）
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    """
    删除指定标签。

    同时会级联删除该标签与所有素材的关联记录（material_tag 表中对应行）。
    不会影响 option 表中的记录。

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

    返回值:
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
