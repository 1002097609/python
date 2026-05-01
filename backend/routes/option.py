from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.option import Option
from ..schemas.option import OptionCreate, OptionUpdate, OptionResponse

router = APIRouter()


@router.get("/", response_model=list[OptionResponse])
def list_options(
    group_key: Optional[str] = Query(None, description="按分组筛选，如 platform / category / style 等"),
    is_active: Optional[int] = Query(None, comment="1=启用 0=禁用"),
    db: Session = Depends(get_db),
):
    query = db.query(Option)
    if group_key:
        query = query.filter(Option.group_key == group_key)
    if is_active is not None:
        query = query.filter(Option.is_active == is_active)
    items = query.order_by(Option.sort_order.asc(), Option.id.asc()).all()
    return items


@router.get("/groups")
def list_group_keys(db: Session = Depends(get_db)):
    """返回所有已有的分组 key"""
    rows = db.query(Option.group_key).distinct().all()
    return [r[0] for r in rows]


@router.get("/{option_id}", response_model=OptionResponse)
def get_option(option_id: int, db: Session = Depends(get_db)):
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")
    return item


@router.post("/", response_model=OptionResponse, status_code=201)
def create_option(data: OptionCreate, db: Session = Depends(get_db)):
    item = Option(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{option_id}", response_model=OptionResponse)
def update_option(option_id: int, data: OptionUpdate, db: Session = Depends(get_db)):
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{option_id}", status_code=204)
def delete_option(option_id: int, db: Session = Depends(get_db)):
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")
    db.delete(item)
    db.commit()
