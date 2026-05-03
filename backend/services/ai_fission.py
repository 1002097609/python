"""
AI 裂变生成服务（services/ai_fission.py）。

接入 LongCat-2.0-Preview 大模型，根据骨架 L1-L5 结构化数据 + 新主题/品类/风格，
端到端生成完整可投放的营销素材文案。

相比规则模板填充引擎（fission_engine.py）的区别：
  - 规则引擎：骨架占位符 + 字符串替换 → 文案框架（需人工润色）
  - AI 引擎：骨架语义描述 + 新内容 → 完整可投放文案（直接可用）

用法：
    from backend.services.ai_fission import generate_fission
    result = generate_fission(skeleton={...}, fission_mode="replace_leaf", new_topic="...")
"""

import json
import hashlib
import logging
import os
from collections import OrderedDict
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ============================================================
# AI 响应缓存（进程内 LRU，与 ai_dismantle 独立）
# ============================================================

_ai_fission_cache: OrderedDict = OrderedDict()
_ai_fission_cache_max_size = 128


def _cache_key(skeleton_id: int, fission_mode: str, new_topic: str,
               new_category: str, new_platform: str, new_style: str,
               replacement: dict, variant_idx: int) -> str:
    raw = f"{skeleton_id}|{fission_mode}|{new_topic}|{new_category}|{new_platform}|{new_style}|{json.dumps(replacement, sort_keys=True)}|{variant_idx}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _get_cached(key: str) -> Optional[dict]:
    if key in _ai_fission_cache:
        _ai_fission_cache.move_to_end(key)
        return _ai_fission_cache[key]
    return None


def _set_cache(key: str, value: dict):
    if key in _ai_fission_cache:
        _ai_fission_cache.move_to_end(key)
    _ai_fission_cache[key] = value
    if len(_ai_fission_cache) > _ai_fission_cache_max_size:
        _ai_fission_cache.popitem(last=False)


# ============================================================
# 熔断器（与 ai_dismantle 共用同一套）
# ============================================================

def _get_circuit():
    """从 ai_dismantle 导入共享的熔断器状态"""
    from .ai_dismantle import _circuit_is_open, _circuit_record_success, _circuit_record_failure
    return _circuit_is_open, _circuit_record_success, _circuit_record_failure


# ============================================================
# LongCat API 配置（与 ai_dismantle 共用）
# ============================================================

LONGCAT_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.longcat.chat/anthropic")
LONGCAT_API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
LONGCAT_MODEL = os.getenv("ANTHROPIC_MODEL", "LongCat-2.0-Preview")


# ============================================================
# 系统 Prompt 构建
# ============================================================

def _build_system_prompt() -> str:
    return """你是一个专业的营销素材创作专家，擅长根据内容骨架和新主题生成可直接投放的抖音/小红书营销文案。

你的任务是：给定一个内容骨架（L1-L5 结构化描述）和新的创作要求，生成完整、连贯、有吸引力的营销素材文案。

输出格式要求：
1. 输出合法 JSON，不要包含 markdown 代码块标记
2. JSON 结构如下：

{
  "title": "主标题（吸引眼球，20字以内）",
  "alt_titles": ["备用标题1", "备用标题2"],
  "content": "完整文案内容（按段落分，段落间用空行分隔）",
  "hook": "开头钩子句（前5秒必留人）",
  "golden_sentences": ["金句1", "金句2"],
  "visual_notes": ["画面指导1", "画面指导2"],
  "tags": ["标签1", "标签2", "标签3"],
  "_meta": {
    "match_score": 85,
    "match_reason": "骨架与主题的匹配度说明",
    "predicted_ctr_range": "1.5%-2.5%",
    "predicted_roi_range": "2.0x-3.5x",
    "platform_tone": "抖音快节奏/小红书种草风 等平台调性说明"
  }
}

创作要求：
1. 文案必须围绕新主题展开，与骨架策略保持一致
2. 开头钩子要强，前3秒抓住注意力
3. 段落过渡自然，逻辑流畅
4. 金句要有记忆点，适合传播
5. 结尾要有互动引导（评论/点赞/关注）
6. 根据投放平台调整语气和节奏
7. 数据引用要合理，不夸大"""


