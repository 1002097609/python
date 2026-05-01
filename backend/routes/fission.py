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


def _distribute_items(items, count):
    """将 items 均匀分配到 count 个位置中。例如 items=[a,b,c], count=5 -> [a, b, c, a, b]"""
    if not items or count <= 0:
        return []
    result = []
    for i in range(count):
        result.append(items[i % len(items)])
    return result


def _fill_template(template, new_topic, data_ref=""):
    """填充模板句式：将占位符 {topic}、{data} 替换为实际内容。"""
    result = template.replace("{topic}", new_topic)
    result = result.replace("{data}", data_ref)
    return result


def _generate_output(fission_mode, structure, elements, strategy, new_topic, replacement) -> str:
    """
    模板填充引擎：根据裂变模式和骨架结构，将用户输入的新内容填充到骨架中生成最终文案。

    设计原则：
      - 尽可能多地利用用户输入的数据（金句、数据引用、视觉描述等）
      - 金句按段落数量均匀分配，避免只用第一条
      - 数据引用作为支撑数据嵌入到相关段落中
      - 视觉描述生成独立的画面指导
      - 骨架中的 template 字段作为句式模板，用新主题和数据填充

    不同裂变模式：
      - replace_leaf:   保持 L2-L4 骨架，替换 L1（主题）和 L5（表达）
      - replace_branch: 保持 L1-L2 主题策略，替换 L3（结构）和 L4（元素）
      - replace_style:  保持 L1/L3-L4 骨架，替换 L2（策略）和 L5（表达）

    返回：填充后的素材文案字符串（含标题、正文段落和视觉指导）
    """
    import json as _json

    # 数据准备
    l5_data = replacement.get("L5", {}) if replacement else {}
    l4_data = replacement.get("L4", {}) if replacement else {}
    l3_data = replacement.get("L3", {}) if replacement else {}
    l2_data = replacement.get("L2", {}) if replacement else {}

    golden_sentences = l5_data.get("golden_sentences", [])
    data_refs = l5_data.get("data_refs", [])
    visual_descs = l5_data.get("visual_desc", [])
    custom_hook = l5_data.get("hook") or l4_data.get("hook")
    custom_interaction = l5_data.get("interaction") or l4_data.get("interaction")
    new_strategy = l2_data.get("strategy_desc", strategy)

    # 解析 elements 和 structure
    if isinstance(elements, str):
        elements = _json.loads(elements) or {}
    elements = elements or {}
    if isinstance(structure, str):
        structure = _json.loads(structure) or []
    sections = structure if isinstance(structure, list) else []
    section_count = len(sections)

    # 预分配：将金句、数据、视觉描述均匀分配到各段落
    gs_per_section = _distribute_items(golden_sentences, section_count)
    dr_per_section = _distribute_items(data_refs, section_count)
    vd_per_section = _distribute_items(visual_descs, section_count)

    content_lines = []

    # 生成标题
    title_formula = l4_data.get("title_formula") or elements.get("title_formula", "")
    if title_formula and new_topic:
        title = _fill_template(title_formula, new_topic, data_refs[0] if data_refs else "")
        content_lines.append(f"【标题】{title}")
        content_lines.append("")

    # 生成正文段落
    for idx, section in enumerate(sections):
        section_name = section.get("name", f"段落{idx+1}")
        section_func = section.get("function", "")
        section_template = section.get("template", "")
        section_ratio = section.get("ratio", 0)

        content_lines.append(f"【{section_name} — {section_func}】（占比 {section_ratio}%）")

        paragraph_blocks = []

        if fission_mode == "replace_leaf":
            block = _build_leaf_block(
                section=section, section_name=section_name, new_topic=new_topic,
                gs=gs_per_section[idx] if idx < len(gs_per_section) else "",
                dr=dr_per_section[idx] if idx < len(dr_per_section) else "",
                custom_hook=custom_hook, custom_interaction=custom_interaction,
                elements=elements, l4_data=l4_data, l2_data=l2_data, strategy=strategy,
            )
            if block:
                paragraph_blocks.append(block)

        elif fission_mode == "replace_branch":
            block = _build_branch_block(
                section=section, section_name=section_name,
                l3_data=l3_data,
                gs=gs_per_section[idx] if idx < len(gs_per_section) else "",
                dr=dr_per_section[idx] if idx < len(dr_per_section) else "",
            )
            if block:
                paragraph_blocks.append(block)

        elif fission_mode == "replace_style":
            block = _build_style_block(
                section_name=section_name,
                new_strategy=new_strategy or (strategy or "新策略"),
                gs=gs_per_section[idx] if idx < len(gs_per_section) else "",
                dr=dr_per_section[idx] if idx < len(dr_per_section) else "",
                custom_hook=custom_hook, custom_interaction=custom_interaction,
                l2_data=l2_data,
            )
            if block:
                paragraph_blocks.append(block)

        content_lines.extend(paragraph_blocks)

        # 视觉描述
        vd = vd_per_section[idx] if idx < len(vd_per_section) else ""
        if vd:
            content_lines.append(f"  📷 画面指导：{vd}")

        content_lines.append("")

    # 备用素材汇总
    used_gs = min(len(gs_per_section), section_count)
    remaining_gs = golden_sentences[used_gs:] if len(golden_sentences) > used_gs else []
    used_dr = min(len(dr_per_section), section_count)
    remaining_dr = data_refs[used_dr:] if len(data_refs) > used_dr else []
    used_vd = min(len(vd_per_section), section_count)
    remaining_vd = visual_descs[used_vd:] if len(visual_descs) > used_vd else []

    if remaining_gs or remaining_dr or remaining_vd:
        content_lines.append("【备用素材 — 可在上述段落中灵活替换】")
        if remaining_gs:
            content_lines.append(f"  💬 额外金句：{' | '.join(remaining_gs)}")
        if remaining_dr:
            content_lines.append(f"  📊 额外数据：{' | '.join(remaining_dr)}")
        if remaining_vd:
            content_lines.append(f"  📷 额外画面：{' | '.join(remaining_vd)}")
        content_lines.append("")

    return "\n".join(content_lines)


