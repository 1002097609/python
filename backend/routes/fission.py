"""
裂变引擎路由模块（routes/fission.py）。

提供素材裂变功能：选择已有骨架 + 输入新内容，通过模板填充引擎组合生成新的素材文案。
支持三种裂变模式：
  - replace_leaf（换叶子）:  替换 L1+L5，骨架不变，效果保留约 85%
  - replace_branch（换枝杈）: 替换 L3+L4，主题不变，效果保留约 65%
  - replace_style（换表达）:  替换 L2+L5，骨架不变，效果保留约 70%

路由列表：
  POST /api/fission/ - 执行裂变操作，生成新素材文案
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.fission import Fission
from ..models.skeleton import Skeleton
from ..models.effect_data import EffectData
from ..services.fission_engine import generate_output
from ..services.operation_log import log_operation

# 创建裂变引擎专用路由器
router = APIRouter()


class FissionRequest(BaseModel):
    """
    裂变请求参数模型。

    字段说明：
        skeleton_id (int):      必填。要使用的骨架 ID，骨架决定了内容的基本框架结构。
        source_material_id (int): 可选。源素材 ID，用于追溯裂变素材的来源。
        fission_mode (str):     必填。裂变模式，取值：replace_leaf / replace_branch / replace_style。
        new_topic (str):        可选。新主题/新品类名称，用于替换原骨架中的主题内容。
        new_category (str):     可选。新品类分类，如从"护肤"变为"零食"。
        new_platform (str):     可选。新投放平台，如从"抖音"变为"快手"。
        new_style (str):        可选。新风格标签，如"搞笑"、"温情"等。
        replacement (dict):     可选。自定义替换内容，key 为替换层级（如 "L5"），value 为替换数据。
    """
    skeleton_id: int
    source_material_id: Optional[int] = None
    fission_mode: str  # replace_leaf / replace_branch / replace_style
    new_topic: Optional[str] = None
    new_category: Optional[str] = None
    new_platform: Optional[str] = None
    new_style: Optional[str] = None
    replacement: Optional[dict] = None


@router.post("/")
def execute_fission(data: FissionRequest, db: Session = Depends(get_db)):
    """
    执行素材裂变操作。

    核心流程：
      1. 根据 skeleton_id 从骨架库获取骨架数据（结构层、元素层、策略层）
      2. 根据裂变模式（fission_mode）调用模板填充引擎生成输出内容
      3. 基于母体骨架的历史效果统计预测新素材的 CTR 和 ROI
      4. 将裂变记录存入数据库，并更新骨架的使用次数

    请求参数：
        data (FissionRequest): 裂变请求数据模型。

    返回值：
        dict: 包含以下字段的字典：
            - fission_id:     新建裂变记录的 ID
            - output_title:   生成的素材标题
            - output_content: 生成的素材正文内容
            - predicted_ctr:  预测点击率范围（如 "1.2%-1.5%"）
            - predicted_roi:  预测 ROI 范围（如 "1.5x-2.0x"）

    异常：
        HTTP 404: 当指定骨架不存在时抛出。
    """
    # 第一步：从骨架库获取指定骨架的完整数据
    skeleton = db.query(Skeleton).filter(Skeleton.id == data.skeleton_id).first()
    if not skeleton:
        raise HTTPException(status_code=404, detail="骨架不存在")

    import json

    # 提取骨架的三层核心数据
    structure = skeleton.structure_json   # L3 结构层：内容段落的逻辑顺序
    elements = skeleton.elements_json     # L4 元素层：标题公式、钩子句式等可插拔元素
    strategy = skeleton.strategy_desc      # L2 策略层：用什么情绪/策略打动用户

    # JSON 字段可能是字符串类型，需要统一解析为 Python 对象
    if isinstance(structure, str):
        structure = json.loads(structure)
    if isinstance(elements, str):
        elements = json.loads(elements)

    # 获取用户传入的自定义替换内容（可为空）
    replacement = data.replacement or {}

    # 第二步：根据裂变模式调用模板填充引擎，生成素材输出内容
    output_content = generate_output(
        fission_mode=data.fission_mode,
        structure=structure,
        elements=elements,
        strategy=strategy,
        new_topic=data.new_topic or "",
        replacement=replacement,
    )

    # 第三步：基于母体骨架的历史效果数据预测新素材的表现
    prediction = _predict_performance(skeleton, data.fission_mode, db)

    # 第四步：将裂变记录持久化到数据库
    fission = Fission(
        skeleton_id=data.skeleton_id,
        source_material_id=data.source_material_id,
        fission_mode=data.fission_mode,
        new_topic=data.new_topic,
        new_category=data.new_category,
        new_platform=data.new_platform,
        new_style=data.new_style,
        replacement_json=replacement,
        output_title=f"{data.new_topic or '未命名'}",
        output_content=output_content,
        output_status=0,  # 0=待投放
        predicted_ctr=prediction["ctr"],
        predicted_roi=prediction["roi"],
    )
    db.add(fission)

    # 第五步：更新骨架的使用次数，用于后续的效果统计和推荐排序
    skeleton.usage_count = (skeleton.usage_count or 0) + 1

    db.commit()
    db.refresh(fission)
    log_operation(db, "fission", fission.id, "create", {
        "skeleton_id": data.skeleton_id,
        "fission_mode": data.fission_mode,
        "new_topic": data.new_topic,
        "predicted_ctr": prediction["ctr"],
        "predicted_roi": prediction["roi"],
    })

    return {
        "fission_id": fission.id,
        "output_title": fission.output_title,
        "output_content": output_content,
        "predicted_ctr": prediction["ctr"],
        "predicted_roi": prediction["roi"],
    }


def _predict_performance(skeleton, fission_mode, db=None) -> dict:
    """
    效果预测函数：基于母体骨架的历史平均效果数据，乘以裂变模式系数，预测新素材的表现范围。

    预测逻辑：
      1. 取骨架的 avg_roi 和 avg_ctr 作为基准值（无历史数据时使用系统默认值）
      2. 根据裂变模式的效果保留系数计算预测基准
      3. 以对称的 +/-10% 波动范围给出预测区间

    注意：
      效果保留系数和默认基准值已迁移到数据库 option 表中（group_key=fission_mode），
      此处保留硬编码回退值仅作为兜底，确保在数据库未初始化时仍能运行。

    参数：
        skeleton (Skeleton): 骨架 ORM 对象，需包含 avg_roi 和 avg_ctr 字段。
        fission_mode (str):  裂变模式，决定效果保留比例。
        db (Session):        数据库会话，用于查询裂变模式的配置参数。

    返回值：
        dict: 包含两个预测字段：
            - ctr: 预测点击率范围字符串，格式 "X.X%-X.X%"
            - roi: 预测 ROI 范围字符串，格式 "X.Xx-X.Xx"
    """
    # 尝试从数据库读取裂变模式的效果保留系数
    mode_factor = None
    if db:
        from ..models.option import Option
        mode_option = db.query(Option).filter(
            Option.group_key == "fission_mode",
            Option.value == fission_mode,
            Option.is_active == 1,
        ).first()
        if mode_option:
            try:
                # 从 label 中提取效果保留系数，如 "换叶子（效果保留85%）" -> 0.85
                import re
                match = re.search(r'(\d+)%', mode_option.label)
                if match:
                    mode_factor = int(match.group(1)) / 100
            except (ValueError, AttributeError):
                pass

    # 读取骨架的历史平均效果指标，若无数据则使用系统默认值
    # 默认值也应逐步迁移到数据库 config 表中
    base_roi = float(skeleton.avg_roi or 2.0)    # 默认 ROI 基准值 2.0x
    base_ctr = float(skeleton.avg_ctr or 1.5)    # 默认 CTR 基准值 1.5%

    # 裂变模式效果保留系数（兜底值，优先使用数据库中的配置）
    if mode_factor is not None:
        factor = mode_factor
    else:
        factors = {
            "replace_leaf": 0.85,    # 换叶子：仅替换内容和表达，保留约 85% 效果
            "replace_branch": 0.65,  # 换枝杈：替换结构和元素，保留约 65% 效果
            "replace_style": 0.70,   # 换表达：替换策略和表达，保留约 70% 效果
        }
        factor = factors.get(fission_mode, 0.7)  # 未知模式使用保守系数 0.7

    # 计算预测范围：中心值 = 基准值 * 系数，波动范围为 +/-10%（对称）
    return {
        "ctr": f"{base_ctr * factor * 0.9:.1f}%-{base_ctr * factor * 1.1:.1f}%",
        "roi": f"{base_roi * factor * 0.9:.1f}x-{base_roi * factor * 1.1:.1f}x",
    }


@router.get("/")
def list_fissions(
    skeleton_id: Optional[int] = None,
    output_status: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    查询裂变记录列表，支持按骨架 ID 和产出状态筛选。

    请求参数：
        skeleton_id (int):   按骨架 ID 筛选（可选）
        output_status (int): 按产出状态筛选（可选，0=草稿 1=待审核 2=已采用 3=已投放）
        page (int):          页码，默认 1
        page_size (int):     每页条数，默认 20

    返回值：
        list[dict]: 裂变记录列表，每条包含 fission 基本信息和关联的骨架名称
    """
    query = db.query(Fission)

    # 按骨架 ID 筛选
    if skeleton_id:
        query = query.filter(Fission.skeleton_id == skeleton_id)
    # 按产出状态筛选
    if output_status is not None:
        query = query.filter(Fission.output_status == output_status)

    # 先查总数，再分页取数据
    total = query.count()
    items = query.order_by(Fission.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 组装返回数据，附带骨架名称便于前端展示
    result = []
    for item in items:
        skeleton = db.query(Skeleton).filter(Skeleton.id == item.skeleton_id).first()
        result.append({
            "id": item.id,
            "skeleton_id": item.skeleton_id,
            "skeleton_name": skeleton.name if skeleton else "未知骨架",
            "fission_mode": item.fission_mode,
            "new_topic": item.new_topic,
            "output_title": item.output_title,
            "output_content": item.output_content,
            "output_status": item.output_status,
            "predicted_ctr": item.predicted_ctr,
            "predicted_roi": item.predicted_roi,
            "actual_ctr": float(item.actual_ctr) if item.actual_ctr else None,
            "actual_roi": float(item.actual_roi) if item.actual_roi else None,
            "created_at": item.created_at,
        })
    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.put("/{fission_id}/status")
def update_fission_status(fission_id: int, status: int, db: Session = Depends(get_db)):
    """
    更新裂变记录的状态，支持状态流转：
      0=草稿 → 1=待审核 → 2=已采用 → 3=已投放

    状态流转规则：
      - 只能向前推进（不能回退）
      - 每次只能推进一个状态（不能跳跃）
      - 已投放（3）为终态，不可再变更

    请求参数：
        fission_id (int): 裂变记录 ID
        status (int):     目标状态值（0-3）

    返回值：
        dict: 操作结果描述

    异常：
        HTTP 400: 当状态流转不合法时抛出
        HTTP 404: 当裂变记录不存在时抛出
    """
    item = db.query(Fission).filter(Fission.id == fission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="裂变记录不存在")

    current = item.output_status

    # 校验目标状态合法性
    if status not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="无效的状态值，必须为 0-3")
    if status == current:
        raise HTTPException(status_code=400, detail="状态未变化")
    if status < current:
        raise HTTPException(status_code=400, detail="状态不能回退")
    if status - current != 1:
        raise HTTPException(status_code=400, detail="每次只能推进一个状态")

    item.output_status = status
    db.commit()
    db.refresh(item)

    status_names = {0: "草稿", 1: "待审核", 2: "已采用", 3: "已投放"}
    log_operation(db, "fission", fission_id, "status_change", {"from": current, "to": status})
    return {
        "id": item.id,
        "output_status": item.output_status,
        "message": f"状态已更新为「{status_names[status]}」",
    }


