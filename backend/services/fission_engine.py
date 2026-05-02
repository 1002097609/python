"""
裂变引擎核心模块（services/fission_engine.py）。

提供模板填充引擎，根据裂变模式和骨架结构，将新内容填充到骨架中生成最终文案。
从路由层抽离，供 seed_data.py 和 routes/fission.py 共用。

支持三种裂变模式：
  - replace_leaf（换叶子）:   替换 L1+L5，骨架不变
  - replace_branch（换枝杈）:  替换 L3+L4，主题不变
  - replace_style（换表达）:   替换 L2+L5，骨架不变
"""


def _distribute_items(items, count):
    """将 items 均匀分配到 count 个位置中。"""
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


def _build_leaf_block(section, section_name, new_topic, gs, dr, custom_hook,
                      custom_interaction, elements, l4_data, l2_data, strategy):
    """replace_leaf 模式：保持 L2-L4 骨架，替换主题和表达。"""
    section_template = section.get("template", "")
    name_lower = section_name.lower()
    is_hook = any(k in name_lower for k in ("开头", "痛点", "共鸣", "钩子", "引入"))
    is_body = any(k in name_lower for k in ("主体", "卖点", "核心", "论证", "展示", "测评"))
    is_ending = any(k in name_lower for k in ("结尾", "互动", "收尾", "号召", "转化"))
    is_transition = any(k in name_lower for k in ("转折", "过渡", "对比"))

    lines = []

    if section_template and new_topic:
        lines.append(f"  {_fill_template(section_template, new_topic, dr)}")

    if is_hook:
        hook = custom_hook or l4_data.get("hook") or elements.get("hook", "")
        if hook:
            lines.append(f"  {_fill_template(hook, new_topic, dr)}")
        elif not section_template:
            lines.append(f"  你是否也在为{new_topic}而烦恼？")

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
    is_hook = any(k in name_lower for k in ("开头", "痛点", "共鸣", "钩子"))
    is_body = any(k in name_lower for k in ("主体", "卖点", "核心", "论证", "展示"))
    is_ending = any(k in name_lower for k in ("结尾", "互动", "收尾", "号召"))

    lines = []
    strategy_tag = f"「{new_strategy}」" if new_strategy else ""

    if is_hook:
        hook = l2_data.get("hook") or custom_hook
        if hook:
            lines.append(f"  {hook}")
        else:
            lines.append(f"  请用{strategy_tag}风格撰写开头钩子")

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


def generate_output(fission_mode, structure, elements, strategy, new_topic, replacement) -> str:
    """
    模板填充引擎：根据裂变模式和骨架结构，将用户输入的新内容填充到骨架中生成最终文案。

    参数：
        fission_mode: 裂变模式（replace_leaf / replace_branch / replace_style）
        structure:    L3 结构层（段落列表）
        elements:     L4 元素层（标题公式、钩子句式等）
        strategy:     L2 策略描述
        new_topic:    新主题
        replacement:  自定义替换内容（可为空）

    返回：填充后的素材文案字符串
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

    # 预分配
    gs_per_section = _distribute_items(golden_sentences, section_count)
    dr_per_section = _distribute_items(data_refs, section_count)
    vd_per_section = _distribute_items(visual_descs, section_count)

    content_lines = []

    # 生成标题（主标题 + 备用标题变体）
    title_formula = l4_data.get("title_formula") or elements.get("title_formula", "")
    if title_formula and new_topic:
        title = _fill_template(title_formula, new_topic, data_refs[0] if data_refs else "")
        content_lines.append(f"【标题】{title}")
        content_lines.append("")
        # 备用标题变体
        if len(data_refs) > 1:
            alt_title = _fill_template(title_formula, new_topic, data_refs[1])
            if alt_title != title:
                content_lines.append(f"【备用标题】{alt_title}")
                content_lines.append("")
        # 如果没有数据引用，生成一个数字变体
        if not data_refs:
            content_lines.append(f"【备用标题】{_fill_template(title_formula, new_topic, '90%人不知道')}")
            content_lines.append("")

    # 生成正文段落
    for idx, section in enumerate(sections):
        section_name = section.get("name", f"段落{idx+1}")
        section_func = section.get("function", "")
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

        # 视觉描述整合到每个段落
        vd = vd_per_section[idx] if idx < len(vd_per_section) else ""
        if vd:
            content_lines.append(f"  📷 画面指导：{vd}")

        content_lines.append("")

    # 备用素材
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

    # 适用场景
    mode_desc_map = {
        "replace_leaf": "本素材采用「换叶子」策略，保留了原骨架的 L2-L4 结构，替换了主题和表达层。适用于同品类不同产品、或同产品不同卖点的快速变体生成。",
        "replace_branch": "本素材采用「换枝杈」策略，保留了原主题和策略层，替换了结构和元素层。适用于跨品类迁移、或同一主题的不同叙事角度。",
        "replace_style": "本素材采用「换表达」策略，保留了原骨架结构，替换了策略风格和表达层。适用于同一内容的不同情绪基调、或不同人群定位的变体。",
    }
    content_lines.append("【适用场景说明】")
    content_lines.append(f"  {mode_desc_map.get(fission_mode, '')}")
    if new_topic:
        content_lines.append(f"  核心主题：{new_topic}")
    if golden_sentences:
        content_lines.append(f"  核心金句：{golden_sentences[0]}")
    content_lines.append("")

    # 注意事项
    content_lines.append("【创作注意事项】")
    tips = [
        "以上文案为骨架填充结果，请根据实际产品信息和投放平台调性进行人工润色。",
        "标题建议 A/B 测试，可尝试备用标题变体。",
        "金句和数据引用请核实准确性，避免夸大宣传。",
        "画面指导仅供参考，实际拍摄/设计可根据素材风格调整。",
    ]
    if fission_mode == "replace_leaf":
        tips.append("换叶子模式下，注意新主题与骨架策略的契合度，避免生硬拼接。")
    elif fission_mode == "replace_branch":
        tips.append("换枝杈模式下，新结构需要重新验证逻辑流畅性，建议完整通读。")
    elif fission_mode == "replace_style":
        tips.append("换表达模式下，确保新策略风格与目标受众匹配，注意语气一致性。")
    for tip in tips:
        content_lines.append(f"  ✦ {tip}")
    content_lines.append("")

    return "\n".join(content_lines)
