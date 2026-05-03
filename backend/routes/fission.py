"""
裂变引擎路由模块（routes/fission.py）。

提供素材裂变功能：选择已有骨架 + 输入新内容，通过模板填充引擎组合生成新的素材文案。
支持三种裂变模式：
  - replace_leaf（换叶子）:  替换 L1+L5，骨架不变，效果保留约 85%
  - replace_branch（换枝杈）: 替换 L3+L4，主题不变，效果保留约 65%
  - replace_style（换表达）:  替换 L2+L5，骨架不变，效果保留约 70%

路由列表：
  POST /api/fission/ - 执行裂变操作，生成新素材文案
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.fission import Fission
from ..models.skeleton import Skeleton
from ..models.effect_data import EffectData
from ..services.fission_engine import generate_output
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

router = APIRouter()


class FissionRequest(BaseModel):
    """裂变请求参数模型"""
    skeleton_id: int
    source_material_id: Optional[int] = None
    fission_mode: str  # replace_leaf / replace_branch / replace_style
    new_topic: Optional[str] = None
    new_category: Optional[str] = None
    new_platform: Optional[str] = None
    new_style: Optional[str] = None
    replacement: Optional[dict] = None


class BatchFissionItem(BaseModel):
    """批量裂变单条参数"""
    new_topic: Optional[str] = None
    new_category: Optional[str] = None
    new_platform: Optional[str] = None
    new_style: Optional[str] = None
    replacement: Optional[dict] = None


class BatchFissionRequest(BaseModel):
    """批量裂变请求参数模型"""
    skeleton_id: int
    source_material_id: Optional[int] = None
    fission_mode: str
    items: list[BatchFissionItem]


def _create_single_fission(db, skeleton, data: FissionRequest) -> dict:
    """执行单次裂变的核心逻辑，返回创建的 fission 响应字典。"""
    structure = skeleton.structure_json
    elements = skeleton.elements_json
    strategy = skeleton.strategy_desc

    if isinstance(structure, str):
        structure = json.loads(structure)
    if isinstance(elements, str):
        elements = json.loads(elements)

    replacement = data.replacement or {}

    output_content = generate_output(
        fission_mode=data.fission_mode,
        structure=structure,
        elements=elements,
        strategy=strategy,
        new_topic=data.new_topic or "",
        replacement=replacement,
    )

    prediction = _predict_performance(skeleton, data.fission_mode, db)

    fission = Fission(
        skeleton_id=data.skeleton_id,
        source_material_id=data.source_material_id,
        fission_mode=data.fission_mode,
        new_topic=data.new_topic,
        new_category=data.new_category,
        new_platform=data.new_platform,
        new_style=data.new_style,
        replacement_json=replacement,
        output_title=f"{data.new_topic or '未命名'}",
        output_content=output_content,
        output_status=0,
        predicted_ctr_min=prediction["ctr_min"],
        predicted_ctr_max=prediction["ctr_max"],
        predicted_roi_min=prediction["roi_min"],
        predicted_roi_max=prediction["roi_max"],
    )
    db.add(fission)
    db.flush()

    return {
        "fission_id": fission.id,
        "output_title": fission.output_title,
        "output_content": output_content,
        "predicted_ctr_min": float(prediction["ctr_min"]),
        "predicted_ctr_max": float(prediction["ctr_max"]),
        "predicted_roi_min": float(prediction["roi_min"]),
        "predicted_roi_max": float(prediction["roi_max"]),
    }


@router.post("/", status_code=201)
def execute_fission(data: FissionRequest, db: Session = Depends(get_db)):
    """
    执行素材裂变操作。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == data.skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        result = _create_single_fission(db, skeleton, data)
        skeleton.usage_count = (skeleton.usage_count or 0) + 1

        db.commit()
        log_operation(db, "fission", result["fission_id"], "create", {
            "skeleton_id": data.skeleton_id,
            "fission_mode": data.fission_mode,
            "new_topic": data.new_topic,
            "predicted_ctr_min": result["predicted_ctr_min"],
            "predicted_ctr_max": result["predicted_ctr_max"],
            "predicted_roi_min": result["predicted_roi_min"],
            "predicted_roi_max": result["predicted_roi_max"],
        })

        return created_response(result)
    except Exception as e:
        db.rollback()
        logger.error(f"Execute fission failed: {e}", exc_info=True)
        return error(f"裂变失败: {str(e)}", 500)


