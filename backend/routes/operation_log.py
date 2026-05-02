"""
操作日志路由模块（routes/operation_log.py）。

提供操作日志的查询接口。

路由列表：
  GET /api/operation-log/ — 查询操作日志（支持筛选、分页）
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..services.operation_log import query_logs

router = APIRouter()


@router.get("/")
def list_operation_logs(
    entity_type: Optional[str] = Query(None, description="操作对象类型：material/skeleton/fission/effect/tag/option"),
    entity_id: Optional[int] = Query(None, description="操作对象 ID"),
    action: Optional[str] = Query(None, description="操作类型：create/update/status_change/delete/import/export"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    查询操作日志列表，支持按对象类型、对象 ID、操作类型筛选，按时间倒序排列。
    """
    return query_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        page=page,
        page_size=page_size,
    )