@router.delete("/{fission_id}")
def delete_fission(fission_id: int, db: Session = Depends(get_db)):
    """
    删除指定裂变记录。

    请求参数：
        fission_id (int): 裂变记录 ID

    返回值：
        dict: 操作结果描述

    异常：
        HTTP 404: 当裂变记录不存在时抛出。
    """
    item = db.query(Fission).filter(Fission.id == fission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="裂变记录不存在")
    db.delete(item)
    db.commit()
    log_operation(db, "fission", fission_id, "delete", {"title": item.output_title})
    return {"message": "删除成功"}


@router.get("/{fission_id}")
def get_fission(fission_id: int, db: Session = Depends(get_db)):
    """
    查询单条裂变记录的详细信息。

    请求参数：
        fission_id (int): 裂变记录 ID

    返回值:
        dict: 裂变记录详情

    异常：
        HTTP 404: 当裂变记录不存在时抛出。
    """
    item = db.query(Fission).filter(Fission.id == fission_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="裂变记录不存在")

    # 查询关联骨架信息
    skeleton = db.query(Skeleton).filter(Skeleton.id == item.skeleton_id).first()

    # 查询关联的效果数据记录
    effects = db.query(EffectData).filter(EffectData.fission_id == item.id).all()

    return {
        "id": item.id,
        "skeleton_id": item.skeleton_id,
        "skeleton_name": skeleton.name if skeleton else "未知骨架",
        "fission_mode": item.fission_mode,
        "new_topic": item.new_topic,
        "new_category": item.new_category,
        "new_platform": item.new_platform,
        "new_style": item.new_style,
        "output_title": item.output_title,
        "output_content": item.output_content,
        "output_status": item.output_status,
        "predicted_ctr": item.predicted_ctr,
        "predicted_roi": item.predicted_roi,
        "actual_ctr": float(item.actual_ctr) if item.actual_ctr else None,
        "actual_roi": float(item.actual_roi) if item.actual_roi else None,
        "effects": [
            {
                "id": e.id,
                "platform": e.platform,
                "impressions": e.impressions,
                "clicks": e.clicks,
                "ctr": float(e.ctr) if e.ctr else None,
                "conversions": e.conversions,
                "cvr": float(e.cvr) if e.cvr else None,
                "cost": float(e.cost) if e.cost else None,
                "revenue": float(e.revenue) if e.revenue else None,
                "roi": float(e.roi) if e.roi else None,
                "cpa": float(e.cpa) if e.cpa else None,
                "stat_date": str(e.stat_date) if e.stat_date else None,
            }
            for e in effects
        ],
        "created_at": item.created_at,
    }
