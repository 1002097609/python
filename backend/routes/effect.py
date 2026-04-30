from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.effect_data import EffectData
from ..models.fission import Fission
from ..models.skeleton import Skeleton

router = APIRouter(prefix="/effect", tags=["效果数据"])


class EffectCreate(BaseModel):
    material_id: Optional[int] = None
    fission_id: Optional[int] = None
    platform: Optional[str] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = None
    conversions: Optional[int] = None
    cvr: Optional[float] = None
    cost: Optional[float] = None
    revenue: Optional[float] = None
    roi: Optional[float] = None
    cpa: Optional[float] = None
    stat_date: Optional[date] = None


@router.post("/")
def create_effect(data: EffectCreate, db: Session = Depends(get_db)):
    effect = EffectData(**data.model_dump(exclude_unset=True))
    db.add(effect)

    # 如果是裂变素材的效果数据，更新裂变记录和骨架统计
    if data.fission_id:
        fission = db.query(Fission).filter(Fission.id == data.fission_id).first()
        if fission:
            fission.actual_roi = data.roi
            fission.actual_ctr = data.ctr
            # 更新骨架统计
            _update_skeleton_stats(db, fission.skeleton_id)

    db.commit()
    db.refresh(effect)
    return {"id": effect.id, "message": "效果数据录入成功"}


@router.get("/{material_id}")
def get_material_effects(material_id: int, db: Session = Depends(get_db)):
    effects = db.query(EffectData).filter(EffectData.material_id == material_id).all()
    return effects


def _update_skeleton_stats(db, skeleton_id: int):
    """更新骨架的平均效果统计"""
    from sqlalchemy import func
    result = db.query(
        func.avg(EffectData.roi).label("avg_roi"),
        func.avg(EffectData.ctr).label("avg_ctr"),
    ).join(Fission, Fission.id == EffectData.fission_id
    ).filter(Fission.skeleton_id == skeleton_id, EffectData.roi.isnot(None)).first()

    if result and result.avg_roi:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if skeleton:
            skeleton.avg_roi = result.avg_roi
            skeleton.avg_ctr = result.avg_ctr