def _build_user_prompt(skeleton: dict, fission_mode: str, new_topic: str,
                       new_category: str, new_platform: str, new_style: str,
                       replacement: dict) -> str:
    """根据骨架数据和用户输入构建 user prompt"""

    # 裂变模式说明
    mode_desc = {
        "replace_leaf": "「换叶子」模式：保留原骨架的策略层(L2)+结构层(L3)+元素层(L4)，替换主题(L1)和表达(L5)。新文案需要将原骨架的叙事结构迁移到新主题上。",
        "replace_branch": "「换枝杈」模式：保留原主题和策略，替换结构(L3)和元素(L4)。新文案需要用新的结构方式重新组织内容。",
        "replace_style": "「换表达」模式：保留骨架结构，替换策略风格(L2)和表达(L5)。新文案需要用新的情绪基调和表达方式重写。",
    }

    lines = [f"请根据以下内容骨架和创作要求，生成完整的营销素材文案。\n"]
    lines.append(f"【裂变模式】{fission_mode} — {mode_desc.get(fission_mode, '')}\n")

    # 骨架数据
    lines.append("【内容骨架】")
    if skeleton.get("strategy_desc"):
        lines.append(f"  策略描述：{skeleton['strategy_desc']}")

    structure = skeleton.get("structure_json", [])
    if structure:
        lines.append(f"  结构模板（{len(structure)} 个段落）：")
        for i, sec in enumerate(structure):
            if isinstance(sec, dict):
                lines.append(f"    {i+1}. {sec.get('name', '段落')} — {sec.get('function', '')}（占比 {sec.get('ratio', 0)}%）")
                if sec.get("template"):
                    lines.append(f"       模板：{sec['template']}")
            else:
                lines.append(f"    {i+1}. {sec}")

    elements = skeleton.get("elements_json", {})
    if elements:
        lines.append(f"  元素模块：")
        if elements.get("title_formula"):
            lines.append(f"    标题公式：{elements['title_formula']}")
        if elements.get("hook"):
            lines.append(f"    钩子句式：{elements['hook']}")
        if elements.get("transition"):
            lines.append(f"    转折方式：{elements['transition']}")
        if elements.get("interaction"):
            lines.append(f"    互动设计：{elements['interaction']}")

    # 效果参考
    if skeleton.get("avg_roi") or skeleton.get("avg_ctr"):
        lines.append(f"  历史效果：",)
        if skeleton.get("avg_roi"):
            lines.append(f"    平均 ROI: {skeleton['avg_roi']}x")
        if skeleton.get("avg_ctr"):
            lines.append(f"    平均 CTR: {skeleton['avg_ctr']}%")

    lines.append("")

    # 新内容要求
    lines.append("【创作要求】")
    lines.append(f"  新主题：{new_topic}")
    if new_category:
        lines.append(f"  新品类：{new_category}")
    if new_platform:
        lines.append(f"  投放平台：{new_platform}")
    if new_style:
        lines.append(f"  风格要求：{new_style}")

    # 替换内容
    if replacement:
        l5 = replacement.get("L5", {})
        if l5.get("golden_sentences"):
            lines.append(f"  指定金句：{' | '.join(l5['golden_sentences'])}")
        if l5.get("data_refs"):
            lines.append(f"  数据引用：{' | '.join(l5['data_refs'])}")
        if l5.get("visual_desc"):
            lines.append(f"  视觉要求：{' | '.join(l5['visual_desc'])}")

        l4 = replacement.get("L4", {})
        if l4.get("hook"):
            lines.append(f"  自定义钩子：{l4['hook']}")
        if l4.get("transition"):
            lines.append(f"  自定义转折：{l4['transition']}")
        if l4.get("interaction"):
            lines.append(f"  自定义互动：{l4['interaction']}")

    lines.append("")
    lines.append("请直接输出 JSON，不要包含任何解释性文字。")

    return "\n".join(lines)


# ============================================================
# LongCat API 调用
# ============================================================

def _call_longcat_ai_fission(skeleton: dict, fission_mode: str, new_topic: str,
                              new_category: str, new_platform: str, new_style: str,
                              replacement: dict, variant_idx: int = 0) -> Optional[dict]:
    """调用 LongCat API 进行 AI 裂变生成"""
    if not LONGCAT_API_KEY:
        logger.warning("LONGCAT_API_KEY 未配置，跳过 AI 裂变调用")
        return None

    # 熔断器检查
    circuit_is_open, circuit_success, circuit_failure = _get_circuit()
    if circuit_is_open():
        logger.warning("熔断器已打开，跳过 AI 裂变调用")
        return None

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        skeleton=skeleton, fission_mode=fission_mode, new_topic=new_topic,
        new_category=new_category, new_platform=new_platform, new_style=new_style,
        replacement=replacement,
    )

    # 变体差异化：通过调整 temperature 和提示词实现
    if variant_idx > 0:
        user_prompt += f"\n\n【变体要求】这是第 {variant_idx + 1} 个变体，请在保持骨架结构的前提下，采用不同的表达方式、语气风格或切入角度，与前面已生成的变体有所区别。"

    try:
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{LONGCAT_BASE_URL}/v1/messages",
                headers={
                    "Authorization": f"Bearer {LONGCAT_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": LONGCAT_MODEL,
                    "max_tokens": 4096,
                    "temperature": 0.7 + variant_idx * 0.1,  # 变体递增温度增加多样性
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )

            if response.status_code != 200:
                logger.error(f"LongCat AI 裂变返回 {response.status_code}: {response.text[:500]}")
                circuit_failure()
                return None

            resp_data = response.json()
            text_content = ""
            for block in resp_data.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")

            if not text_content:
                logger.error("LongCat AI 裂变返回空内容")
                circuit_failure()
                return None

            # 解析 JSON
            json_str = text_content.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]
                json_str = json_str.rsplit("```", 1)[0]
                json_str = json_str.strip()

            result = json.loads(json_str)
            logger.info(f"LongCat AI 裂变成功: title={result.get('title', '?')[:20]}")
            circuit_success()
            return result

    except httpx.TimeoutException:
        logger.error("LongCat AI 裂变调用超时")
        circuit_failure()
        return None
    except json.JSONDecodeError as e:
        logger.error(f"LongCat AI 裂变返回 JSON 解析失败: {e}")
        circuit_failure()
        return None
    except Exception as e:
        logger.error(f"LongCat AI 裂变调用异常: {e}")
        circuit_failure()
        return None


