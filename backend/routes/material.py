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
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.material import Material
from ..models.skeleton import Skeleton
from ..schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse, BatchStatusUpdate
from ..services.operation_log import log_operation
from ..response import success, created as created_response, no_content as no_content_response, error

logger = logging.getLogger(__name__)

# 创建素材管理专用路由器
router = APIRouter()


@router.post("/", status_code=201)
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    """
    创建新素材。

    接收素材的基本信息（标题、内容、平台、品类等），在数据库中创建一条新的素材记录。
    创建成功后返回完整的素材数据（含自动生成的 id 和时间戳）。
    """
    try:
        material = Material(**data.model_dump())
        db.add(material)
        db.commit()
        db.refresh(material)
        log_operation(db, "material", material.id, "create", {"title": material.title, "platform": material.platform, "category": material.category})
        return created_response(MaterialResponse.model_validate(material).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Create material failed: {e}", exc_info=True)
        return error(f"创建素材失败: {str(e)}", 500)


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
    """
    try:
        query = db.query(Material)

        if platform:
            query = query.filter(Material.platform == platform)
        if category:
            query = query.filter(Material.category == category)
        if status is not None:
            query = query.filter(Material.status == status)

        from ..models.tag import MaterialTag
        if tag_ids:
            ids = [int(x) for x in tag_ids.split(',') if x.strip().isdigit()]
            if ids:
                query = query.join(MaterialTag, Material.id == MaterialTag.material_id)
                query = query.filter(MaterialTag.tag_id.in_(ids))
                query = query.distinct()
        elif tag_id is not None:
            query = query.join(MaterialTag, Material.id == MaterialTag.material_id)
            query = query.filter(MaterialTag.tag_id == tag_id)

        if keyword:
            query = query.filter(
                (Material.title.contains(keyword)) | (Material.content.contains(keyword))
            )

        total = query.count()
        items = query.order_by(Material.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return success({
            "items": [MaterialResponse.model_validate(i).model_dump() for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except Exception as e:
        logger.error(f"List materials failed: {e}", exc_info=True)
        return error(f"查询素材列表失败: {str(e)}", 500)


@router.get("/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    """
    根据素材 ID 查询单个素材的详细信息。
    """
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)
        return success(MaterialResponse.model_validate(material).model_dump())
    except Exception as e:
        logger.error(f"Get material {material_id} failed: {e}", exc_info=True)
        return error(f"查询素材失败: {str(e)}", 500)


@router.put("/{material_id}")
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    """
    更新指定素材的信息。支持部分更新（仅传入需要修改的字段）。
    """
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)

        changed_fields = data.model_dump(exclude_unset=True)
        for key, value in changed_fields.items():
            setattr(material, key, value)

        db.commit()
        db.refresh(material)
        log_operation(db, "material", material.id, "update", {"changed_fields": list(changed_fields.keys())})
        return success(MaterialResponse.model_validate(material).model_dump())
    except Exception as e:
        db.rollback()
        logger.error(f"Update material {material_id} failed: {e}", exc_info=True)
        return error(f"更新素材失败: {str(e)}", 500)


@router.put("/batch/status")
def batch_update_material_status(
    data: BatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    批量更新多个素材的状态。

    请求体：
        {"ids": [1, 2, 3], "status": 1}
    """
    try:
        if not data.ids:
            return error("ids 不能为空", 422)
        if data.status not in (0, 1, 2):
            return error("status 必须为 0（未拆解）、1（已拆解）或 2（已归档）", 422)
        updated = db.query(Material).filter(Material.id.in_(data.ids)).update(
            {"status": data.status}, synchronize_session=False
        )
        db.commit()
        for mid in data.ids:
            log_operation(db, "material", mid, "status_change", {"status": data.status})
        return success({"updated": updated})
    except Exception as e:
        db.rollback()
        logger.error(f"Batch update material status failed: {e}", exc_info=True)
        return error(f"批量更新失败: {str(e)}", 500)


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    """
    删除指定的素材记录。
    """
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return error("素材不存在", 404)

        # 级联删除：先删关联的拆解记录（dismantle → skeleton → fission → effect_data）
        from ..models.dismantle import Dismantle
        from ..models.fission import Fission
        from ..models.effect_data import EffectData

        dismantles = db.query(Dismantle).filter(Dismantle.material_id == material_id).all()
        for dm in dismantles:
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
        return no_content_response()
    except Exception as e:
        db.rollback()
        logger.error(f"Delete material {material_id} failed: {e}", exc_info=True)
        return error(f"删除素材失败: {str(e)}", 500)


@router.post("/import")
def import_materials(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    批量导入素材（JSON 格式）。
    """
    try:
        content = file.file.read().decode("utf-8")
        items = json.loads(content)
        if not isinstance(items, list):
            return error("JSON 格式错误：根节点必须是数组", 400)

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
        return success({"inserted": inserted, "skipped": skipped, "message": f"导入完成：新增 {inserted} 条，跳过 {skipped} 条"})
    except json.JSONDecodeError:
        return error("JSON 格式无效", 400)
    except Exception as e:
        db.rollback()
        logger.error(f"Import materials failed: {e}", exc_info=True)
        return error(f"导入失败: {str(e)}", 500)


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
    """
    try:
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

        return StreamingResponse(
            io.BytesIO(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=materials_{timestamp}.json"},
        )
    except Exception as e:
        logger.error(f"Export materials failed: {e}", exc_info=True)
        return error(f"导出失败: {str(e)}", 500)
