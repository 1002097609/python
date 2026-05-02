"""
骨架库路由模块（routes/skeleton.py）。

提供可复用骨架的查询、删除以及从拆解记录自动提取骨架的功能。
骨架是从拆解结果中提取的 L2-L4 层结构化数据，代表可跨品类复用的内容模板。
骨架附带效果统计（avg_roi、avg_ctr）和 usage_count，用于指导裂变时的骨架选择。

路由列表：
  GET    /api/skeleton/                      - 分页查询骨架列表（支持筛选和排序）
  GET    /api/skeleton/{id}                  - 查询单个骨架详情
  DELETE /api/skeleton/{id}                  - 删除骨架
  POST   /api/skeleton/from-dismantle/{id}   - 从拆解记录自动提取骨架
"""

import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from ..database import get_db
from ..models.skeleton import Skeleton
from ..services.operation_log import log_operation

# 创建骨架库专用路由器
router = APIRouter()


def _skeleton_to_dict(s: Skeleton) -> dict:
    """
    将 Skeleton ORM 对象转换为普通字典，处理 Decimal 类型的序列化问题。

    数据库中的 avg_roi 和 avg_ctr 字段为 Decimal 类型，JSON 序列化时需要转为 float。

    参数：
        s (Skeleton): 骨架 ORM 实例。

    返回值：
        dict: 包含骨架各字段的普通字典，可直接被 FastAPI 序列化为 JSON 响应。
    """
    return {
        "id": s.id,
        "name": s.name,
        "skeleton_type": s.skeleton_type,
        "usage_count": s.usage_count,
        # Decimal 类型不能直接 JSON 序列化，需要转为 float
        "avg_roi": float(s.avg_roi) if isinstance(s.avg_roi, Decimal) else s.avg_roi,
        "avg_ctr": float(s.avg_ctr) if isinstance(s.avg_ctr, Decimal) else s.avg_ctr,
        "created_at": s.created_at,
    }


