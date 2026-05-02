"""
操作日志模型模块

定义 OperationLog（操作日志）ORM 模型，对应数据库中的 operation_log 表。
记录系统中的关键操作（创建/删除/状态变更），用于审计和追溯。

主要字段：
  id:         自增主键
  entity_type: 操作对象类型（material/skeleton/fission/effect/tag/option）
  entity_id:   操作对象 ID
  action:      操作类型（create/update/status_change/delete/import/export）
  detail:      操作详情（JSON，记录变更前后的关键字段）
  operator:    操作人标识
  created_at:  操作时间
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON
from sqlalchemy.sql import func
from backend.database import Base


class OperationLog(Base):
    """
    操作日志表（operation_log）

    记录系统中所有关键业务操作，用于审计追踪。
    每次创建、删除、状态变更、导入导出操作时自动写入。
    """

    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 操作对象类型：material / skeleton / fission / effect / tag / option
    entity_type = Column(String(50), nullable=False, comment="操作对象类型")

    # 操作对象 ID
    entity_id = Column(Integer, comment="操作对象 ID")

    # 操作类型：create / update / status_change / delete / import / export
    action = Column(String(50), nullable=False, comment="操作类型")

    # 操作详情（JSON），记录变更前后的关键字段
    detail = Column(JSON, comment="操作详情：变更前后的关键字段")

    # 操作人标识
    operator = Column(String(50), comment="操作人")

    # 操作时间
    created_at = Column(DateTime, server_default=func.now(), comment="操作时间")

    __table_args__ = (
        Index("idx_log_entity", "entity_type", "entity_id"),  # 按对象查询操作历史
        Index("idx_log_action", "action"),                      # 按操作类型筛选
        Index("idx_log_created", "created_at"),                 # 按时间排序
    )
