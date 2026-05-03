"""
标签管理路由模块（routes/tag.py）。

提供标签的 CRUD 操作和素材标签关联管理接口。
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.tag import Tag, MaterialTag
from ..models.material import Material
from ..models.option import Option
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    type: str
    option_id: Optional[int] = None


class TagUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    option_id: Optional[int] = None


class TagResponse(BaseModel):
    id: int
    name: str
    type: str
    option_id: Optional[int] = None

    class Config:
        from_attributes = True


class MaterialTagCreate(BaseModel):
    tag_id: int


class TagFromOption(BaseModel):
    option_id: int


@router.get("/")
def list_tags(
    tag_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """查询标签列表，支持按类型筛选。"""
    try:
        query = db.query(Tag)
        if tag_type:
            query = query.filter(Tag.type == tag_type)
        items = query.order_by(Tag.type, Tag.name).all()
        return success([TagResponse.model_validate(i).model_dump() for i in items])
    except Exception as e:
        logger.error(f"List tags failed: {e}", exc_info=True)
        return error(f"查询标签失败: {str(e)}", 500)


@router.get("/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """查询单个标签的详细信息。"""
    try:
        item = db.query(Tag).filter(Tag.id == tag_id).first()
        if not item:
            return error("标签不存在", 404)
        return success(TagResponse.model_validate(item).model_dump())
    except Exception as e:
        logger.error(f"Get tag {tag_id} failed: {e}", exc_info=True)
        return error(f"查询标签失败: {str(e)}", 500)


@router.post("/", status_code=201)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    """创建新标签。"""
    try:
        if data.option_id:
            opt = db.query(Option).filter(Option.id == data.option_id).first()
            if not opt:
                return error(f"选项 ID {data.option_id} 不存在", 404)
            tag_name = opt.label
            tag_type = opt.group_key
        else:
            tag_name = data.name
            tag_type = data.type

        existing = db.query(Tag).filter(Tag.name == tag_name, Tag.type == tag_type).first()
        if existing:
            return error(f"标签「{tag_name}」在类型「{tag_type}」下已存在", 409)

        tag = Tag(name=tag_name, type=tag_type, option_id=data.option_id)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        log_operation(db, "tag", tag.id, "create", {"name": tag.name, "type": tag.type})
        return created_response(TagResponse.model_validate(tag).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Create tag failed: {e}", exc_info=True)
        return error(f"创建标签失败: {str(e)}", 500)


@router.post("/from-option", status_code=201)
def create_tag_from_option(data: TagFromOption, db: Session = Depends(get_db)):
    """从已有的 option 记录创建标签。"""
    try:
        opt = db.query(Option).filter(Option.id == data.option_id).first()
        if not opt:
            return error(f"选项 ID {data.option_id} 不存在", 404)

        existing = db.query(Tag).filter(Tag.name == opt.label, Tag.type == opt.group_key).first()
        if existing:
            return error(f"标签「{opt.label}」在类型「{opt.group_key}」下已存在", 409)

        tag = Tag(name=opt.label, type=opt.group_key, option_id=opt.id)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        log_operation(db, "tag", tag.id, "create", {"name": tag.name, "type": tag.type, "from_option": True})
        return created_response(TagResponse.model_validate(tag).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Create tag from option failed: {e}", exc_info=True)
        return error(f"创建标签失败: {str(e)}", 500)


@router.put("/{tag_id}")
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    """更新标签信息。支持部分更新。"""
    try:
        item = db.query(Tag).filter(Tag.id == tag_id).first()
        if not item:
            return error("标签不存在", 404)

        if data.option_id is not None:
            opt = db.query(Option).filter(Option.id == data.option_id).first()
            if not opt:
                return error(f"选项 ID {data.option_id} 不存在", 404)
            item.name = opt.label
            item.type = opt.group_key
            item.option_id = data.option_id
        else:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(item, key, value)

        db.commit()
        db.refresh(item)
        log_operation(db, "tag", tag_id, "update", {"name": item.name, "type": item.type})
        return success(TagResponse.model_validate(item).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Update tag {tag_id} failed: {e}", exc_info=True)
        return error(f"更新标签失败: {str(e)}", 500)


@router.get("/{tag_id}/usage")
def get_tag_usage(tag_id: int, db: Session = Depends(get_db)):
    """查询标签被多少素材使用。"""
    try:
        item = db.query(Tag).filter(Tag.id == tag_id).first()
        if not item:
            return error("标签不存在", 404)
        count = db.query(func.count(MaterialTag.material_id)).filter(
            MaterialTag.tag_id == tag_id
        ).scalar()
        return success({"tag_id": tag_id, "usage_count": count})
    except Exception as e:
        logger.error(f"Get tag usage {tag_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """删除指定标签。"""
    try:
        item = db.query(Tag).filter(Tag.id == tag_id).first()
        if not item:
            return error("标签不存在", 404)

        usage_count = db.query(func.count(MaterialTag.material_id)).filter(
            MaterialTag.tag_id == tag_id
        ).scalar()

        if usage_count > 0 and not force:
            return error(f"标签「{item.name}」仍被 {usage_count} 个素材使用，强制删除请传 force=true", 409)

        db.query(MaterialTag).filter(MaterialTag.tag_id == tag_id).delete()
        db.delete(item)
        db.commit()
        log_operation(db, "tag", tag_id, "delete", {"name": item.name, "type": item.type, "usage_count": usage_count})
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete tag {tag_id} failed: {e}", exc_info=True)
        return error(f"删除标签失败: {str(e)}", 500)


@router.get("/material/{material_id}")
def get_material_tags(material_id: int, db: Session = Depends(get_db)):
    """获取指定素材的所有标签。"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)

        tags = db.query(Tag).join(MaterialTag, MaterialTag.tag_id == Tag.id).filter(
            MaterialTag.material_id == material_id
        ).order_by(Tag.type, Tag.name).all()
        return success([TagResponse.model_validate(t).model_dump() for t in tags])
    except Exception as e:
        logger.error(f"Get material tags {material_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


@router.post("/material/{material_id}/tags", status_code=201)
def add_material_tag(material_id: int, data: MaterialTagCreate, db: Session = Depends(get_db)):
    """给素材打上标签。"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)

        tag = db.query(Tag).filter(Tag.id == data.tag_id).first()
        if not tag:
            return error("标签不存在", 404)

        existing = db.query(MaterialTag).filter(
            MaterialTag.material_id == material_id,
            MaterialTag.tag_id == data.tag_id,
        ).first()
        if existing:
            return error("该素材已打上此标签", 409)

        mt = MaterialTag(material_id=material_id, tag_id=data.tag_id)
        db.add(mt)
        db.commit()
        log_operation(db, "tag", tag.id, "create", {"action": "add_to_material", "material_id": material_id, "tag_name": tag.name})
        return created_response(TagResponse.model_validate(tag).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Add material tag failed: {e}", exc_info=True)
        return error(f"打标签失败: {str(e)}", 500)


@router.delete("/material/{material_id}/tags/{tag_id}")
def remove_material_tag(material_id: int, tag_id: int, db: Session = Depends(get_db)):
    """移除素材上的标签。"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)

        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            return error("标签不存在", 404)

        mt = db.query(MaterialTag).filter(
            MaterialTag.material_id == material_id,
            MaterialTag.tag_id == tag_id,
        ).first()
        if not mt:
            return error("该素材未打此标签", 404)

        db.delete(mt)
        db.commit()
        log_operation(db, "tag", tag_id, "update", {"action": "remove_from_material", "material_id": material_id})
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Remove material tag failed: {e}", exc_info=True)
        return error(f"移除标签失败: {str(e)}", 500)
