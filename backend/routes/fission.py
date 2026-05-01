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
    output_content = _generate_output(
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

    return {
        "fission_id": fission.id,
        "output_title": fission.output_title,
        "output_content": output_content,
        "predicted_ctr": prediction["ctr"],
        "predicted_roi": prediction["roi"],
    }


def _generate_output(fission_mode, structure, elements, strategy, new_topic, replacement) -> str:
    """
    模板填充引擎：根据裂变模式和骨架结构，将新内容填充到骨架中生成最终文案。

    三种裂变模式的核心差异：
      - replace_leaf（换叶子）:   保持 L2-L4 骨架不变，替换 L1（主题）和 L5（表达）
      - replace_branch（换枝杈）: 保持 L1-L2 主题策略不变，替换 L3（结构）和 L4（元素）
      - replace_style（换表达）:  保持 L1/L3-L4 骨架不变，替换 L2（策略）和 L5（表达）

    所有需要用户手动填写的部分通过 replacement 参数传入，
    若 replacement 中未提供对应内容，则输出段落占位符。

    参数：
        fission_mode (str):  裂变模式，决定替换哪些层级。
        structure (list):    L3 结构层数据，包含各段落名称和功能描述。
        elements (dict):     L4 元素层数据，包含可插拔的元素（标题公式、钩子等）。
        strategy (str):      L2 策略层描述。
        new_topic (str):     新主题/品类名称，用于替换原主题内容。
        replacement (dict):  自定义替换内容字典，key 为层级（如 "L5"），value 为替换数据。

    返回值：
        str: 填充后的素材文案，段落之间用换行符分隔。
    """
    content = []

    # 从 replacement 中提取各层替换数据（可能为空）
    l5_data = replacement.get("L5", {})
    l4_data = replacement.get("L4", {})
    l3_data = replacement.get("L3", {})
    l2_data = replacement.get("L2", {})

    # 获取用户提供的金句列表和策略描述
    golden_sentences = l5_data.get("golden_sentences", [])
    new_strategy = l2_data.get("strategy_desc", strategy)  # 换表达模式下使用新策略

    # 遍历结构层中的每个段落，逐段填充内容
    if isinstance(structure, list):
        for section in structure:
            section_name = section.get("name", "")        # 段落名称，如"开头"、"主体"
            section_func = section.get("function", "")     # 段落功能描述，如"痛点共鸣"
            content.append(f"【{section_name} — {section_func}】")

            # --------------------------------------------------
            # replace_leaf 模式：保持骨架（L2-L4）不变，替换主题和表达
            # --------------------------------------------------
            if fission_mode == "replace_leaf":
                # 开头段落：用新主题生成共鸣句式
                if section_name in ("开头", "痛点共鸣"):
                    hook = l5_data.get("hook") or l4_data.get("hook")
                    content.append(hook or f"你是否也有{new_topic}相关的困扰？")
                # 主体段落：优先使用用户提供的金句，其次使用骨架元素中的钩子
                elif section_name in ("主体", "卖点"):
                    if golden_sentences:
                        content.append(golden_sentences[0])
                    elif elements and isinstance(elements, dict):
                        hook = elements.get("hook", "")
                        content.append(hook or f"[请填写{section_name}内容]")
                    else:
                        content.append(f"[请填写{section_name}内容]")
                # 结尾段落：优先使用用户提供的互动设计，其次使用骨架元素
                elif section_name in ("结尾", "互动"):
                    interaction = l5_data.get("interaction") or (elements or {}).get("interaction", "")
                    content.append(interaction or f"[请填写{section_name}内容]")
                else:
                    filler = l5_data.get(section_name, "")
                    content.append(filler or f"[请填写{section_name}内容]")

            # --------------------------------------------------
            # replace_branch 模式：保持主题策略（L1-L2）不变，替换结构和元素
            # --------------------------------------------------
            elif fission_mode == "replace_branch":
                # 从 replacement.L3 获取新结构段落的内容
                branch_content = l3_data.get(section_name, {})
                if isinstance(branch_content, dict):
                    # 如果 L3 替换数据是 dict，提取 content 字段
                    text = branch_content.get("content", "")
                elif isinstance(branch_content, str):
                    text = branch_content
                else:
                    text = ""

                if text:
                    content.append(text)
                else:
                    # 回退到原骨架的段落内容
                    section_content = section.get("content", "")
                    content.append(section_content or f"[请填写{section_name}内容]")

            # --------------------------------------------------
            # replace_style 模式：保持骨架（L1/L3-L4）不变，替换策略和表达
            # --------------------------------------------------
            elif fission_mode == "replace_style":
                # 开头段落：使用新策略生成开场
                if section_name in ("开头", "痛点共鸣"):
                    new_hook = l2_data.get("hook") or l5_data.get("hook")
                    content.append(new_hook or f"[请用「{new_strategy or '新策略'}」风格填写{section_name}]")
                # 主体段落：在新策略框架下重写表达
                elif section_name in ("主体", "卖点"):
                    style_content = l5_data.get(section_name) or l5_data.get("golden_sentences", [])
                    if isinstance(style_content, list) and style_content:
                        content.append(style_content[0])
                    elif isinstance(style_content, str) and style_content:
                        content.append(style_content)
                    else:
                        content.append(f"[请用「{new_strategy or '新策略'}」风格填写{section_name}]")
                # 结尾段落：在新策略框架下设计互动
                elif section_name in ("结尾", "互动"):
                    new_interaction = l2_data.get("interaction") or l5_data.get("interaction")
                    content.append(new_interaction or f"[请用「{new_strategy or '新策略'}」风格填写{section_name}]")
                else:
                    style_text = l5_data.get(section_name, "")
                    content.append(style_text or f"[请用「{new_strategy or '新策略'}」风格填写{section_name}]")

            content.append("")

    return "\n".join(content)


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

    # 按创建时间倒序排列，最新的在前
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
    return result


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