@router.get("/")
def list_skeletons(
    platform: Optional[str] = Query(None),
    skeleton_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="按名称/描述关键词搜索"),
    sort_by: str = Query("usage_count", pattern="^(usage_count|avg_roi|avg_ctr|created_at)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    分页查询骨架列表，支持按平台、骨架类型筛选，支持按使用次数/平均ROI/平均CTR/创建时间排序。

    请求参数（均为可选查询参数）：
        platform (str):       按投放平台筛选，如 "抖音"。
        skeleton_type (str):  按骨架类型筛选，如 "测评对比型"、"红黑榜型" 等。
        sort_by (str):        排序字段，可选值为 usage_count / avg_roi / avg_ctr / created_at。
                              默认为 usage_count（使用次数）。
        page (int):           页码，从 1 开始，默认值 1。
        page_size (int):      每页条数，范围 1-100，默认值 20。

    返回值：
        list[dict]: 骨架字典列表，按指定字段倒序排列。
    """
    # 构建基础查询
    query = db.query(Skeleton)

    # 动态追加筛选条件
    if platform:
        query = query.filter(Skeleton.platform == platform)
    if skeleton_type:
        query = query.filter(Skeleton.skeleton_type == skeleton_type)
    if keyword:
        query = query.filter(Skeleton.name.contains(keyword) | Skeleton.strategy_desc.contains(keyword))

    # 根据传入的排序字段动态获取 ORM 列属性，默认使用 usage_count
    sort_column = getattr(Skeleton, sort_by, Skeleton.usage_count)
    query = query.order_by(sort_column.desc())

    # 先查总数，再分页取数据
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_skeleton_to_dict(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{skeleton_id}")
def get_skeleton(skeleton_id: int, db: Session = Depends(get_db)):
    """
    根据骨架 ID 查询单个骨架的详细信息。

    请求参数：
        skeleton_id (int): 骨架的唯一标识 ID。

    返回值:
        Skeleton: 骨架 ORM 对象（FastAPI 自动序列化）。

    异常：
        HTTP 404: 当骨架不存在时抛出。
    """
    skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
    if not skeleton:
        raise HTTPException(status_code=404, detail="骨架不存在")
    return skeleton


@router.delete("/{skeleton_id}", status_code=204)
def delete_skeleton(skeleton_id: int, db: Session = Depends(get_db)):
    """
    删除指定的骨架记录。

    请求参数：
        skeleton_id (int): 要删除的骨架 ID。

    返回值：
        无返回体，HTTP 状态码 204 表示删除成功。

    异常：
        HTTP 404: 当骨架不存在时抛出。
    """
    skeleton = db.query(Skeleton).filter(Skeleton.id == skeleton_id).first()
    if not skeleton:
        raise HTTPException(status_code=404, detail="骨架不存在")

    # 级联删除：先删关联的裂变记录和效果数据
    from ..models.fission import Fission
    from ..models.effect_data import EffectData

    fissions = db.query(Fission).filter(Fission.skeleton_id == skeleton_id).all()
    for ff in fissions:
        db.query(EffectData).filter(EffectData.fission_id == ff.id).delete()
    db.query(Fission).filter(Fission.skeleton_id == skeleton_id).delete()

    name = skeleton.name
    fissions_count = len(fissions)
    db.delete(skeleton)
    db.commit()
    log_operation(db, "skeleton", skeleton_id, "delete", {"name": name, "cascade_fissions": fissions_count})


@router.post("/from-dismantle/{dismantle_id}")
def create_skeleton_from_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    """
    从已有的拆解记录中自动提取骨架并存入骨架库。

    提取逻辑：从拆解记录的 L3 结构层智能推断骨架类型，
    将 L2（策略）、L3（结构）、L4（元素）层数据组合为新的骨架记录。
    同时更新拆解记录的 skeleton_id 外键关联。

    请求参数：
        dismantle_id (int): 拆解记录的唯一标识 ID。

    返回值：
        dict: 包含 skeleton_id（新建骨架ID）、name（骨架名称）和 message（操作结果描述）的字典。

    异常：
        HTTP 404: 当拆解记录不存在时抛出。
    """
    from ..models.dismantle import Dismantle

    # 首先检查拆解记录是否存在
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")

    # 根据 L3 结构层的段落名称推断骨架类型（如"测评对比型"、"红黑榜型"等）
    skeleton_type = _infer_skeleton_type(dismantle.l3_structure)

    # 拼接骨架名称：类型 + 主题，截断至 100 字符以内
    name = f"{skeleton_type} — {dismantle.l1_topic or '未命名'}"[:100]

    # 从拆解记录的各层数据中提取骨架所需的字段
    skeleton = Skeleton(
        name=name,
        skeleton_type=skeleton_type,
        source_material_id=dismantle.material_id,  # 关联原始素材
        strategy_desc=dismantle.l2_emotion,         # 策略层 -> 策略描述
        structure_json=dismantle.l3_structure,       # 结构层 -> 骨架 JSON
        elements_json=dismantle.l4_elements,         # 元素层 -> 元素 JSON
        style_tags=dismantle.l2_strategy,            # 策略层 -> 风格标签列表
    )
    db.add(skeleton)
    db.flush()  # .flush() 获取自增 ID 但不提交事务

    # 更新拆解记录的外键关联，建立拆解与骨架的映射关系
    dismantle.skeleton_id = skeleton.id

    db.commit()
    db.refresh(skeleton)
    log_operation(db, "skeleton", skeleton.id, "create", {"name": name, "skeleton_type": skeleton_type, "source_dismantle_id": dismantle_id})
    return {"skeleton_id": skeleton.id, "name": name, "message": "骨架提取成功"}


def _infer_skeleton_type(l3_structure) -> str:
    """
    根据 L3 内容结构中的段落名称自动推断骨架类型。

    判断逻辑：解析 L3 结构数组中的段落 name 字段，通过关键词匹配确定骨架类型。

    匹配规则：
        含"测评"或"对比" -> "测评对比型"
        含"红榜"或"黑榜" -> "红黑榜型"
        含"误区"         -> "误区纠正型"
        含"步骤"         -> "教程步骤型"
        其他              -> "通用型"

    参数：
        l3_structure: L3 结构数据，可以是 JSON 字符串或已解析的 list。

    返回值：
        str: 推断出的骨架类型名称。
    """
    # 空值兜底：若 L3 结构为空，返回默认的"通用型"
    if not l3_structure:
        return "通用型"

    import json
    # 若传入的是 JSON 字符串，先解析为 Python 对象
    structure = json.loads(l3_structure) if isinstance(l3_structure, str) else l3_structure

    # 提取所有段落的 name 字段拼接为逗号分隔的字符串，便于关键词匹配
    names = [s.get("name", "") for s in structure]
    names_str = ",".join(names)

    # 根据段落名称中的关键词判定骨架类型
    if "测评" in names_str or "对比" in names_str:
        return "测评对比型"
    if "红榜" in names_str or "黑榜" in names_str:
        return "红黑榜型"
    if "误区" in names_str:
        return "误区纠正型"
    if "步骤" in names_str:
        return "教程步骤型"
    return "通用型"


@router.post("/import")
def import_skeletons(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    批量导入骨架（JSON 格式）。

    接收 JSON 文件，格式为骨架对象数组：
    [{"name":"...", "skeleton_type":"测评对比型", "strategy_desc":"...", "structure_json":[...], "elements_json":{...}}, ...]

    返回导入结果：成功数 / 跳过数（名称已存在则跳过）。
    """
    content = file.file.read().decode("utf-8")
    items = json.loads(content)
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="JSON 格式错误：根节点必须是数组")

    inserted = 0
    skipped = 0
    for item in items:
        name = item.get("name", "").strip()
        if not name:
            skipped += 1
            continue
        existing = db.query(Skeleton).filter(Skeleton.name == name).first()
        if existing:
            skipped += 1
            continue
        db.add(Skeleton(
            name=name,
            skeleton_type=item.get("skeleton_type"),
            strategy_desc=item.get("strategy_desc"),
            structure_json=item.get("structure_json"),
            elements_json=item.get("elements_json"),
            style_tags=item.get("style_tags"),
            platform=item.get("platform"),
        ))
        inserted += 1
    db.commit()
    log_operation(db, "skeleton", 0, "import", {"inserted": inserted, "skipped": skipped})
    return {"inserted": inserted, "skipped": skipped, "message": f"导入完成：新增 {inserted} 条，跳过 {skipped} 条"}


