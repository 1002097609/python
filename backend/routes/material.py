"""
素材管理路由模块（routes/material.py）。

提供营销素材的完整 CRUD（增删改查）接口，支持按平台、品类、状态进行筛选分页查询。
素材是系统中最基础的数据单元，所有拆解操作均以素材为入口。

路由列表：
  POST   /api/material/         - 创建新素材
  GET    /api/material/         - 分页查询素材列表（支持筛选）
  GET    /api/material/{id}     - 查询单个素材详情
  PUT    /api/material/{id}     - 更新素材信息
  DELETE /api/material/{id}     - 删除素材
"""

import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.material import Material
from ..schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse, BatchStatusUpdate
from ..services.operation_log import log_operation

# 创建素材管理专用路由器
router = APIRouter()


@router.post("/", response_model=MaterialResponse, status_code=201)
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    """
    创建新素材。

    接收素材的基本信息（标题、内容、平台、品类等），在数据库中创建一条新的素材记录。
    创建成功后返回完整的素材数据（含自动生成的 id 和时间戳）。

    请求参数：
        data (MaterialCreate): 素材创建模型，包含 title、content 等字段。

    返回值：
        MaterialResponse: 创建成功的素材对象，HTTP 状态码 201。
    """
    # 将 Pydantic 模型数据转为字典后直接解构为 ORM 模型实例
    material = Material(**data.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    log_operation(db, "material", material.id, "create", {"title": material.title, "platform": material.platform, "category": material.category})
    return material


@router.get("/")
def list_materials(
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None, description="按标签 ID 筛选（单标签，兼容旧接口）"),
    tag_ids: Optional[str] = Query(None, description="按多个标签 ID 筛选，逗号分隔，如 1,2,3"),
    keyword: Optional[str] = Query(None, description="按标题关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    分页查询素材列表，支持按平台、品类、状态、标签、关键词进行筛选。

    请求参数（均为可选查询参数）：
        platform (str):   按投放平台筛选，如 "抖音"、"快手" 等。
        category (str):   按素材品类筛选，如 "护肤"、"零食" 等。
        status (int):     按素材状态筛选，如 0=未拆解、1=已拆解。
        tag_id (int):     按标签 ID 筛选，只返回包含该标签的素材。
        keyword (str):    按标题关键词模糊搜索。
        page (int):       页码，从 1 开始，默认值 1。
        page_size (int):  每页条数，范围 1-100，默认值 20。

    返回值：
        dict: 分页结果，包含 items / total / page / page_size。
    """
    # 构建基础查询
    query = db.query(Material)

    # 根据传入的筛选条件动态追加过滤子句
    if platform:
        query = query.filter(Material.platform == platform)
    if category:
        query = query.filter(Material.category == category)
    if status is not None:
        query = query.filter(Material.status == status)

    # 标签筛选：通过 material_tag 关联表 JOIN 过滤
    from ..models.tag import MaterialTag
    if tag_ids:
        # 多标签筛选：素材包含任意一个指定标签即匹配（OR 语义）
        ids = [int(x) for x in tag_ids.split(',') if x.strip().isdigit()]
        if ids:
            query = query.join(MaterialTag, Material.id == MaterialTag.material_id)
            query = query.filter(MaterialTag.tag_id.in_(ids))
            query = query.distinct()
    elif tag_id is not None:
        query = query.join(MaterialTag, Material.id == MaterialTag.material_id)
        query = query.filter(MaterialTag.tag_id == tag_id)

    # 关键词搜索：标题模糊匹配
    if keyword:
        query = query.filter(Material.title.contains(keyword))

    # 先查总数，再分页取数据
    total = query.count()
    items = query.order_by(Material.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [MaterialResponse.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    """
    根据素材 ID 查询单个素材的详细信息。

    请求参数：
        material_id (int): 素材的唯一标识 ID。

    返回值：
        MaterialResponse: 素材详情对象。

    异常：
        HTTP 404: 当指定 ID 的素材不存在时抛出。
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    """
    更新指定素材的信息。支持部分更新（仅传入需要修改的字段）。

    请求参数：
        material_id (int): 要更新的素材 ID。
        data (MaterialUpdate): 更新数据模型，所有字段均为可选。

    返回值：
        MaterialResponse: 更新后的完整素材对象。

    异常：
        HTTP 404: 当指定 ID 的素材不存在时抛出。
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 使用 exclude_unset=True 仅获取调用方实际传入的字段，实现部分更新
    changed_fields = data.model_dump(exclude_unset=True)
    for key, value in changed_fields.items():
        setattr(material, key, value)

    db.commit()
    db.refresh(material)
    log_operation(db, "material", material.id, "update", {"changed_fields": list(changed_fields.keys())})
    return material


@router.put("/batch/status")
def batch_update_material_status(
    data: BatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    批量更新多个素材的状态。

    请求体：
        {"ids": [1, 2, 3], "status": 1}

    返回值：
        {"updated": 3}

    异常：
        HTTP 422: ids 为空或 status 不在合法值域（0/1/2）中时抛出。
    """
    if not data.ids:
        raise HTTPException(status_code=422, detail="ids 不能为空")
    if data.status not in (0, 1, 2):
        raise HTTPException(status_code=422, detail="status 必须为 0（未拆解）、1（已拆解）或 2（已归档）")
    updated = db.query(Material).filter(Material.id.in_(data.ids)).update(
        {"status": data.status}, synchronize_session=False
    )
    db.commit()
    for mid in data.ids:
        log_operation(db, "material", mid, "status_change", {"status": data.status})
    return {"updated": updated}


@router.delete("/{material_id}", status_code=204)
def delete_material(material_id: int, db: Session = Depends(get_db)):
    """
    删除指定的素材记录。

    请求参数：
        material_id (int): 要删除的素材 ID。

    返回值：
        无返回体，HTTP 状态码 204 表示删除成功。

    异常：
        HTTP 404: 当指定 ID 的素材不存在时抛出。
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 级联删除：先删关联的拆解记录（dismantle → skeleton → fission → effect_data）
    from ..models.dismantle import Dismantle
    from ..models.fission import Fission
    from ..models.effect_data import EffectData

    dismantles = db.query(Dismantle).filter(Dismantle.material_id == material_id).all()
    for dm in dismantles:
        # 级联删除该拆解关联的骨架及其裂变记录
        if dm.skeleton_id:
            fissions = db.query(Fission).filter(Fission.skeleton_id == dm.skeleton_id).all()
            for ff in fissions:
                db.query(EffectData).filter(EffectData.fission_id == ff.id).delete()
            db.query(Fission).filter(Fission.skeleton_id == dm.skeleton_id).delete()
            db.query(Skeleton).filter(Skeleton.id == dm.skeleton_id).delete()
        db.delete(dm)

    title = material.title
    db.delete(material)
    db.commit()
    log_operation(db, "material", material_id, "delete", {"title": title})


@router.post("/import")
def import_materials(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    批量导入素材（JSON 格式）。

    接收 JSON 文件，格式为素材对象数组：
    [{"title":"...", "content":"...", "platform":"抖音", "category":"护肤", "media_type":"video"}, ...]

    返回导入结果：成功数 / 跳过数（标题已存在则跳过）。
    """
    content = file.file.read().decode("utf-8")
    items = json.loads(content)
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="JSON 格式错误：根节点必须是数组")

    inserted = 0
    skipped = 0
    for item in items:
        title = item.get("title", "").strip()
        if not title:
            skipped += 1
            continue
        existing = db.query(Material).filter(Material.title == title).first()
        if existing:
            skipped += 1
            continue
        db.add(Material(
            title=title,
            content=item.get("content", ""),
            platform=item.get("platform", ""),
            category=item.get("category", ""),
            media_type=item.get("media_type", "video"),
            source_url=item.get("source_url", ""),
            status=item.get("status", 0),
        ))
        inserted += 1
    db.commit()
    log_operation(db, "material", 0, "import", {"inserted": inserted, "skipped": skipped})
    return {"inserted": inserted, "skipped": skipped, "message": f"导入完成：新增 {inserted} 条，跳过 {skipped} 条"}


@router.get("/export")
def export_materials(
    format: str = Query("json", pattern="^(json|csv)$"),
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    导出素材数据，支持 JSON 和 CSV 格式。

    参数：
        format: json（默认）或 csv
        platform / category / status: 可选筛选条件

    返回：文件下载响应。
    """
    query = db.query(Material)
    if platform:
        query = query.filter(Material.platform == platform)
    if category:
        query = query.filter(Material.category == category)
    if status is not None:
        query = query.filter(Material.status == status)

    items = query.order_by(Material.id).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "title": i.title,
            "content": i.content,
            "platform": i.platform,
            "category": i.category,
            "media_type": i.media_type,
            "source_url": i.source_url,
            "status": i.status,
        })

    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    log_operation(db, "material", 0, "export", {"format": format, "count": len(rows)})

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=materials_{timestamp}.csv"},
        )

    # JSON
    return StreamingResponse(
        io.BytesIO(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=materials_{timestamp}.json"},
    )
