"""
骨架库路由模块（routes/skeleton.py）。

提供可复用骨架的查询、删除以及从拆解记录自动提取骨架的功能。
骨架是从拆解结果中提取的 L2-L4 层结构化数据，代表可跨品类复用的内容模板。
骨架附带效果统计（avg_roi、avg_ctr）和 usage_count，用于指导裂变时的骨架选择。

路由列表：
  GET    /api/skeleton/                      - 分页查询骨架列表（支持筛选和排序）
  GET    /api/skeleton/{id}                  - 查询单个骨架详情
  DELETE /api/skeleton/{id}                  - 删除骨架
  POST   /api/skeleton/from-dismantle/{id}   - 从拆解记录自动提取骨架
"""

import csv
import io
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from ..database import get_db
from ..models.skeleton import Skeleton
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

# 创建骨架库专用路由器
router = APIRouter()


def _skeleton_to_dict(s: Skeleton) -> dict:
    """
    将 Skeleton ORM 对象转换为普通字典，处理 Decimal 类型的序列化问题。
    """
    return {
        "id": s.id,
        "name": s.name,
        "skeleton_type": s.skeleton_type,
        "source_material_id": s.source_material_id,
        "strategy_desc": s.strategy_desc,
        "structure_json": s.structure_json,
        "elements_json": s.elements_json,
        "style_tags": s.style_tags,
        "usage_count": s.usage_count,
        "avg_roi": float(s.avg_roi) if isinstance(s.avg_roi, Decimal) else s.avg_roi,
        "avg_ctr": float(s.avg_ctr) if isinstance(s.avg_ctr, Decimal) else s.avg_ctr,
        "suitable_for": s.suitable_for,
        "platform": s.platform,
        "created_at": s.created_at,
    }


