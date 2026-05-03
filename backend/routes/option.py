"""
选项数据路由模块（routes/option.py）- 新版。

提供下拉框选项的 CRUD 管理接口，支持按分组（group_key）和启用状态筛选。

路由列表：
  GET    /api/option/         - 查询选项列表
  GET    /api/option/groups   - 获取所有已有的分组 key 列表
  GET    /api/option/{id}     - 查询单个选项详情
  POST   /api/option/         - 创建新选项
  PUT    /api/option/{id}     - 更新选项信息
  DELETE /api/option/{id}     - 删除选项
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.option import Option
from ..schemas.option import OptionCreate, OptionUpdate, OptionResponse
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def list_options(
    group_key: Optional[str] = Query(None, description="按分组筛选"),
    is_active: Optional[int] = Query(None, comment="1=启用 0=禁用"),
    db: Session = Depends(get_db),
):
    """查询选项列表，支持按分组标识和启用状态筛选。"""
    try:
        query = db.query(Option)
        if group_key:
            query = query.filter(Option.group_key == group_key)
        if is_active is not None:
            query = query.filter(Option.is_active == is_active)
        items = query.order_by(Option.sort_order.asc(), Option.id.asc()).all()
        return success([OptionResponse.model_validate(i).model_dump() for i in items])
    except Exception as e:
        logger.error(f"List options failed: {e}", exc_info=True)
        return error(f"查询选项失败: {str(e)}", 500)


@router.get("/groups")
def list_group_keys(db: Session = Depends(get_db)):
    """获取所有已有的分组 key 列表。"""
    try:
        rows = db.query(Option.group_key).distinct().all()
        return success([r[0] for r in rows])
    except Exception as e:
        logger.error(f"List group keys failed: {e}", exc_info=True)
        return error(f"查询分组失败: {str(e)}", 500)


@router.get("/{option_id}")
def get_option(option_id: int, db: Session = Depends(get_db)):
    """根据选项 ID 查询单个选项的详细信息。"""
    try:
        item = db.query(Option).filter(Option.id == option_id).first()
        if not item:
            return error("选项不存在", 404)
        return success(OptionResponse.model_validate(item).model_dump())
    except Exception as e:
        logger.error(f"Get option {option_id} failed: {e}", exc_info=True)
        return error(f"查询选项失败: {str(e)}", 500)


@router.post("/", status_code=201)
def create_option(data: OptionCreate, db: Session = Depends(get_db)):
    """创建新的下拉框选项。"""
    try:
        item = Option(**data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        log_operation(db, "option", item.id, "create", {"group_key": item.group_key, "label": item.label})
        return created_response(OptionResponse.model_validate(item).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Create option failed: {e}", exc_info=True)
        return error(f"创建选项失败: {str(e)}", 500)


@router.put("/{option_id}")
def update_option(option_id: int, data: OptionUpdate, db: Session = Depends(get_db)):
    """更新指定选项的信息。支持部分更新。"""
    try:
        item = db.query(Option).filter(Option.id == option_id).first()
        if not item:
            return error("选项不存在", 404)

        changed = list(data.model_dump(exclude_unset=True).keys())
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        db.commit()
        db.refresh(item)
        log_operation(db, "option", option_id, "update", {"changed_fields": changed})
        return success(OptionResponse.model_validate(item).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Update option {option_id} failed: {e}", exc_info=True)
        return error(f"更新选项失败: {str(e)}", 500)


@router.delete("/{option_id}")
def delete_option(
    option_id: int,
    hard: bool = Query(False, description="是否物理删除（默认软删除）"),
    db: Session = Depends(get_db)
):
    """删除指定的选项记录。默认执行软删除。"""
    try:
        item = db.query(Option).filter(Option.id == option_id).first()
        if not item:
            return error("选项不存在", 404)

        if hard:
            db.delete(item)
        else:
            item.is_active = 0

        log_operation(db, "option", item.id, "delete", {
            "label": item.label,
            "group_key": item.group_key,
            "hard": hard,
        })
        db.commit()
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete option {option_id} failed: {e}", exc_info=True)
        return error(f"删除选项失败: {str(e)}", 500)
