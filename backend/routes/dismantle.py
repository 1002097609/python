"""
拆解引擎路由模块（routes/dismantle.py）。

提供素材的五层拆解（L1-L5）相关接口，负责将营销素材从抽象到具体逐层拆分为：
  L1 主题层、L2 策略层、L3 结构层、L4 元素层、L5 表达层。
拆解完成后，素材状态自动更新为"已拆解"。

路由列表：
  POST /api/dismantle/                     - 创建拆解记录
  GET  /api/dismantle/{id}                 - 根据拆解 ID 查询拆解详情
  GET  /api/dismantle/by-material/{id}     - 根据素材 ID 查询对应的拆解记录
  PUT  /api/dismantle/{id}                 - 更新拆解记录
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.dismantle import Dismantle
from ..models.material import Material
from ..schemas.dismantle import DismantleCreate, DismantleUpdate, DismantleResponse
from ..services.ai_dismantle import analyze_material
from ..response import success, created as created_response, error

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", status_code=201)
def create_dismantle(data: DismantleCreate, db: Session = Depends(get_db)):
    """
    为指定素材创建 L1-L5 拆解记录。
    """
    try:
        material = db.query(Material).filter(Material.id == data.material_id).first()
        if not material:
            return error("素材不存在", 404)

        dismantle = Dismantle(**data.model_dump())
        db.add(dismantle)
        material.status = 1

        db.commit()
        db.refresh(dismantle)
        return created_response(DismantleResponse.model_validate(dismantle).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Create dismantle failed: {e}", exc_info=True)
        return error(f"创建拆解记录失败: {str(e)}", 500)


@router.get("/{dismantle_id}")
def get_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    """根据拆解记录 ID 查询拆解详情。"""
    try:
        dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
        if not dismantle:
            return error("拆解记录不存在", 404)
        return success(DismantleResponse.model_validate(dismantle).model_dump())
    except Exception as e:
        logger.error(f"Get dismantle {dismantle_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


@router.get("/by-material/{material_id}")
def get_dismantle_by_material(material_id: int, db: Session = Depends(get_db)):
    """根据素材 ID 查询对应的拆解记录。"""
    try:
        dismantle = db.query(Dismantle).filter(Dismantle.material_id == material_id).first()
        if not dismantle:
            return error("该素材尚未拆解", 404)
        return success(DismantleResponse.model_validate(dismantle).model_dump())
    except Exception as e:
        logger.error(f"Get dismantle by material {material_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


@router.get("/by-material/{material_id}/history")
def get_dismantle_history(material_id: int, db: Session = Depends(get_db)):
    """查询指定素材的所有拆解历史版本。"""
    try:
        items = db.query(Dismantle).filter(
            Dismantle.material_id == material_id
        ).order_by(Dismantle.created_at.desc()).all()
        return success([DismantleResponse.model_validate(i).model_dump() for i in items])
    except Exception as e:
        logger.error(f"Get dismantle history {material_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


@router.put("/{dismantle_id}")
def update_dismantle(dismantle_id: int, data: DismantleUpdate, db: Session = Depends(get_db)):
    """更新拆解记录。支持部分更新。"""
    try:
        dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
        if not dismantle:
            return error("拆解记录不存在", 404)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(dismantle, key, value)

        db.commit()
        db.refresh(dismantle)
        return success(DismantleResponse.model_validate(dismantle).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Update dismantle {dismantle_id} failed: {e}", exc_info=True)
        return error(f"更新失败: {str(e)}", 500)


# ============================================================
# AI 辅助拆解
# ============================================================

class AiAnalyzeRequest(BaseModel):
    """AI 辅助拆解请求模型"""
    title: str
    content: str
    platform: Optional[str] = ""
    category: Optional[str] = ""


class AiAnalyzeResponse(BaseModel):
    """AI 辅助拆解响应模型"""
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None
    l3_structure: Optional[list] = None
    l4_elements: Optional[dict] = None
    l5_expressions: Optional[dict] = None
    _meta: Optional[dict] = None


@router.post("/ai-analyze")
def ai_analyze_dismantle(
    data: AiAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    AI 辅助拆解接口。
    """
    try:
        if not data.title and not data.content:
            return error("标题和内容不能同时为空", 400)

        result = analyze_material(
            title=data.title or "",
            content=data.content or "",
            platform=data.platform or "",
            category=data.category or "",
        )

        # 校验 meta 中的 category 是否存在于 option 表
        if result.get("_meta", {}).get("detected_category"):
            from ..models.option import Option
            cat = result["_meta"]["detected_category"]
            existing_cat = db.query(Option).filter(
                Option.group_key == "category", Option.value == cat, Option.is_active == 1
            ).first()
            if not existing_cat:
                result["_meta"]["detected_category"] = "通用"

        return success(AiAnalyzeResponse(**result).model_dump())
    except Exception as e:
        logger.error(f"AI analyze failed: {e}", exc_info=True)
        return error(f"AI 分析失败: {str(e)}", 500)
