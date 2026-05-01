"""
效果数据路由模块（routes/effect.py）。

提供投放效果数据的录入和查询接口，是系统效果闭环的核心环节。
当裂变素材的实际投放数据回写后，系统会自动更新关联骨架的平均效果统计
（avg_roi、avg_ctr），从而指导下一次的骨架选择和效果预测。

路由列表：
  POST /api/effect/       - 录入效果数据（支持关联裂变记录）
  GET  /api/effect/{id}   - 查询指定素材的所有效果数据
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.effect_data import EffectData
from ..models.fission import Fission
from ..models.skeleton import Skeleton

# 创建效果数据专用路由器，设置路由前缀和标签
router = APIRouter(prefix="/effect", tags=["效果数据"])


class EffectCreate(BaseModel):
    """
    效果数据创建模型，用于录入素材的投放效果数据。

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


@router.post("/")
def create_effect(data: EffectCreate, db: Session = Depends(get_db)):
    """
    录入素材的投放效果数据。

    核心逻辑：
      1. 将效果数据写入 effect_data 表
      2. 如果关联了 fission_id，则同时更新裂变记录的实际 ROI 和 CTR
      3. 触发骨架统计更新：重新计算关联骨架的 avg_roi 和 avg_ctr（效果闭环）

    请求参数：
        data (EffectCreate): 效果数据模型，所有字段均为可选（实际录入时按需填充）。

    返回值：
        dict: 包含 id（新录入记录 ID）和 message（操作结果描述）。
    """
    # 创建效果数据记录并写入数据库（exclude_unset=True 仅处理实际传入的字段）
    effect = EffectData(**data.model_dump(exclude_unset=True))
    db.add(effect)

    # 如果关联了裂变记录，同步更新裂变素材的实际效果指标
    if data.fission_id:
        fission = db.query(Fission).filter(Fission.id == data.fission_id).first()
        if fission:
            # 将实际投放效果回写到裂变记录
            fission.actual_roi = data.roi
            fission.actual_ctr = data.ctr
            # 触发骨架统计更新，重新计算该骨架关联的所有裂变素材的平均效果
            _update_skeleton_stats(db, fission.skeleton_id)

    db.commit()
    db.refresh(effect)
    return {"id": effect.id, "message": "效果数据录入成功"}


@router.get("/{material_id}")
def get_material_effects(material_id: int, db: Session = Depends(get_db)):
    """
    查询指定素材的所有效果数据记录。

    可用于前端展示素材的投放效果趋势分析。一个素材可能有多条效果数据记录
    （按日期或按投放计划分组）。

    请求参数：
        material_id (int): 要查询效果数据的素材 ID。

    返回值：
        list[EffectData]: 该素材的所有效果数据记录列表。
    """
    effects = db.query(EffectData).filter(EffectData.material_id == material_id).all()
    return effects


def _update_skeleton_stats(db, skeleton_id: int):
    """
    更新指定骨架的平均效果统计。

    通过关联裂变记录和效果数据表，计算该骨架所有已回写效果数据的平均 ROI 和 CTR，
    并将结果更新到骨架表中。这是系统的效果闭环关键逻辑：
    投放后回写 effect_data -> 更新 skeleton.avg_roi/avg_ctr -> 指导下次裂变效果预测。

    参数：
        db (Session):       数据库会话。
        skeleton_id (int):  要更新统计数据的骨架 ID。
    """
    from sqlalchemy import func

    # 通过 fission_id 关联 effect_data 和 fission 表，
    # 计算指定骨架所有已回写效果数据的平均值
    result = db.query(
        func.avg(EffectData.roi).label("avg_roi"),
        func.avg(EffectData.ctr).label("avg_ctr"),
    ).join(Fission, Fission.id == EffectData.fission_id
    ).filter(Fission.skeleton_id == skeleton_id, EffectData.roi.isnot(None)).first()

    # 仅在计算结果有效时更新骨架表
    if result and result.avg_roi:
        skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
        if skeleton:
            skeleton.avg_roi = result.avg_roi
            skeleton.avg_ctr = result.avg_ctr


@router.get("/fission/{fission_id}")
def get_fission_effects(fission_id: int, db: Session = Depends(get_db)):
    """
    查询指定裂变素材的所有效果数据记录。

    用于在裂变记录详情页展示该素材的投放效果趋势。
    一个裂变素材可能有多条效果数据记录（按日期分组）。

    请求参数：
        fission_id (int): 裂变记录 ID

    返回值:
        list[dict]: 效果数据列表，按统计日期升序排列
    """
    effects = (
        db.query(EffectData)
        .filter(EffectData.fission_id == fission_id)
        .order_by(EffectData.stat_date.asc())
        .all()
    )
    return [
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
    ]
