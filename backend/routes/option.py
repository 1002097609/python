"""
选项数据路由模块（routes/option.py）- 新版。

提供下拉框选项的 CRUD 管理接口，支持按分组（group_key）和启用状态筛选。
选项数据用于前端页面的各种下拉选择器，如投放平台、素材品类、风格标签等。
每个选项包含分组标识（group_key）、显示文本（label）和实际值（value）。

option 表是品类/平台/风格/策略等数据的唯一数据源。
tag 表通过 option_id 外键引用 option 表。

路由列表：
  GET    /api/option/         - 查询选项列表（支持按分组和启用状态筛选）
  GET    /api/option/groups   - 获取所有已有的分组 key 列表
  GET    /api/option/{id}     - 查询单个选项详情
  POST   /api/option/         - 创建新选项
  PUT    /api/option/{id}     - 更新选项信息
  DELETE /api/option/{id}     - 删除选项
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.option import Option
from ..schemas.option import OptionCreate, OptionUpdate, OptionResponse

# 创建新版选项数据专用路由器
router = APIRouter()


@router.get("/", response_model=list[OptionResponse])
def list_options(
    group_key: Optional[str] = Query(None, description="按分组筛选，如 platform / category / style 等"),
    is_active: Optional[int] = Query(None, comment="1=启用 0=禁用"),
    db: Session = Depends(get_db),
):
    """
    查询选项列表，支持按分组标识和启用状态筛选。

    结果按排序权重（sort_order）升序排列，同权重下按 ID 升序排列，
    确保前端下拉框中选项的顺序可控。

    请求参数（均为可选查询参数）：
        group_key (str):   按分组标识筛选，如 "platform"（平台）、"category"（品类）、"style"（风格）等。
        is_active (int):   按启用状态筛选，1=启用，0=禁用。不传则返回全部。

    返回值：
        list[OptionResponse]: 选项列表。
    """
    query = db.query(Option)

    # 动态追加筛选条件
    if group_key:
        query = query.filter(Option.group_key == group_key)
    if is_active is not None:
        query = query.filter(Option.is_active == is_active)

    # 先按排序权重升序，再按 ID 升序（保证排序稳定性）
    items = query.order_by(Option.sort_order.asc(), Option.id.asc()).all()
    return items


@router.get("/groups")
def list_group_keys(db: Session = Depends(get_db)):
    """
    获取所有已有的分组 key 列表。

    用于前端动态生成下拉框的分组导航，提升管理页面的可用性。

    返回值:
        list[str]: 分组 key 字符串列表，如 ["platform", "category", "style"]。
    """
    # 使用 distinct 查询去重，获取所有不重复的 group_key
    rows = db.query(Option.group_key).distinct().all()
    # SQLAlchemy distinct().all() 返回的是元组列表，需要提取第一个元素
    return [r[0] for r in rows]


@router.get("/{option_id}", response_model=OptionResponse)
def get_option(option_id: int, db: Session = Depends(get_db)):
    """
    根据选项 ID 查询单个选项的详细信息。

    请求参数：
        option_id (int): 选项的唯一标识 ID。

    返回值：
        OptionResponse: 选项详情对象。

    异常：
        HTTP 404: 当选项不存在时抛出。
    """
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")
    return item


@router.post("/", response_model=OptionResponse, status_code=201)
def create_option(data: OptionCreate, db: Session = Depends(get_db)):
    """
    创建新的下拉框选项。

    请求参数：
        data (OptionCreate): 选项创建模型，包含 group_key、label、value、sort_order 字段。

    返回值：
        OptionResponse: 创建成功的选项对象，HTTP 状态码 201。
    """
    item = Option(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{option_id}", response_model=OptionResponse)
def update_option(option_id: int, data: OptionUpdate, db: Session = Depends(get_db)):
    """
    更新指定选项的信息。支持部分更新（仅传入需要修改的字段）。

    可用于调整显示文本、排序权重或启用/禁用状态。

    请求参数：
        option_id (int):    要更新的选项 ID。
        data (OptionUpdate): 更新模型，所有字段均为可选。

    返回值：
        OptionResponse: 更新后的完整选项对象。

    异常：
        HTTP 404: 当选项不存在时抛出。
    """
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")

    # exclude_unset=True 确保只有调用方实际传入的字段才会被更新
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{option_id}", status_code=204)
def delete_option(option_id: int, db: Session = Depends(get_db)):
    """
    删除指定的选项记录。

    请求参数：
        option_id (int): 要删除的选项 ID。

    返回值：
        无返回体，HTTP 状态码 204 表示删除成功。

    异常：
        HTTP 404: 当选项不存在时抛出。
    """
    item = db.query(Option).filter(Option.id == option_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="选项不存在")
    db.delete(item)
    db.commit()