# ============================================================
# 规则兜底（AI 不可用时）
# ============================================================

def _rule_based_fission(skeleton: dict, fission_mode: str, new_topic: str,
                        new_category: str, new_platform: str, new_style: str,
                        replacement: dict) -> dict:
    """规则引擎兜底：调用现有的 fission_engine 生成结果"""
    from .fission_engine import generate_output

    structure = skeleton.get("structure_json", [])
    elements = skeleton.get("elements_json", {})
    strategy = skeleton.get("strategy_desc", "")

    output_content = generate_output(
        fission_mode=fission_mode,
        structure=structure,
        elements=elements,
        strategy=strategy,
        new_topic=new_topic,
        replacement=replacement,
    )

    # 提取标题
    title = f"{new_topic} | 营销素材"
    title_formula = (elements or {}).get("title_formula", "")
    if title_formula and new_topic:
        import re
        title = re.sub(r'\{topic\}', new_topic, title_formula)
        title = re.sub(r'\{data\}', '', title).strip()

    l5 = replacement.get("L5", {}) if replacement else {}
    golden_sentences = l5.get("golden_sentences", [])
    visual_descs = l5.get("visual_desc", [])

    base_roi = float(skeleton.get("avg_roi") or 2.0)
    base_ctr = float(skeleton.get("avg_ctr") or 1.5)
    factors = {"replace_leaf": 0.85, "replace_branch": 0.65, "replace_style": 0.70}
    factor = factors.get(fission_mode, 0.7)

    return {
        "title": title,
        "alt_titles": [],
        "content": output_content,
        "hook": (elements or {}).get("hook", ""),
        "golden_sentences": golden_sentences[:3],
        "visual_notes": visual_descs[:2],
        "tags": [new_category or "通用", new_platform or "全平台", fission_mode],
        "_meta": {
            "match_score": int(factor * 100),
            "match_reason": f"规则引擎兜底（{fission_mode} 模式，效果保留 {int(factor*100)}%）",
            "predicted_ctr_range": f"{base_ctr * factor * 0.9:.1f}%-{base_ctr * factor * 1.1:.1f}%",
            "predicted_roi_range": f"{base_roi * factor * 0.9:.1f}x-{base_roi * factor * 1.1:.1f}x",
            "platform_tone": f"{new_platform or '通用'}平台调性",
            "_fallback": True,
        },
    }


# ============================================================
# 主入口
# ============================================================

def generate_fission(skeleton: dict, fission_mode: str, new_topic: str,
                     new_category: str = "", new_platform: str = "",
                     new_style: str = "", replacement: dict = None,
                     variant_count: int = 1) -> list:
    """
    AI 裂变生成主函数。

    优先调用 LongCat-2.0-Preview 大模型端到端生成文案，
    API 不可用时降级为规则引擎（fission_engine.generate_output）。

    参数：
        skeleton:      骨架数据（含 structure_json, elements_json, strategy_desc, avg_roi, avg_ctr）
        fission_mode:  裂变模式（replace_leaf / replace_branch / replace_style）
        new_topic:      新主题
        new_category:  新品类（可选）
        new_platform:  新平台（可选）
        new_style:     新风格（可选）
        replacement:   替换内容（可选，含 L5/L4/L3/L2）
        variant_count: 生成变体数量（默认 1，最多 5）

    返回：
        list[dict]: 每个元素包含 title, content, hook, golden_sentences,
                    visual_notes, tags, _meta（含匹配度评分和效果预测）
    """
    replacement = replacement or {}
    variant_count = min(max(variant_count, 1), 5)
    results = []

    skeleton_id = skeleton.get("id", 0)

    for i in range(variant_count):
        # 检查缓存
        key = _cache_key(skeleton_id, fission_mode, new_topic, new_category,
                         new_platform, new_style, replacement, i)
        cached = _get_cached(key)
        if cached:
            logger.info(f"AI 裂变命中缓存 variant={i}")
            results.append(cached)
            continue

        # 优先调用 AI
        ai_result = _call_longcat_ai_fission(
            skeleton=skeleton, fission_mode=fission_mode, new_topic=new_topic,
            new_category=new_category, new_platform=new_platform, new_style=new_style,
            replacement=replacement, variant_idx=i,
        )

        if ai_result:
            _set_cache(key, ai_result)
            results.append(ai_result)
        else:
            # 降级：规则引擎
            logger.info(f"AI 裂变降级为规则引擎 variant={i}")
            rule_result = _rule_based_fission(
                skeleton=skeleton, fission_mode=fission_mode, new_topic=new_topic,
                new_category=new_category, new_platform=new_platform, new_style=new_style,
                replacement=replacement,
            )
            _set_cache(key, rule_result)
            results.append(rule_result)

    return results