@router.get("/export")
def export_skeletons(
    format: str = Query("json", pattern="^(json|csv)$"),
    platform: Optional[str] = Query(None),
    skeleton_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    导出骨架数据，支持 JSON 和 CSV 格式。

    参数：
        format: json（默认）或 csv
        platform / skeleton_type: 可选筛选条件

    返回：文件下载响应。
    """
    query = db.query(Skeleton)
    if platform:
        query = query.filter(Skeleton.platform == platform)
    if skeleton_type:
        query = query.filter(Skeleton.skeleton_type == skeleton_type)

    items = query.order_by(Skeleton.id).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "name": i.name,
            "skeleton_type": i.skeleton_type,
            "strategy_desc": i.strategy_desc,
            "structure_json": json.dumps(i.structure_json, ensure_ascii=False) if i.structure_json else "",
            "elements_json": json.dumps(i.elements_json, ensure_ascii=False) if i.elements_json else "",
            "style_tags": json.dumps(i.style_tags, ensure_ascii=False) if i.style_tags else "",
            "platform": i.platform,
            "usage_count": i.usage_count,
            "avg_roi": float(i.avg_roi) if i.avg_roi else None,
            "avg_ctr": float(i.avg_ctr) if i.avg_ctr else None,
        })

    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    log_operation(db, "skeleton", 0, "export", {"format": format, "count": len(rows)})

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=skeletons_{timestamp}.csv"},
        )

    # JSON
    return StreamingResponse(
        io.BytesIO(json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=skeletons_{timestamp}.json"},
    )
