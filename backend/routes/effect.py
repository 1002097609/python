"""
效果数据路由模块（routes/effect.py）。

提供投放效果数据的录入、查询、编辑和删除接口，是系统效果闭环的核心环节。
当裂变素材的实际投放数据回写后，系统会自动更新关联骨架的平均效果统计
（avg_roi、avg_ctr），从而指导下一次的骨架选择和效果预测。

路由列表：
  POST   /api/effect/              - 录入效果数据（支持关联裂变记录）
  GET    /api/effect/fission/{id}   - 查询指定裂变记录的所有效果数据
  GET    /api/effect/{id}           - 查询指定素材的所有效果数据
  PUT    /api/effect/{id}           - 编辑效果数据
  DELETE /api/effect/{id}           - 删除效果数据
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.effect_data import EffectData
from ..models.fission import Fission
from ..models.skeleton import Skeleton
from ..services.operation_log import log_operation

# 创建效果数据专用路由器，设置路由前缀和标签
router = APIRouter(tags=["效果数据"])


class EffectCreate(BaseModel):
    """
    效果数据创建/更新模型，用于录入素材的投放效果数据。

    字段说明：
        material_id (int):   素材 ID，标识效果数据归属的原始素材。
        fission_id (int):   裂变 ID，若效果数据来自裂变素材则填写，触发骨架统计更新。
        platform (str):     投放平台，如 "抖音"、"快手"。
        impressions (int):  曝光量，素材被展示的总次数。
        clicks (int):       点击量，用户点击素材的总次数。
        ctr (float):        点击率（Click-Through Rate），点击/曝光的百分比。
        conversions (int):  转化量，完成目标行为（如购买）的次数。
        cvr (float):        转化率（Conversion Rate），转化/点击的百分比。
        cost (float):       投放花费（元）。
        revenue (float):    投放带来的收入（元）。
        roi (float):        投资回报率，收入/花费的比值。
        cpa (float):        单次转化成本，花费/转化的比值。
        stat_date (date):   数据统计日期，格式 YYYY-MM-DD。

    自动推导规则（传入原始数据时自动计算衍生指标）：
        ctr:    clicks / impressions * 100
        cvr:    conversions / clicks * 100
        roi:    revenue / cost
        cpa:    cost / conversions
    """
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


def _auto_calculate(data: dict) -> dict:
    """
    根据原始数据自动推导衍生指标。

    传入 impressions/clicks/conversions/cost/revenue 时，
    自动计算 ctr/cvr/roi/cpa，减少手动填写工作量。
    """
    imp = data.get("impressions")
    clk = data.get("clicks")
    conv = data.get("conversions")
    cost = data.get("cost")
    rev = data.get("revenue")

    if imp and clk and imp > 0 and not data.get("ctr"):
        data["ctr"] = round(clk / imp * 100, 2)
    if clk and conv and clk > 0 and not data.get("cvr"):
        data["cvr"] = round(conv / clk * 100, 2)
    if cost is not None and rev is not None and cost > 0 and not data.get("roi"):
        data["roi"] = round(rev / cost, 2)
    if cost is not None and conv is not None and conv > 0 and not data.get("cpa"):
        data["cpa"] = round(cost / conv, 2)

    return data


def _update_skeleton_stats(db, skeleton_id: int):
    """
    更新指定骨架的效果统计（按展示量加权平均）。

    加权算法：
      - avg_roi = SUM(revenue) / SUM(cost)  （整体投入产出比）
      - avg_ctr = SUM(clicks) / SUM(impressions) * 100  （整体点击率）
    相比简单 AVG，加权平均更能反映真实投放效果，避免小样本数据扭曲统计。

    效果闭环：投放回写 effect_data -> 更新 skeleton.avg_roi/avg_ctr -> 指导下次裂变选骨架。
    """
    from sqlalchemy import func, case

    result = db.query(
        func.sum(EffectData.revenue).label("total_revenue"),
        func.sum(EffectData.cost).label("total_cost"),
        func.sum(EffectData.clicks).label("total_clicks"),
        func.sum(EffectData.impressions).label("total_impressions"),
    ).join(Fission, Fission.id == EffectData.fission_id
    ).filter(Fission.skeleton_id == skeleton_id).first()

    skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
    if not skeleton:
        return

    total_cost = result.total_cost or 0
    total_revenue = result.total_revenue or 0
    total_clicks = result.total_clicks or 0
    total_impressions = result.total_impressions or 0

    if total_cost > 0:
        skeleton.avg_roi = total_revenue / total_cost
    else:
        skeleton.avg_roi = None

    if total_impressions > 0:
        skeleton.avg_ctr = total_clicks / total_impressions * 100
    else:
        skeleton.avg_ctr = None


def _update_fission_actual(db, fission_id: int):
    """
    更新裂变记录的实际效果指标。
    取该裂变记录最新的效果数据（按日期倒序）更新 actual_roi 和 actual_ctr。
    """
    from sqlalchemy import desc
    fission = db.query(Fission).filter(Fission.id == fission_id).first()
    if not fission:
        return
    latest = (
        db.query(EffectData)
        .filter(EffectData.fission_id == fission_id, EffectData.roi.isnot(None))
        .order_by(desc(EffectData.stat_date))
        .first()
    )
    if latest:
        fission.actual_roi = latest.roi
        fission.actual_ctr = latest.ctr
    else:
        fission.actual_roi = None
        fission.actual_ctr = None


def _effect_to_dict(e: EffectData) -> dict:
    """将 EffectData ORM 对象转换为可序列化的字典。"""
    return {
        "id": e.id,
        "material_id": e.material_id,
        "fission_id": e.fission_id,
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
        "created_at": str(e.created_at) if e.created_at else None,
    }


# ============================================================
# 路由：注意路由顺序，具体路径在前，参数路径在后
# ============================================================


@router.post("/")
def create_effect(data: EffectCreate, db: Session = Depends(get_db)):
    """
    录入素材的投放效果数据。

    核心逻辑：
      1. 自动推导衍生指标（CTR/CVR/ROI/CPA）
      2. 将效果数据写入 effect_data 表
      3. 如果关联了 fission_id，同步更新裂变记录的实际 ROI 和 CTR
      4. 触发骨架统计更新（效果闭环）
    """
    if not data.fission_id and not data.material_id:
        raise HTTPException(status_code=400, detail="fission_id 和 material_id 至少需要传入一个")

    raw = data.model_dump(exclude_unset=True)
    raw = _auto_calculate(raw)
    effect = EffectData(**raw)
    db.add(effect)

    if data.fission_id:
        _update_fission_actual(db, data.fission_id)
        fission = db.query(Fission).filter(Fission.id == data.fission_id).first()
        if fission:
            _update_skeleton_stats(db, fission.skeleton_id)

    db.commit()
    db.refresh(effect)
    log_operation(db, "effect_data", effect.id, "create", {"fission_id": data.fission_id, "roi": raw.get("roi")})
    return _effect_to_dict(effect)


@router.get("/fission/{fission_id}")
def get_fission_effects(fission_id: int, db: Session = Depends(get_db)):
    """
    查询指定裂变素材的所有效果数据记录（按日期升序）。
    注意：此路由必须注册在 /{id} 之前。
    """
    effects = (
        db.query(EffectData)
        .filter(EffectData.fission_id == fission_id)
        .order_by(EffectData.stat_date.asc())
        .all()
    )
    return [_effect_to_dict(e) for e in effects]


@router.get("/{effect_id}")
def get_effect(effect_id: int, db: Session = Depends(get_db)):
    """查询单条效果数据详情。"""
    effect = db.query(EffectData).filter(EffectData.id == effect_id).first()
    if not effect:
        raise HTTPException(status_code=404, detail="效果数据不存在")
    return _effect_to_dict(effect)


@router.put("/{effect_id}")
def update_effect(effect_id: int, data: EffectCreate, db: Session = Depends(get_db)):
    """
    编辑效果数据。支持部分更新，自动重新推导衍生指标。
    编辑后同步更新裂变记录实际效果和骨架统计。
    """
    effect = db.query(EffectData).filter(EffectData.id == effect_id).first()
    if not effect:
        raise HTTPException(status_code=404, detail="效果数据不存在")

    raw = data.model_dump(exclude_unset=True)
    # 合并现有数据与新数据，重新计算衍生指标
    merged = {
        "impressions": raw.get("impressions", effect.impressions),
        "clicks": raw.get("clicks", effect.clicks),
        "conversions": raw.get("conversions", effect.conversions),
        "cost": raw.get("cost", float(effect.cost) if effect.cost else None),
        "revenue": raw.get("revenue", float(effect.revenue) if effect.revenue else None),
        "ctr": raw.get("ctr", float(effect.ctr) if effect.ctr else None),
        "cvr": raw.get("cvr", float(effect.cvr) if effect.cvr else None),
        "roi": raw.get("roi", float(effect.roi) if effect.roi else None),
        "cpa": raw.get("cpa", float(effect.cpa) if effect.cpa else None),
    }
    merged = _auto_calculate(merged)

    for key, value in raw.items():
        setattr(effect, key, value)
    # 覆盖计算后的衍生指标
    for key in ("ctr", "cvr", "roi", "cpa"):
        if merged.get(key) is not None:
            setattr(effect, key, merged[key])

    # 同步更新裂变记录和骨架统计
    if effect.fission_id:
        _update_fission_actual(db, effect.fission_id)
        fission = db.query(Fission).filter(Fission.id == effect.fission_id).first()
        if fission:
            _update_skeleton_stats(db, fission.skeleton_id)

    db.commit()
    db.refresh(effect)
    log_operation(db, "effect_data", effect.id, "update", {"roi": merged.get("roi")})
    return _effect_to_dict(effect)


@router.delete("/{effect_id}")
def delete_effect(effect_id: int, db: Session = Depends(get_db)):
    """
    删除效果数据。
    删除后同步更新裂变记录实际效果和骨架统计。
    """
    effect = db.query(EffectData).filter(EffectData.id == effect_id).first()
    if not effect:
        raise HTTPException(status_code=404, detail="效果数据不存在")

    fission_id = effect.fission_id
    skeleton_id = None
    if fission_id:
        fission = db.query(Fission).filter(Fission.id == fission_id).first()
        if fission:
            skeleton_id = fission.skeleton_id

    db.delete(effect)
    db.commit()

    # 同步更新
    if fission_id:
        _update_fission_actual(db, fission_id)
        if skeleton_id:
            _update_skeleton_stats(db, skeleton_id)

    log_operation(db, "effect_data", effect_id, "delete", {"fission_id": fission_id})
    return {"message": "效果数据已删除"}
