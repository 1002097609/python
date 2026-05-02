"""
操作日志服务模块（services/operation_log.py）。

提供统一的日志写入和查询接口，供各路由模块调用。
"""

from sqlalchemy.orm import Session
from backend.models.operation_log import OperationLog


def log_operation(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    detail: dict = None,
    operator: str = None,
):
    """
    记录一条操作日志。

    参数：
        db:         数据库会话
        entity_type: 操作对象类型（material/skeleton/fission/effect/tag/option）
        entity_id:   操作对象 ID
        action:      操作类型（create/update/status_change/delete/import/export）
        detail:      操作详情（dict，可为空）
        operator:    操作人标识（可为空）
    """
    try:
        db.add(OperationLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            detail=detail or {},
            operator=operator or "system",
        ))
        db.commit()
    except Exception:
        # 日志写入失败不应影响主业务流程
        db.rollback()


def query_logs(
    db: Session,
    entity_type: str = None,
    entity_id: int = None,
    action: str = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    查询操作日志，支持按对象类型、对象 ID、操作类型筛选，按时间倒序排列。

    返回：
        dict: {items: [...], total, page, page_size}
    """
    query = db.query(OperationLog)

    if entity_type:
        query = query.filter(OperationLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(OperationLog.entity_id == entity_id)
    if action:
        query = query.filter(OperationLog.action == action)

    total = query.count()
    items = query.order_by(OperationLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": item.id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "action": item.action,
                "detail": item.detail,
                "operator": item.operator,
                "created_at": str(item.created_at) if item.created_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
