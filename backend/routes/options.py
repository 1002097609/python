"""
选项数据路由模块（routes/options.py）- 旧版兼容接口。

提供批量获取所有下拉框选项的功能，按分组 key 聚合后返回。
此模块为遗留兼容接口，新功能请使用 /api/option/ 新版路由（routes/option.py）。

路由列表：
  GET /api/options/ - 获取全部启用的选项数据，按分组 key 聚合返回
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.option import Option
from ..response import success, error

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", include_in_schema=False)
@router.get("/")
def get_all_options(db: Session = Depends(get_db)):
    """从数据库读取所有已启用的下拉框选项，按分组 key 聚合后返回。"""
    try:
        items = (
            db.query(Option)
            .filter(Option.is_active == 1)
            .order_by(Option.group_key, Option.sort_order, Option.id)
            .all()
        )

        result = {}
        for item in items:
            key = item.group_key
            if key not in result:
                result[key] = []
            result[key].append({"label": item.label, "value": item.value})
        return success(result)
    except Exception as e:
        logger.error(f"Get all options failed: {e}", exc_info=True)
        return error(f"查询选项失败: {str(e)}", 500)