@router.get("/")
def list_skeletons(
    platform: Optional[str] = Query(None),
    skeleton_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="按名称/描述关键词搜索"),
    sort_by: str = Query("usage_count", pattern="^(usage_count|avg_roi|avg_ctr|created_at)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """
    分页查询骨架列表，支持按平台、骨架类型筛选，支持按使用次数/平均ROI/平均CTR/创建时间排序。
    """
    try:
        query = db.query(Skeleton)

        if platform:
            query = query.filter(Skeleton.platform == platform)
        if skeleton_type:
            query = query.filter(Skeleton.skeleton_type == skeleton_type)
        if keyword:
            query = query.filter(Skeleton.name.contains(keyword) | Skeleton.strategy_desc.contains(keyword))

        sort_column = getattr(Skeleton, sort_by, Skeleton.usage_count)
        query = query.order_by(sort_column.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return success({
            "items": [_skeleton_to_dict(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        logger.error(f"List skeletons failed: {e}", exc_info=True)
        return error(f"查询骨架列表失败: {str(e)}", 500)


@router.put("/{skeleton_id}")
def update_skeleton(skeleton_id: int, data: dict, db: Session = Depends(get_db)):
    """
    更新骨架信息。支持部分更新。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        for key, value in data.items():
            if hasattr(skeleton, key) and value is not None:
                setattr(skeleton, key, value)

        db.commit()
        db.refresh(skeleton)
        log_operation(db, "skeleton", skeleton.id, "update", {"changed_fields": list(data.keys())})
        return success(_skeleton_to_dict(skeleton))
    except Exception as e:
        db.rollback()
        logger.error(f"Update skeleton {skeleton_id} failed: {e}", exc_info=True)
        return error(f"更新骨架失败: {str(e)}", 500)


@router.get("/{skeleton_id}")
def get_skeleton(skeleton_id: int, db: Session = Depends(get_db)):
    """
    根据骨架 ID 查询单个骨架的详细信息。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)
        return success(_skeleton_to_dict(skeleton))
    except Exception as e:
        logger.error(f"Get skeleton {skeleton_id} failed: {e}", exc_info=True)
        return error(f"查询骨架失败: {str(e)}", 500)


@router.delete("/{skeleton_id}")
def delete_skeleton(skeleton_id: int, db: Session = Depends(get_db)):
    """
    删除指定的骨架记录。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        # 级联删除：先删关联的裂变记录和效果数据
        from ..models.fission import Fission
        from ..models.effect_data import EffectData

        fissions = db.query(Fission).filter(Fission.skeleton_id == skeleton_id).all()
        for ff in fissions:
            db.query(EffectData).filter(EffectData.fission_id == ff.id).delete()
        db.query(Fission).filter(Fission.skeleton_id == skeleton_id).delete()

        name = skeleton.name
        fissions_count = len(fissions)
        source_material_id = skeleton.source_material_id
        db.delete(skeleton)
        db.commit()
        log_operation(db, "skeleton", skeleton_id, "delete", {"name": name, "cascade_fissions": fissions_count})

        # 回退关联素材状态为"未拆解"，因为骨架已不存在
        if source_material_id:
            from ..models.material import Material
            material = db.query(Material).filter(Material.id == source_material_id).first()
            if material:
                material.status = 0

        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete skeleton {skeleton_id} failed: {e}", exc_info=True)
        return error(f"删除骨架失败: {str(e)}", 500)


@router.get("/{skeleton_id}/effects")
def get_skeleton_effects(skeleton_id: int, db: Session = Depends(get_db)):
    """
    聚合查询指定骨架所有裂变记录的效果数据。
    """
    try:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if not skeleton:
            return error("骨架不存在", 404)

        from ..models.fission import Fission
        from ..models.effect_data import EffectData
        from sqlalchemy import func

        fissions = db.query(Fission).filter(Fission.skeleton_id == skeleton_id).all()

        fission_ids = [f.id for f in fissions]
        effects = []
        if fission_ids:
            effects = db.query(EffectData).filter(EffectData.fission_id.in_(fission_ids)).all()

        effects_by_fission = {}
        for e in effects:
            effects_by_fission.setdefault(e.fission_id, []).append(e)

        fission_results = []
        all_effects_for_trend = []
        for f in fissions:
            eff_arr = effects_by_fission.get(f.id, [])
            summary = None
            if eff_arr:
                total_cost = sum(e.cost or 0 for e in eff_arr)
                total_revenue = sum(e.revenue or 0 for e in eff_arr)
                avg_roi = sum(e.roi or 0 for e in eff_arr) / len(eff_arr)
                avg_ctr = sum(e.ctr or 0 for e in eff_arr) / len(eff_arr)
                summary = {
                    "roi": round(float(avg_roi), 2),
                    "ctr": round(float(avg_ctr), 2),
                    "cost": round(float(total_cost), 2),
                    "revenue": round(float(total_revenue), 2),
                }
                all_effects_for_trend.extend(eff_arr)

            fission_results.append({
                "id": f.id,
                "fission_mode": f.fission_mode,
                "new_topic": f.new_topic,
                "new_category": f.new_category,
                "output_status": f.output_status,
                "predicted_ctr_min": float(f.predicted_ctr_min) if f.predicted_ctr_min else None,
                "predicted_ctr_max": float(f.predicted_ctr_max) if f.predicted_ctr_max else None,
                "predicted_roi_min": float(f.predicted_roi_min) if f.predicted_roi_min else None,
                "predicted_roi_max": float(f.predicted_roi_max) if f.predicted_roi_max else None,
                "prediction_accuracy": float(f.prediction_accuracy) if f.prediction_accuracy else None,
                "effect_summary": summary,
                "created_at": str(f.created_at) if f.created_at else None,
            })

        date_map = {}
        for e in all_effects_for_trend:
            d = str(e.stat_date) if e.stat_date else ""
            if not d:
                continue
            if d not in date_map:
                date_map[d] = {"rois": [], "ctrs": [], "costs": [], "revenues": []}
            if e.roi is not None:
                date_map[d]["rois"].append(float(e.roi))
            if e.ctr is not None:
                date_map[d]["ctrs"].append(float(e.ctr))
            if e.cost is not None:
                date_map[d]["costs"].append(float(e.cost))
            if e.revenue is not None:
                date_map[d]["revenues"].append(float(e.revenue))

        trend = []
        for d in sorted(date_map.keys()):
            entry = date_map[d]
            trend.append({
                "date": d,
                "avg_roi": round(sum(entry["rois"]) / len(entry["rois"]), 2) if entry["rois"] else None,
                "avg_ctr": round(sum(entry["ctrs"]) / len(entry["ctrs"]), 2) if entry["ctrs"] else None,
                "total_cost": round(sum(entry["costs"]), 2),
                "total_revenue": round(sum(entry["revenues"]), 2),
                "count": len(entry["rois"]),
            })

        return success({"trend": trend, "fissions": fission_results})
    except Exception as e:
        logger.error(f"Get skeleton effects {skeleton_id} failed: {e}", exc_info=True)
        return error(f"查询骨架效果数据失败: {str(e)}", 500)


@router.post("/from-dismantle/{dismantle_id}", status_code=201)
def create_skeleton_from_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    """
    从已有的拆解记录中自动提取骨架并存入骨架库。
    """
    try:
        from ..models.dismantle import Dismantle

        dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
        if not dismantle:
            return error("拆解记录不存在", 404)

        # 幂等检查
        if dismantle.skeleton_id:
            existing = db.query(Skeleton).filter(Skeleton.id == dismantle.skeleton_id).first()
            if existing:
                return success({"skeleton_id": existing.id, "name": existing.name, "message": "该拆解记录已提取过骨架，返回已有骨架"})

        skeleton_type = _infer_skeleton_type(dismantle.l3_structure)
        name = f"{skeleton_type} — {dismantle.l1_topic or '未命名'}"[:100]

        from ..models.material import Material
        material = db.query(Material).filter(Material.id == dismantle.material_id).first()
        platform = material.platform if material else None

        style_tags = _extract_style_tags(dismantle.l4_elements)

        skeleton = Skeleton(
            name=name,
            skeleton_type=skeleton_type,
            source_material_id=dismantle.material_id,
            strategy_desc=dismantle.l2_emotion,
            structure_json=dismantle.l3_structure,
            elements_json=dismantle.l4_elements,
            style_tags=style_tags,
            platform=platform,
        )
        db.add(skeleton)
        db.flush()

        dismantle.skeleton_id = skeleton.id

        db.commit()
        db.refresh(skeleton)
        log_operation(db, "skeleton", skeleton.id, "create", {"name": name, "skeleton_type": skeleton_type, "source_dismantle_id": dismantle_id})
        return created_response(_skeleton_to_dict(skeleton))
    except Exception as e:
        db.rollback()
        logger.error(f"Create skeleton from dismantle {dismantle_id} failed: {e}", exc_info=True)
        return error(f"提取骨架失败: {str(e)}", 500)


def _infer_skeleton_type(l3_structure) -> str:
    """根据 L3 内容结构中的段落名称自动推断骨架类型。"""
    if not l3_structure:
        return "通用型"

    import json
    structure = json.loads(l3_structure) if isinstance(l3_structure, str) else l3_structure
    names = [s.get("name", "") for s in structure]
    names_str = ",".join(names)

    scores = {
        "测评对比型": sum(1 for kw in ("测评", "对比", "横评", "实测", "亲测") if kw in names_str),
        "红黑榜型":  sum(1 for kw in ("红榜", "黑榜", "榜单", "推荐", "排行") if kw in names_str),
        "误区纠正型": sum(1 for kw in ("误区", "避坑", "踩雷", "注意", "千万别") if kw in names_str),
        "教程步骤型": sum(1 for kw in ("步骤", "教程", "方法", "做法", "流程", "攻略") if kw in names_str),
        "故事叙事型": sum(1 for kw in ("故事", "经历", "分享", "日记", "记录") if kw in names_str),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "通用型"


def _extract_style_tags(l4_elements) -> list:
    """从 L4 元素层数据中提取风格标签。"""
    if not l4_elements:
        return []

    import json
    elements = json.loads(l4_elements) if isinstance(l4_elements, str) else l4_elements
    if not isinstance(elements, dict):
        return []

    tags = []
    for key in ("hook", "title_formula", "transition", "interaction"):
        val = elements.get(key, "")
        if val and isinstance(val, str) and len(val) >= 2:
            tags.append(val)
    return tags


# ============================================================
# 骨架自动推荐
# ============================================================

from pydantic import BaseModel
from typing import Optional


class SkeletonRecommendRequest(BaseModel):
    """骨架推荐请求模型 — 传入拆解记录的 L1-L5 数据"""
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None
    l3_structure: Optional[list] = None
    l4_elements: Optional[dict] = None
    category: Optional[str] = None
    platform: Optional[str] = None
    limit: int = 5


@router.post("/recommend")
def recommend_skeletons(data: SkeletonRecommendRequest, db: Session = Depends(get_db)):
    """
    骨架自动推荐接口。

    根据传入的拆解数据（L1-L5），从骨架库中匹配最适合用于裂变的骨架。

    匹配算法：
      1. L2 策略标签匹配（权重 35%）— 策略标签重合度
      2. L3 结构类型匹配（权重 30%）— 骨架类型 + 段落结构相似度
      3. 品类匹配（权重 15%）— 同品类优先
      4. 平台匹配（权重 10%）— 同平台优先
      5. 效果加成（权重 10%）— avg_roi / avg_ctr 历史效果

    返回 Top N 推荐骨架 + 匹配分数 + 匹配原因。
    """
    try:
        # 解析拆解数据
        dismantle_strategies = set(s.strip() for s in (data.l2_strategy or []) if s and s.strip())
        dismantle_emotion = (data.l2_emotion or "").strip()
        dismantle_category = (data.category or "").strip()
        dismantle_platform = (data.platform or "").strip()
        dismantle_topic = (data.l1_topic or "").strip()

        # 解析 L3 结构类型
        l3_structure = data.l3_structure or []
        if isinstance(l3_structure, str):
            import json
            l3_structure = json.loads(l3_structure)
        section_names = [s.get("name", "") for s in l3_structure if isinstance(s, dict)]
        inferred_type = _infer_skeleton_type(l3_structure)

        # 获取候选骨架（同平台或同品类优先，但不过滤太严）
        query = db.query(Skeleton)
        all_skeletons = query.all()

        if not all_skeletons:
            return success({"items": [], "total": 0, "message": "骨架库为空，请先提取骨架"})

        # 对每个骨架计算匹配分数
        scored = []
        for sk in all_skeletons:
            score = 0.0
            reasons = []

            # --- 1. L2 策略标签匹配（35%）---
            sk_strategies = set()
            if sk.strategy_desc:
                # 从策略描述中提取关键词
                for s in dismantle_strategies:
                    if s in sk.strategy_desc:
                        sk_strategies.add(s)
                # 反向：骨架描述中的关键词出现在拆解情绪中
                if dismantle_emotion and sk.strategy_desc:
                    for kw in dismantle_emotion:
                        if kw in sk.strategy_desc and len(kw) > 1:
                            sk_strategies.add(kw)

            if dismantle_strategies:
                overlap = len(sk_strategies & dismantle_strategies)
                strategy_score = min(overlap / max(len(dismantle_strategies), 1), 1.0) * 35
                score += strategy_score
                if overlap > 0:
                    reasons.append(f"策略标签匹配 {overlap} 个")

            # --- 2. L3 结构类型匹配（30%）---
            if sk.skeleton_type and inferred_type:
                if sk.skeleton_type == inferred_type:
                    score += 30
                    reasons.append(f"结构类型一致：{sk.skeleton_type}")
                elif sk.skeleton_type in ("通用型",) or inferred_type in ("通用型",):
                    score += 10
                    reasons.append("通用型骨架，适配性广")

            # 段落名称相似度（Jaccard）
            if section_names and sk.structure_json:
                sk_sections = sk.structure_json
                if isinstance(sk_sections, str):
                    import json as _json
                    sk_sections = _json.loads(sk_sections)
                sk_names = set(s.get("name", "") for s in sk_sections if isinstance(s, dict))
                if sk_names and section_names:
                    input_names = set(section_names)
                    intersection = len(sk_names & input_names)
                    union = len(sk_names | input_names)
                    if union > 0:
                        jaccard = intersection / union
                        struct_score = jaccard * 15  # 额外最多 15 分
                        score += struct_score
                        if jaccard > 0.3:
                            reasons.append(f"段落结构相似度 {jaccard:.0%}")

            # --- 3. 品类匹配（15%）---
            if dismantle_category and sk.suitable_for:
                suitable = sk.suitable_for
                if isinstance(suitable, str):
                    suitable = [suitable]
                if dismantle_category in suitable:
                    score += 15
                    reasons.append(f"品类匹配：{dismantle_category}")
                # 部分匹配
                elif any(dismune_category in str(s) for s in suitable):
                    score += 8
                    reasons.append(f"品类部分匹配")

            # --- 4. 平台匹配（10%）---
            if dismantle_platform and sk.platform:
                if sk.platform == dismantle_platform:
                    score += 10
                    reasons.append(f"平台匹配：{dismantle_platform}")
                elif sk.platform == "通用":
                    score += 3

            # --- 5. 效果加成（10%）---
            roi = float(sk.avg_roi) if sk.avg_roi else 0
            ctr = float(sk.avg_ctr) if sk.avg_ctr else 0
            usage = sk.usage_count or 0

            if roi > 0 or ctr > 0:
                # ROI 归一化到 0-7 分（假设 ROI 5x 为满分）
                roi_score = min(roi / 5.0, 1.0) * 7
                # CTR 归一化到 0-3 分（假设 CTR 5% 为满分）
                ctr_score = min(ctr / 5.0, 1.0) * 3
                effect_score = roi_score + ctr_score
                score += effect_score
                if roi > 2.0:
                    reasons.append(f"历史 ROI {roi:.1f}x")
                if ctr > 1.5:
                    reasons.append(f"历史 CTR {ctr:.1f}%")

            # 使用次数加成（经验验证）
            if usage > 0:
                usage_bonus = min(usage / 10.0, 1.0) * 3  # 最多 3 分
                score += usage_bonus
                if usage >= 5:
                    reasons.append(f"已验证 {usage} 次")

            scored.append((score, reasons, sk))

        # 排序取 Top N
        scored.sort(key=lambda x: x[0], reverse=True)
        limit = min(max(data.limit, 1), 10)

        results = []
        for score, reasons, sk in scored[:limit]:
            sk_dict = _skeleton_to_dict(sk)
            sk_dict["match_score"] = round(score, 1)
            sk_dict["match_reasons"] = reasons
            sk_dict["match_level"] = (
                "high" if score >= 60 else
                "medium" if score >= 35 else
                "low"
            )
            results.append(sk_dict)

        return success({
            "items": results,
            "total": len(results),
            "query_analysis": {
                "inferred_type": inferred_type,
                "input_strategies": list(dismantle_strategies),
                "input_category": dismantle_category,
                "input_platform": dismantle_platform,
            },
        })
    except Exception as e:
        logger.error(f"Recommend skeletons failed: {e}", exc_info=True)
        return error(f"骨架推荐失败: {str(e)}", 500)
        if val:
            tags.append(val)
    return tags


@router.post("/import")
def import_skeletons(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """批量导入骨架（JSON 格式）。"""
    try:
        content = file.file.read().decode("utf-8")
        items = json.loads(content)
        if not isinstance(items, list):
            return error("JSON 格式错误：根节点必须是数组", 400)

        inserted = 0
        skipped = 0
        for item in items:
            name = item.get("name", "").strip()
            if not name:
                skipped += 1
                continue
            existing = db.query(Skeleton).filter(Skeleton.name == name).first()
            if existing:
                skipped += 1
                continue
            db.add(Skeleton(
                name=name,
                skeleton_type=item.get("skeleton_type"),
                strategy_desc=item.get("strategy_desc"),
                structure_json=item.get("structure_json"),
                elements_json=item.get("elements_json"),
                style_tags=item.get("style_tags"),
                platform=item.get("platform"),
            ))
            inserted += 1
        db.commit()
        log_operation(db, "skeleton", 0, "import", {"inserted": inserted, "skipped": skipped})
        return success({"inserted": inserted, "skipped": skipped, "message": f"导入完成：新增 {inserted} 条，跳过 {skipped} 条"})
    except json.JSONDecodeError:
        return error("JSON 格式无效", 400)
    except Exception as e:
        db.rollback()
        logger.error(f"Import skeletons failed: {e}", exc_info=True)
        return error(f"导入失败: {str(e)}", 500)


@router.get("/export")
def export_skeletons(
    format: str = Query("json", pattern="^(json|csv)$"),
    platform: Optional[str] = Query(None),
    skeleton_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """导出骨架数据，支持 JSON 和 CSV 格式。"""
    try:
        query = db.query(Skeleton)
        if platform:
            query = query.filter(Skeleton.platform == platform)
        if skeleton_type:
            query = query.filter(Skeleton.skeleton_type == skeleton_type)

        items = query.order_by(Skeleton.id).all()
        rows = []
        for i in items:
            rows.append({
                "id": i.id,
                "name": i.name,
                "skeleton_type": i.skeleton_type,
                "strategy_desc": i.strategy_desc,
                "structure_json": json.dumps(i.structure_json, ensure_ascii=False) if i.structure_json else "",
                "elements_json": json.dumps(i.elements_json, ensure_ascii=False) if i.elements_json else "",
                "style_tags": json.dumps(i.style_tags, ensure_ascii=False) if i.style_tags else "",
                "platform": i.platform,
                "usage_count": i.usage_count,
                "avg_roi": float(i.avg_roi) if i.avg_roi else None,
                "avg_ctr": float(i.avg_ctr) if i.avg_ctr else None,
            })

        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        log_operation(db, "skeleton", 0, "export", {"format": format, "count": len(rows)})

        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else ["id"])
            writer.writeheader()
            writer.writerows(rows)
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode("utf-8-sig")),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename=skeletons_{timestamp}.csv"},
            )

        return StreamingResponse(
            io.BytesIO(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=skeletons_{timestamp}.json"},
        )
    except Exception as e:
        logger.error(f"Export skeletons failed: {e}", exc_info=True)
        return error(f"导出失败: {str(e)}", 500)
