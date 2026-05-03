"""
裂变预设路由模块（routes/fission_preset.py）。

提供裂变预设的 CRUD 管理接口。预设是预配置的裂变模板，
用户可在裂变页面一键加载，避免重复填写品类、风格、替换内容等。

路由列表：
  GET    /api/fission-preset/      - 获取所有启用的预设列表
  GET    /api/fission-preset/{id}  - 获取单个预设详情
  POST   /api/fission-preset/      - 创建预设
  PUT    /api/fission-preset/{id}  - 更新预设
  DELETE /api/fission-preset/{id}  - 删除预设
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.fission_preset import FissionPreset
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

router = APIRouter()


class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config_json: dict
    sort_order: int = 0


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[dict] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None


@router.get("/")
def list_presets(db: Session = Depends(get_db)):
    """获取所有启用的预设列表，按排序权重排列。"""
    try:
        items = (
            db.query(FissionPreset)
            .filter(FissionPreset.is_active == 1)
            .order_by(FissionPreset.sort_order, FissionPreset.id)
            .all()
        )
        return success([{
            "id": i.id,
            "name": i.name,
            "description": i.description,
            "config_json": i.config_json,
            "sort_order": i.sort_order,
            "is_active": i.is_active,
            "created_at": str(i.created_at) if i.created_at else None,
        } for i in items])
    except Exception as e:
        logger.error(f"List presets failed: {e}", exc_info=True)
        return error(f"查询预设失败: {str(e)}", 500)


@router.get("/{preset_id}")
def get_preset(preset_id: int, db: Session = Depends(get_db)):
    """获取单个预设详情。"""
    try:
        item = db.query(FissionPreset).filter(FissionPreset.id == preset_id).first()
        if not item:
            return error("预设不存在", 404)
        return success({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "config_json": item.config_json,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "created_at": str(item.created_at) if item.created_at else None,
        })
    except Exception as e:
        logger.error(f"Get preset {preset_id} failed: {e}", exc_info=True)
        return error(f"查询预设失败: {str(e)}", 500)


@router.post("/", status_code=201)
def create_preset(data: PresetCreate, db: Session = Depends(get_db)):
    """创建新预设。"""
    try:
        item = FissionPreset(**data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        log_operation(db, "fission_preset", item.id, "create", {"name": item.name})
        return created_response({
            "id": item.id,
            "name": item.name,
            "message": "创建成功",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Create preset failed: {e}", exc_info=True)
        return error(f"创建预设失败: {str(e)}", 500)


@router.put("/{preset_id}")
def update_preset(preset_id: int, data: PresetUpdate, db: Session = Depends(get_db)):
    """更新预设信息，支持部分更新。"""
    try:
        item = db.query(FissionPreset).filter(FissionPreset.id == preset_id).first()
        if not item:
            return error("预设不存在", 404)
        changed = []
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(item, key, value)
                changed.append(key)
        db.commit()
        db.refresh(item)
        log_operation(db, "fission_preset", preset_id, "update", {"changed_fields": changed})
        return success({
            "id": item.id,
            "name": item.name,
            "message": "更新成功",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Update preset {preset_id} failed: {e}", exc_info=True)
        return error(f"更新预设失败: {str(e)}", 500)


@router.delete("/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    """删除指定预设。"""
    try:
        item = db.query(FissionPreset).filter(FissionPreset.id == preset_id).first()
        if not item:
            return error("预设不存在", 404)
        name = item.name
        db.delete(item)
        db.commit()
        log_operation(db, "fission_preset", preset_id, "delete", {"name": name})
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete preset {preset_id} failed: {e}", exc_info=True)
        return error(f"删除预设失败: {str(e)}", 500)
