"""
数据统计仪表盘路由模块（routes/dashboard.py）。

提供系统整体运营数据的聚合统计接口，用于前端仪表盘页面展示。
涵盖：概览指标、品类分布、骨架效果排行、裂变漏斗、效果趋势。

路由列表：
  GET /api/dashboard/overview   - 概览指标
  GET /api/dashboard/category   - 品类分布统计
  GET /api/dashboard/skeleton   - 骨架效果排行 TOP10
  GET /api/dashboard/fission    - 裂变状态漏斗统计
  GET /api/dashboard/trend      - 效果数据趋势（近30天）
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, timedelta
from ..database import get_db
from ..models.material import Material
from ..models.skeleton import Skeleton
from ..models.fission import Fission
from ..models.effect_data import EffectData
from ..response import success, error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["数据统计"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    """概览指标：返回系统中核心实体的总数统计。"""
    try:
        material_count = db.query(func.count(Material.id)).scalar()
        material_pending = db.query(func.count(Material.id)).filter(Material.status == 0).scalar()
        material_done = db.query(func.count(Material.id)).filter(Material.status >= 1).scalar()

        skeleton_count = db.query(func.count(Skeleton.id)).scalar()

        fission_count = db.query(func.count(Fission.id)).scalar()
        fission_draft = db.query(func.count(Fission.id)).filter(Fission.output_status == 0).scalar()
        fission_active = db.query(func.count(Fission.id)).filter(Fission.output_status == 3).scalar()

        effect_count = db.query(func.count(EffectData.id)).scalar()
        cost_revenue = db.query(
            func.sum(EffectData.cost).label("total_cost"),
            func.sum(EffectData.revenue).label("total_revenue"),
            func.avg(EffectData.roi).label("avg_roi"),
        ).first()

        return success({
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
        })
    except Exception as e:
        logger.error(f"Dashboard overview failed: {e}", exc_info=True)
        return error(f"查询概览数据失败: {str(e)}", 500)


@router.get("/category")
def category_distribution(db: Session = Depends(get_db)):
    """品类分布统计：按品类分组统计各品类的素材数量。"""
    try:
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
        return success([
            {
                "category": r.category,
                "count": r.count,
                "dismantled": int(r.dismantled or 0),
            }
            for r in rows
        ])
    except Exception as e:
        logger.error(f"Dashboard category failed: {e}", exc_info=True)
        return error(f"查询品类分布失败: {str(e)}", 500)


@router.get("/skeleton")
def skeleton_ranking(
    sort_by: str = Query("avg_roi", pattern="^(avg_roi|avg_ctr|usage_count)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """骨架效果排行榜：按指定指标排序，返回 TOP N 骨架。"""
    try:
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
        return success([
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
        ])
    except Exception as e:
        logger.error(f"Dashboard skeleton ranking failed: {e}", exc_info=True)
        return error(f"查询骨架排行失败: {str(e)}", 500)


@router.get("/fission")
def fission_funnel(db: Session = Depends(get_db)):
    """裂变状态漏斗统计：统计各状态的裂变数量。"""
    try:
        status_map = {0: "草稿", 1: "待审核", 2: "已采用", 3: "已投放"}
        rows = (
            db.query(
                Fission.output_status.label("status"),
                func.count(Fission.id).label("count"),
            )
            .group_by(Fission.output_status)
            .order_by(Fission.output_status)
            .all()
        )
        return success([
            {
                "status": r.status,
                "label": status_map.get(r.status, f"状态{r.status}"),
                "count": r.count,
            }
            for r in rows
        ])
    except Exception as e:
        logger.error(f"Dashboard fission funnel failed: {e}", exc_info=True)
        return error(f"查询裂变漏斗失败: {str(e)}", 500)


@router.get("/trend")
def effect_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """效果数据趋势：按日期聚合最近 N 天的效果数据。"""
    try:
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
        return success([
            {
                "date": str(r.date),
                "avg_ctr": float(r.avg_ctr) if r.avg_ctr else None,
                "avg_roi": float(r.avg_roi) if r.avg_roi else None,
                "total_cost": float(r.total_cost) if r.total_cost else 0,
                "total_revenue": float(r.total_revenue) if r.total_revenue else 0,
                "count": r.count,
            }
            for r in rows
        ])
    except Exception as e:
        logger.error(f"Dashboard trend failed: {e}", exc_info=True)
        return error(f"查询趋势数据失败: {str(e)}", 500)
