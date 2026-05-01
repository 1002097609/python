from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from ..database import get_db
from ..models.skeleton import Skeleton

router = APIRouter()


def _skeleton_to_dict(s: Skeleton) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "skeleton_type": s.skeleton_type,
        "usage_count": s.usage_count,
        "avg_roi": float(s.avg_roi) if isinstance(s.avg_roi, Decimal) else s.avg_roi,
        "avg_ctr": float(s.avg_ctr) if isinstance(s.avg_ctr, Decimal) else s.avg_ctr,
        "created_at": s.created_at,
    }


@router.get("/")
def list_skeletons(
    platform: Optional[str] = Query(None),
    skeleton_type: Optional[str] = Query(None),
    sort_by: str = Query("usage_count", pattern="^(usage_count|avg_roi|avg_ctr|created_at)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Skeleton)
    if platform:
        query = query.filter(Skeleton.platform == platform)
    if skeleton_type:
        query = query.filter(Skeleton.skeleton_type == skeleton_type)

    sort_column = getattr(Skeleton, sort_by, Skeleton.usage_count)
    query = query.order_by(sort_column.desc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return [_skeleton_to_dict(i) for i in items]


@router.get("/{skeleton_id}")
def get_skeleton(skeleton_id: int, db: Session = Depends(get_db)):
    skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
    if not skeleton:
        raise HTTPException(status_code=404, detail="骨架不存在")
    return skeleton


@router.post("/from-dismantle/{dismantle_id}")
def create_skeleton_from_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    from ..models.dismantle import Dismantle
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")

    # 推断骨架类型
    skeleton_type = _infer_skeleton_type(dismantle.l3_structure)
    name = f"{skeleton_type} — {dismantle.l1_topic or '未命名'}"[:100]

    skeleton = Skeleton(
        name=name,
        skeleton_type=skeleton_type,
        source_material_id=dismantle.material_id,
        strategy_desc=dismantle.l2_emotion,
        structure_json=dismantle.l3_structure,
        elements_json=dismantle.l4_elements,
        style_tags=dismantle.l2_strategy,
    )
    db.add(skeleton)
    db.flush()

    # 更新拆解记录的骨架关联
    dismantle.skeleton_id = skeleton.id
    db.commit()
    db.refresh(skeleton)
    return {"skeleton_id": skeleton.id, "name": name, "message": "骨架提取成功"}


def _infer_skeleton_type(l3_structure) -> str:
    if not l3_structure:
        return "通用型"
    import json
    structure = json.loads(l3_structure) if isinstance(l3_structure, str) else l3_structure
    names = [s.get("name", "") for s in structure]
    names_str = ",".join(names)
    if "测评" in names_str or "对比" in names_str:
        return "测评对比型"
    if "红榜" in names_str or "黑榜" in names_str:
        return "红黑榜型"
    if "误区" in names_str:
        return "误区纠正型"
    if "步骤" in names_str:
        return "教程步骤型"
    return "通用型"
