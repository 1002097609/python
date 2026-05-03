"""
操作日志路由模块（routes/operation_log.py）。

提供操作日志的查询接口。

路由列表：
  GET /api/operation-log/ — 查询操作日志（支持筛选、分页）
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..services.operation_log import query_logs
from ..response import success, error

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def list_operation_logs(
    entity_type: Optional[str] = Query(None, description="操作对象类型"),
    entity_id: Optional[int] = Query(None, description="操作对象 ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询操作日志列表，支持按对象类型、对象 ID、操作类型筛选，按时间倒序排列。"""
    try:
        return success(query_logs(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            page=page,
            page_size=page_size,
        ))
    except Exception as e:
        logger.error(f"List operation logs failed: {e}", exc_info=True)
        return error(f"查询操作日志失败: {str(e)}", 500)
