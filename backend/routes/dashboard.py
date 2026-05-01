"""
数据统计仪表盘路由模块（routes/dashboard.py）。

提供系统整体运营数据的聚合统计接口，用于前端仪表盘页面展示。
涵盖：概览指标、品类分布、骨架效果排行、裂变漏斗、效果趋势。

路由列表：
  GET /api/dashboard/overview   - 概览指标（素材/骨架/裂变/效果数据总数）
  GET /api/dashboard/category   - 品类分布统计
  GET /api/dashboard/skeleton   - 骨架效果排行 TOP10
  GET /api/dashboard/fission    - 裂变状态漏斗统计
  GET /api/dashboard/trend      - 效果数据趋势（近30天）
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal_column
from datetime import date, timedelta
from ..database import get_db
from ..models.material import Material
from ..models.skeleton import Skeleton
from ..models.fission import Fission
from ..models.effect_data import EffectData

router = APIRouter(prefix="/dashboard", tags=["数据统计"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """
    概览指标：返回系统中核心实体的总数统计。

    返回值：
        dict: 包含以下字段：
            - material_count:   素材总数
            - material_pending: 未拆解素材数
            - material_done:    已拆解素材数
            - skeleton_count:   骨架总数
            - fission_count:    裂变总数
            - fission_draft:    草稿状态裂变数
            - fission_active:   已投放裂变数
            - effect_count:     效果数据记录数
            - total_cost:       累计投放花费
            - total_revenue:    累计投放收入
            - avg_roi:          平均 ROI
    """
    # 素材统计
    material_count = db.query(func.count(Material.id)).scalar()
    material_pending = db.query(func.count(Material.id)).filter(Material.status == 0).scalar()
    material_done = db.query(func.count(Material.id)).filter(Material.status >= 1).scalar()

    # 骨架统计
    skeleton_count = db.query(func.count(Skeleton.id)).scalar()

    # 裂变统计
    fission_count = db.query(func.count(Fission.id)).scalar()
    fission_draft = db.query(func.count(Fission.id)).filter(Fission.output_status == 0).scalar()
    fission_active = db.query(func.count(Fission.id)).filter(Fission.output_status == 3).scalar()

    # 效果数据统计
    effect_count = db.query(func.count(EffectData.id)).scalar()
    cost_revenue = db.query(
        func.sum(EffectData.cost).label("total_cost"),
        func.sum(EffectData.revenue).label("total_revenue"),
        func.avg(EffectData.roi).label("avg_roi"),
    ).first()

    return {
        "material": {
            "total": material_count,
            "pending": material_pending,
            "done": material_done,
        },
        "skeleton": {
            "total": skeleton_count,
        },
        "fission": {
            "total": fission_count,
            "draft": fission_draft,
            "active": fission_active,
        },
        "effect": {
            "count": effect_count,
            "total_cost": float(cost_revenue.total_cost or 0),
            "total_revenue": float(cost_revenue.total_revenue or 0),
            "avg_roi": float(cost_revenue.avg_roi or 0),
        },
    }


@router.get("/category")
def category_distribution(db: Session = Depends(get_db)):
    """
    品类分布统计：按品类分组统计各品类的素材数量和平均拆解状态。

    返回值:
        list[dict]: 品类列表，每项包含：
            - category:     品类名称
            - count:        素材数量
            - dismantled:   已拆解数量
    """
    rows = (
        db.query(
            Material.category.label("category"),
            func.count(Material.id).label("count"),
            func.sum(case((Material.status >= 1, 1), else_=0)).label("dismantled"),
        )
        .filter(Material.category.isnot(None))
        .group_by(Material.category)
        .order_by(func.count(Material.id).desc())
        .all()
    )
    return [
        {
            "category": r.category,
            "count": r.count,
            "dismantled": int(r.dismantled or 0),
        }
        for r in rows
    ]


@router.get("/skeleton")
def skeleton_ranking(
    sort_by: str = Query("avg_roi", pattern="^(avg_roi|avg_ctr|usage_count)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    骨架效果排行榜：按指定指标排序，返回 TOP N 骨架。

    请求参数：
        sort_by (str): 排序字段，avg_roi / avg_ctr / usage_count，默认 avg_roi
        limit (int):   返回条数，默认 10

    返回值:
        list[dict]: 骨架排行列表
    """
    sort_column = {
        "avg_roi": Skeleton.avg_roi,
        "avg_ctr": Skeleton.avg_ctr,
        "usage_count": Skeleton.usage_count,
    }.get(sort_by, Skeleton.avg_roi)

    rows = (
        db.query(Skeleton)
        .filter(sort_column.isnot(None))
        .order_by(sort_column.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "name": s.name,
            "skeleton_type": s.skeleton_type,
            "usage_count": s.usage_count,
            "avg_roi": float(s.avg_roi) if s.avg_roi else None,
            "avg_ctr": float(s.avg_ctr) if s.avg_ctr else None,
            "platform": s.platform,
        }
        for s in rows
    ]


@router.get("/fission")
def fission_funnel(db: Session = Depends(get_db)):
    """
    裂变状态漏斗统计：统计各状态的裂变数量。

    返回值:
        list[dict]: 状态列表，每项包含：
            - status:   状态码 (0-3)
            - label:    状态标签
            - count:    数量
    """
    status_map = {
        0: "草稿",
        1: "待审核",
        2: "已采用",
        3: "已投放",
    }
    rows = (
        db.query(
            Fission.output_status.label("status"),
            func.count(Fission.id).label("count"),
        )
        .group_by(Fission.output_status)
        .order_by(Fission.output_status)
        .all()
    )
    return [
        {
            "status": r.status,
            "label": status_map.get(r.status, f"状态{r.status}"),
            "count": r.count,
        }
        for r in rows
    ]


@router.get("/trend")
def effect_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """
    效果数据趋势：按日期聚合最近 N 天的效果数据。

    请求参数：
        days (int): 查询天数范围，默认 30

    返回值:
        list[dict]: 每日效果数据列表，每项包含：
            - date:         日期字符串
            - avg_ctr:       平均 CTR
            - avg_roi:       平均 ROI
            - total_cost:    总花费
            - total_revenue: 总收入
            - count:         数据记录数
    """
    start_date = date.today() - timedelta(days=days)
    rows = (
        db.query(
            EffectData.stat_date.label("date"),
            func.avg(EffectData.ctr).label("avg_ctr"),
            func.avg(EffectData.roi).label("avg_roi"),
            func.sum(EffectData.cost).label("total_cost"),
            func.sum(EffectData.revenue).label("total_revenue"),
            func.count(EffectData.id).label("count"),
        )
        .filter(EffectData.stat_date >= start_date)
        .group_by(EffectData.stat_date)
        .order_by(EffectData.stat_date)
        .all()
    )
    return [
        {
            "date": str(r.date),
            "avg_ctr": float(r.avg_ctr) if r.avg_ctr else None,
            "avg_roi": float(r.avg_roi) if r.avg_roi else None,
            "total_cost": float(r.total_cost) if r.total_cost else 0,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0,
            "count": r.count,
        }
        for r in rows
    ]