def _build_leaf_block(section, section_name, new_topic, gs, dr, custom_hook,
                      custom_interaction, elements, l4_data, l2_data, strategy):
    """replace_leaf 模式：保持 L2-L4 骨架，替换主题和表达。"""
    section_template = section.get("template", "")
    name_lower = section_name.lower()
    is_hook = any(k in name_lower for k in ("开头", "痛点", "共鸣", "钒子", "引入"))
    is_body = any(k in name_lower for k in ("主体", "卖点", "核心", "论证", "展示", "测评"))
    is_ending = any(k in name_lower for k in ("结尾", "互动", "收尾", "号召", "转化"))
    is_transition = any(k in name_lower for k in ("转折", "过渡", "对比"))

    lines = []

    # 模板句式填充
    if section_template and new_topic:
        lines.append(f"  {_fill_template(section_template, new_topic, dr)}")

    if is_hook:
        hook = custom_hook or l4_data.get("hook") or elements.get("hook", "")
        if hook:
            lines.append(f"  {_fill_template(hook, new_topic, dr)}")
        elif not section_template:
            lines.append(f"  你是否也在为{new_topic}而烦惱？")

    elif is_body:
        if gs:
            lines.append(f"  💬 {gs}")
        if dr:
            lines.append(f"  📊 数据支撑：{dr}")
        transition = l4_data.get("transition") or elements.get("transition", "")
        if transition:
            lines.append(f"  🔀 {_fill_template(transition, new_topic, dr)}")
        if not lines and strategy:
            lines.append(f"  策略参考：{strategy}")

    elif is_transition:
        transition = l4_data.get("transition") or elements.get("transition", "")
        if transition:
            lines.append(f"  {_fill_template(transition, new_topic, dr)}")
        if gs:
            lines.append(f"  💬 {gs}")

    elif is_ending:
        interaction = custom_interaction or l4_data.get("interaction") or elements.get("interaction", "")
        if interaction:
            lines.append(f"  {_fill_template(interaction, new_topic, dr)}")
        if gs:
            lines.append(f"  💬 {gs}")
        if not interaction and not gs:
            lines.append(f"  评论区告诉我你对{new_topic}的看法！")

    else:
        if gs:
            lines.append(f"  💬 {gs}")
        elif dr:
            lines.append(f"  📊 {dr}")
        elif not section_template:
            lines.append(f"  [请围绕「{new_topic}」填写{section_name}内容]")

    return "\n".join(lines) if lines else ""


def _build_branch_block(section, section_name, l3_data, gs, dr):
    """replace_branch 模式：保持主题策略不变，替换结构和元素。"""
    lines = []
    branch_content = l3_data.get(section_name, {})

    if isinstance(branch_content, dict):
        text = branch_content.get("content", "")
    elif isinstance(branch_content, str):
        text = branch_content
    else:
        text = ""

    if text:
        lines.append(f"  {text}")
    else:
        section_content = section.get("content", "")
        if section_content:
            lines.append(f"  {section_content}")
        else:
            lines.append(f"  [请填写新的{section_name}内容]")

    if gs:
        lines.append(f"  💬 {gs}")
    if dr:
        lines.append(f"  📊 数据支撑：{dr}")

    return "\n".join(lines) if lines else ""


def _build_style_block(section_name, new_strategy, gs, dr, custom_hook,
                       custom_interaction, l2_data):
    """replace_style 模式：保持骨架不变，替换策略和表达。"""
    name_lower = section_name.lower()
    is_hook = any(k in name_lower for k in ("开头", "痛点", "共鸣", "钒子"))
    is_body = any(k in name_lower for k in ("主体", "卖点", "核心", "论证", "展示"))
    is_ending = any(k in name_lower for k in ("结尾", "互动", "收尾", "号召"))

    lines = []
    strategy_tag = f"「{new_strategy}」" if new_strategy else ""

    if is_hook:
        hook = l2_data.get("hook") or custom_hook
        if hook:
            lines.append(f"  {hook}")
        else:
            lines.append(f"  请用{strategy_tag}风格撰写开头钒子")

    elif is_body:
        if gs:
            lines.append(f"  💬 {gs}")
        if dr:
            lines.append(f"  📊 数据支撑：{dr}")
        if not gs and not dr:
            lines.append(f"  请用{strategy_tag}风格重写{section_name}内容")

    elif is_ending:
        interaction = l2_data.get("interaction") or custom_interaction
        if interaction:
            lines.append(f"  {interaction}")
        else:
            lines.append(f"  请用{strategy_tag}风格设计互动收尾")

    else:
        if gs:
            lines.append(f"  💬 {gs}")
        else:
            lines.append(f"  请用{strategy_tag}风格填写{section_name}")

    return "\n".join(lines) if lines else ""



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
