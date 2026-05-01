"""
选项数据路由模块（routes/options.py）- 旧版兼容接口。

提供批量获取所有下拉框选项的功能，按分组 key 聚合后返回。
此模块为遗留兼容接口，新功能请使用 /api/option/ 新版路由（routes/option.py）。

路由列表：
  GET /api/options/ - 获取全部启用的选项数据，按分组 key 聚合返回
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.option import Option

# 创建旧版选项数据专用路由器
router = APIRouter()


@router.get("", include_in_schema=False)
@router.get("/")
def get_all_options(db: Session = Depends(get_db)):
    """
    从数据库读取所有已启用的下拉框选项，按分组 key 聚合后返回。

    返回的数据结构为字典，key 为分组标识（如 "platform"），value 为该分组的选项列表。
    每个选项包含 label（显示文本）和 value（实际值）。

    示例返回值：
    {
        "platform": [{"label": "抖音", "value": "douyin"}, {"label": "快手", "value": "kuaishou"}],
        "category": [{"label": "护肤", "value": "skincare"}, {"label": "零食", "value": "snack"}]
    }

    返回值：
        dict: 以 group_key 为键、选项列表为值的字典。
    """
    # 仅查询已启用（is_active=1）的选项，按分组和排序权重排列
    items = (
        db.query(Option)
        .filter(Option.is_active == 1)
        .order_by(Option.group_key, Option.sort_order, Option.id)
        .all()
    )

    # 将列表形式的选项数据按 group_key 聚合为字典结构，方便前端直接使用
    result = {}
    for item in items:
        key = item.group_key
        if key not in result:
            result[key] = []
        result[key].append({"label": item.label, "value": item.value})
    return result