@router.post("/batch", status_code=201)
def execute_batch_fission(data: BatchFissionRequest, db: Session = Depends(get_db)):
    """
    批量执行裂变操作：同一骨架 + 裂变模式，对多个新主题/品类批量生成素材。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == data.skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        if not data.items:
            return error("items 不能为空", 400)

        results = []
        for item in data.items:
            single_req = FissionRequest(
                skeleton_id=data.skeleton_id,
                source_material_id=data.source_material_id,
                fission_mode=data.fission_mode,
                new_topic=item.new_topic,
                new_category=item.new_category,
                new_platform=item.new_platform,
                new_style=item.new_style,
                replacement=item.replacement,
            )
            result = _create_single_fission(db, skeleton, single_req)
            results.append(result)

        skeleton.usage_count = (skeleton.usage_count or 0) + len(results)

        db.commit()
        log_operation(db, "fission", 0, "batch_create", {
            "skeleton_id": data.skeleton_id,
            "fission_mode": data.fission_mode,
            "count": len(results),
        })

        return created_response({
            "count": len(results),
            "items": results,
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Batch fission failed: {e}", exc_info=True)
        return error(f"批量裂变失败: {str(e)}", 500)


def _predict_performance(skeleton, fission_mode, db=None) -> dict:
    """效果预测函数：基于母体骨架的历史平均效果数据，乘以裂变模式系数，预测新素材的表现范围。"""
    mode_factor = None
    if db:
        from ..models.option import Option
        mode_option = db.query(Option).filter(
            Option.group_key == "fission_mode",
            Option.value == fission_mode,
            Option.is_active == 1,
        ).first()
        if mode_option:
            try:
                import re
                match = re.search(r'(\d+)%', mode_option.label)
                if match:
                    mode_factor = int(match.group(1)) / 100
            except (ValueError, AttributeError):
                pass

    base_roi = float(skeleton.avg_roi or 2.0)
    base_ctr = float(skeleton.avg_ctr or 1.5)

    if mode_factor is not None:
        factor = mode_factor
    else:
        factors = {
            "replace_leaf": 0.85,
            "replace_branch": 0.65,
            "replace_style": 0.70,
        }
        factor = factors.get(fission_mode, 0.7)

    return {
        "ctr_min": round(base_ctr * factor * 0.9, 2),
        "ctr_max": round(base_ctr * factor * 1.1, 2),
        "roi_min": round(base_roi * factor * 0.9, 2),
        "roi_max": round(base_roi * factor * 1.1, 2),
    }


@router.get("/")
def list_fissions(
    skeleton_id: Optional[int] = None,
    output_status: Optional[int] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    查询裂变记录列表，支持按骨架 ID、产出状态、平台、日期范围筛选。
    """
    try:
        query = db.query(Fission)

        if skeleton_id:
            query = query.filter(Fission.skeleton_id == skeleton_id)
        if output_status is not None:
            query = query.filter(Fission.output_status == output_status)
        if platform:
            query = query.filter(Fission.new_platform == platform)
        if start_date:
            query = query.filter(Fission.created_at >= start_date)
        if end_date:
            query = query.filter(Fission.created_at <= end_date + " 23:59:59")

        total = query.count()
        items = query.order_by(Fission.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        skeleton_ids = [item.skeleton_id for item in items]
        skeletons = {}
        if skeleton_ids:
            for s in db.query(Skeleton).filter(Skeleton.id.in_(skeleton_ids)).all():
                skeletons[s.id] = s

        result = []
        for item in items:
            sk = skeletons.get(item.skeleton_id)
            result.append({
                "id": item.id,
                "skeleton_id": item.skeleton_id,
                "skeleton_name": sk.name if sk else "未知骨架",
                "fission_mode": item.fission_mode,
                "new_topic": item.new_topic,
                "output_title": item.output_title,
                "output_content": item.output_content,
                "output_status": item.output_status,
                "predicted_ctr_min": float(item.predicted_ctr_min) if item.predicted_ctr_min else None,
                "predicted_ctr_max": float(item.predicted_ctr_max) if item.predicted_ctr_max else None,
                "predicted_roi_min": float(item.predicted_roi_min) if item.predicted_roi_min else None,
                "predicted_roi_max": float(item.predicted_roi_max) if item.predicted_roi_max else None,
                "actual_ctr": float(item.actual_ctr) if item.actual_ctr else None,
                "actual_roi": float(item.actual_roi) if item.actual_roi else None,
                "prediction_accuracy": float(item.prediction_accuracy) if item.prediction_accuracy else None,
                "created_at": item.created_at,
            })
        return success({"items": result, "total": total, "page": page, "page_size": page_size})
    except Exception as e:
        logger.error(f"List fissions failed: {e}", exc_info=True)
        return error(f"查询裂变记录失败: {str(e)}", 500)


@router.get("/stats")
def fission_stats(db: Session = Depends(get_db)):
    """裂变记录全局统计，返回各状态计数。"""
    try:
        from sqlalchemy import func, case

        stats = db.query(
            func.count(Fission.id).label("total"),
            func.sum(case((Fission.output_status == 0, 1), else_=0)).label("draft"),
            func.sum(case((Fission.output_status == 1, 1), else_=0)).label("pending"),
            func.sum(case((Fission.output_status == 2, 1), else_=0)).label("approved"),
            func.sum(case((Fission.output_status == 3, 1), else_=0)).label("deployed"),
            func.sum(case((Fission.actual_roi.isnot(None), 1), else_=0)).label("has_effect"),
        ).first()

        return success({
            "total": stats.total or 0,
            "draft": int(stats.draft or 0),
            "pending": int(stats.pending or 0),
            "approved": int(stats.approved or 0),
            "deployed": int(stats.deployed or 0),
            "has_effect": int(stats.has_effect or 0),
        })
    except Exception as e:
        logger.error(f"Get fission stats failed: {e}", exc_info=True)
        return error(f"查询统计失败: {str(e)}", 500)


@router.put("/{fission_id}/status")
def update_fission_status(fission_id: int, status: int, db: Session = Depends(get_db)):
    """
    更新裂变记录的状态，支持状态流转：0=草稿 → 1=待审核 → 2=已采用 → 3=已投放
    """
    try:
        item = db.query(Fission).filter(Fission.id == fission_id).first()
        if not item:
            return error("裂变记录不存在", 404)

        current = item.output_status

        if status not in (0, 1, 2, 3):
            return error("无效的状态值，必须为 0-3", 400)
        if status == current:
            return error("状态未变化", 400)
        if status < current:
            return error("状态不能回退", 400)
        if status - current != 1:
            return error("每次只能推进一个状态", 400)

        item.output_status = status
        db.commit()
        db.refresh(item)

        status_names = {0: "草稿", 1: "待审核", 2: "已采用", 3: "已投放"}
        log_operation(db, "fission", fission_id, "status_change", {"from": current, "to": status})
        return success({
            "id": item.id,
            "output_status": item.output_status,
            "message": f"状态已更新为「{status_names[status]}」",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"Update fission {fission_id} status failed: {e}", exc_info=True)
        return error(f"更新状态失败: {str(e)}", 500)


@router.delete("/{fission_id}")
def delete_fission(fission_id: int, db: Session = Depends(get_db)):
    """删除指定裂变记录。"""
    try:
        item = db.query(Fission).filter(Fission.id == fission_id).first()
        if not item:
            return error("裂变记录不存在", 404)
        db.delete(item)
        db.commit()
        log_operation(db, "fission", fission_id, "delete", {"title": item.output_title})
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete fission {fission_id} failed: {e}", exc_info=True)
        return error(f"删除失败: {str(e)}", 500)


@router.get("/{fission_id}")
def get_fission(fission_id: int, db: Session = Depends(get_db)):
    """查询单条裂变记录的详细信息。"""
    try:
        item = db.query(Fission).filter(Fission.id == fission_id).first()
        if not item:
            return error("裂变记录不存在", 404)

        skeleton = db.query(Skeleton).filter(Skeleton.id == item.skeleton_id).first()
        effects = db.query(EffectData).filter(EffectData.fission_id == item.id).all()

        return success({
            "id": item.id,
            "skeleton_id": item.skeleton_id,
            "skeleton_name": skeleton.name if skeleton else "未知骨架",
            "fission_mode": item.fission_mode,
            "new_topic": item.new_topic,
            "new_category": item.new_category,
            "new_platform": item.new_platform,
            "new_style": item.new_style,
            "output_title": item.output_title,
            "output_content": item.output_content,
            "output_status": item.output_status,
            "predicted_ctr_min": float(item.predicted_ctr_min) if item.predicted_ctr_min else None,
            "predicted_ctr_max": float(item.predicted_ctr_max) if item.predicted_ctr_max else None,
            "predicted_roi_min": float(item.predicted_roi_min) if item.predicted_roi_min else None,
            "predicted_roi_max": float(item.predicted_roi_max) if item.predicted_roi_max else None,
            "actual_ctr": float(item.actual_ctr) if item.actual_ctr else None,
            "actual_roi": float(item.actual_roi) if item.actual_roi else None,
            "prediction_accuracy": float(item.prediction_accuracy) if item.prediction_accuracy else None,
            "effects": [
                {
                    "id": e.id,
                    "platform": e.platform,
                    "impressions": e.impressions,
                    "clicks": e.clicks,
                    "ctr": float(e.ctr) if e.ctr else None,
                    "conversions": e.conversions,
                    "cvr": float(e.cvr) if e.cvr else None,
                    "cost": float(e.cost) if e.cost else None,
                    "revenue": float(e.revenue) if e.revenue else None,
                    "roi": float(e.roi) if e.roi else None,
                    "cpa": float(e.cpa) if e.cpa else None,
                    "stat_date": str(e.stat_date) if e.stat_date else None,
                }
                for e in effects
            ],
            "created_at": item.created_at,
        })
    except Exception as e:
        logger.error(f"Get fission {fission_id} failed: {e}", exc_info=True)
        return error(f"查询失败: {str(e)}", 500)


# ============================================================
# AI 裂变生成
# ============================================================

class AiFissionRequest(BaseModel):
    """AI 裂变请求参数模型"""
    skeleton_id: int
    fission_mode: str  # replace_leaf / replace_branch / replace_style
    new_topic: str
    new_category: Optional[str] = ""
    new_platform: Optional[str] = ""
    new_style: Optional[str] = ""
    replacement: Optional[dict] = None
    variant_count: int = 1  # 生成变体数量 1-5


@router.post("/ai-generate", status_code=201)
def ai_generate_fission(data: AiFissionRequest, db: Session = Depends(get_db)):
    """
    AI 裂变生成接口。

    根据骨架 L1-L5 结构化数据 + 新主题/品类/风格，调用 LongCat AI 端到端生成完整可投放文案。
    AI 不可用时自动降级为规则引擎（fission_engine.generate_output）。

    支持一次生成多个变体（variant_count），每个变体采用不同的表达风格。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == data.skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        if not data.new_topic:
            return error("新主题不能为空", 400)

        # 构建骨架数据字典
        skeleton_data = {
            "id": skeleton.id,
            "name": skeleton.name,
            "skeleton_type": skeleton.skeleton_type,
            "strategy_desc": skeleton.strategy_desc or "",
            "structure_json": skeleton.structure_json or [],
            "elements_json": skeleton.elements_json or {},
            "avg_roi": float(skeleton.avg_roi) if skeleton.avg_roi else None,
            "avg_ctr": float(skeleton.avg_ctr) if skeleton.avg_ctr else None,
            "platform": skeleton.platform or "",
        }

        # 解析 JSON 字段（SQLite 可能返回字符串）
        import json as _json
        if isinstance(skeleton_data["structure_json"], str):
            skeleton_data["structure_json"] = _json.loads(skeleton_data["structure_json"])
        if isinstance(skeleton_data["elements_json"], str):
            skeleton_data["elements_json"] = _json.loads(skeleton_data["elements_json"])

        # 调用 AI 裂变引擎
        from ..services.ai_fission import generate_fission
        results = generate_fission(
            skeleton=skeleton_data,
            fission_mode=data.fission_mode,
            new_topic=data.new_topic,
            new_category=data.new_category or "",
            new_platform=data.new_platform or "",
            new_style=data.new_style or "",
            replacement=data.replacement or {},
            variant_count=data.variant_count,
        )

        # 构建响应
        response_items = []
        for r in results:
            meta = r.get("_meta", {})
            response_items.append({
                "title": r.get("title", ""),
                "alt_titles": r.get("alt_titles", []),
                "content": r.get("content", ""),
                "hook": r.get("hook", ""),
                "golden_sentences": r.get("golden_sentences", []),
                "visual_notes": r.get("visual_notes", []),
                "tags": r.get("tags", []),
                "match_score": meta.get("match_score"),
                "match_reason": meta.get("match_reason", ""),
                "predicted_ctr_range": meta.get("predicted_ctr_range", ""),
                "predicted_roi_range": meta.get("predicted_roi_range", ""),
                "platform_tone": meta.get("platform_tone", ""),
                "is_ai": not meta.get("_fallback", False),
            })

        return created_response({
            "count": len(response_items),
            "items": response_items,
            "skeleton_id": data.skeleton_id,
            "fission_mode": data.fission_mode,
            "new_topic": data.new_topic,
        })
    except Exception as e:
        logger.error(f"AI fission generate failed: {e}", exc_info=True)
        return error(f"AI 裂变生成失败: {str(e)}", 500)
