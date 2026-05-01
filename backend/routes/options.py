from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.option import Option

router = APIRouter()


@router.get("")
def get_all_options(db: Session = Depends(get_db)):
    """从数据库读取所有下拉框选项，按分组返回"""
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
    return result
