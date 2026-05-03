"""
AI 辅助拆解服务（services/ai_dismantle.py）。

接入 LongCat-2.0-Preview 大模型，根据素材标题和内容自动生成 L1-L5 五层拆解数据。

用法：
    from backend.services.ai_dismantle import analyze_material
    result = analyze_material(title="...", content="...")
"""

import json
import hashlib
import logging
import os
import time
from collections import OrderedDict
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ============================================================
# AI 响应缓存（进程内 LRU，逐出最旧条目）
# ============================================================

_ai_cache: OrderedDict = OrderedDict()
_ai_cache_max_size = 128


def _cache_key(title: str, content: str, platform: str, category: str) -> str:
    """根据输入参数生成缓存 key（基于内容 hash，相同内容不重复调用）"""
    raw = f"{title}|{content}|{platform}|{category}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _get_cached(key: str) -> Optional[dict]:
    """从缓存获取结果（LRU：命中时移到末尾）"""
    if key in _ai_cache:
        _ai_cache.move_to_end(key)
        return _ai_cache[key]
    return None


def _set_cache(key: str, value: dict):
    """写入缓存，超出容量时逐出最旧条目"""
    if key in _ai_cache:
        _ai_cache.move_to_end(key)
    _ai_cache[key] = value
    if len(_ai_cache) > _ai_cache_max_size:
        _ai_cache.popitem(last=False)  # 逐出最旧的条目


# ============================================================
# 熔断器（连续失败 N 次后直接降级，冷却期后重置）
# ============================================================

_circuit_fail_count = 0
_circuit_threshold = 3       # 连续失败次数阈值
_circuit_cooldown = 30       # 冷却期（秒）
_circuit_last_fail_time = 0  # 上次失败时间戳


def _circuit_is_open() -> bool:
    """检查熔断器是否打开（打开时直接降级，不走 AI）"""
    global _circuit_fail_count, _circuit_last_fail_time
    if _circuit_fail_count >= _circuit_threshold:
        elapsed = time.time() - _circuit_last_fail_time
        if elapsed < _circuit_cooldown:
            return True
        # 冷却期过后重置
        _circuit_fail_count = 0
    return False


def _circuit_record_success():
    """记录成功，重置失败计数"""
    global _circuit_fail_count
    _circuit_fail_count = 0


def _circuit_record_failure():
    """记录失败"""
    global _circuit_fail_count, _circuit_last_fail_time
    _circuit_fail_count += 1
    _circuit_last_fail_time = time.time()

# ============================================================
# LongCat API 配置
# ============================================================

LONGCAT_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.longcat.chat/anthropic")
LONGCAT_API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
LONGCAT_MODEL = os.getenv("ANTHROPIC_MODEL", "LongCat-2.0-Preview")


# ============================================================
# 系统 Prompt
# ============================================================

SYSTEM_PROMPT = """你是一个专业的营销素材拆解专家，擅长将抖音/小红书等平台的营销素材按五层模型进行结构化拆解。

请根据用户提供的素材标题和内容，按以下 JSON 格式输出拆解结果：

{
  "l1_topic": "主题（素材讲什么，一句话概括）",
  "l1_core_point": "核心卖点（最想传达的一句话）",
  "l2_strategy": ["策略标签1", "策略标签2"],
  "l2_emotion": "情绪策略（如：焦虑→信任→行动）",
  "l3_structure": [
    {"name": "段落名", "function": "功能说明", "ratio": 占比数字},
    ...
  ],
  "l4_elements": {
    "title_formula": "标题公式",
    "hook": "钩子句式",
    "transition": "转折方式",
    "interaction": "互动设计"
  },
  "l5_expressions": {
    "golden_sentences": ["金句1", "金句2", "金句3"],
    "data_refs": ["数据引用1", "数据引用2"],
    "visual_desc": ["视觉描述1", "视觉描述2"]
  },
  "_meta": {
    "detected_category": "检测到的品类",
    "structure_type": "结构类型（测评对比型/教程步骤型/红黑榜型/攻略清单型/通用叙事型）"
  }
}

策略标签可选：共鸣型、成分党、对比测评、悬念型、教程型、清单型、红黑榜型、种草型、攻略型、误区纠正型

要求：
1. 必须输出合法 JSON，不要包含 markdown 代码块标记
2. l3_structure 的 ratio 总和应为 100
3. 所有内容必须基于素材实际内容分析，不要凭空编造
4. golden_sentences 应该是素材中实际出现或可以推导的金句风格表达
5. 如果素材中没有明确数据，data_refs 可以填写合理的行业通用数据"""


# ============================================================
# 规则引擎（API 不可用时的兜底方案）
# ============================================================

def _detect_structure_type(text: str) -> tuple:
    """
    基于关键词+结构模式识别素材结构类型。
    返回 (structure_type, confidence) 其中 confidence 为 high/medium/low。
    """
    scores = {
        "测评对比型": 0,
        "教程步骤型": 0,
        "红黑榜型": 0,
        "攻略清单型": 0,
    }

    # 关键词打分
    keyword_scores = {
        "测评对比型": ["测评", "横评", "对比", "打分", "评测试", "哪个好", "vs", "VS"],
        "教程步骤型": ["教程", "步骤", "攻略", "手把手", "怎么做", "教程", "教学", "教程分享"],
        "红黑榜型": ["红黑榜", "千万别", "避坑", "踩雷", "烂脸", "智商税", "不要买"],
        "攻略清单型": ["清单", "推荐", "合集", "盘点", "大全", "TOP", "排行", "榜单"],
    }
    for stype, kws in keyword_scores.items():
        for kw in kws:
            if kw in text:
                scores[stype] += 1

    # 结构模式识别：多个强信号词组合提升置信度
    # 测评对比型：同时出现"对比"+"打分/排名"
    if scores["测评对比型"] >= 2:
        confidence = "high"
    elif scores["测评对比型"] == 1:
        confidence = "medium"
    else:
        confidence = None

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return "通用叙事型", "low"

    # 根据得分确定置信度
    if best_score >= 2:
        return best_type, "high"
    return best_type, "medium"


def _rule_based_analyze(title: str, content: str, platform: str = "", category: str = "") -> dict:
    """基于规则的拆解（兜底方案），带置信度标记。"""
    import random

    text = title + content

    # 品类检测
    category_keywords = {
        "护肤": ["护肤", "面霜", "精华", "保湿", "抗老", "敏感肌", "防晒", "美白", "成分"],
        "彩妆": ["彩妆", "粉底", "口红", "眼影", "化妆", "妆容", "底妆"],
        "零食": ["零食", "速食", "奶茶", "巧克力", "坚果", "低卡"],
        "母婴": ["母婴", "宝宝", "婴儿", "辅食", "奶瓶", "推车"],
        "户外": ["户外", "露营", "徒步", "登山", "钓鱼"],
        "数码": ["数码", "手机", "耳机", "电脑", "键盘", "平板"],
        "家居": ["家居", "收纳", "清洁", "厨房", "租房", "改造"],
        "服饰": ["服饰", "穿搭", "显瘦", "大衣", "卫衣", "裤子"],
        "宠物": ["宠物", "猫", "狗", "猫粮", "狗粮"],
        "健身": ["健身", "跑步", "瑜伽", "哑铃", "减肥", "减脂"],
    }
    detected_cat = "通用"
    for cat, kws in category_keywords.items():
        if any(kw in text for kw in kws):
            detected_cat = cat
            break

    # 策略检测
    strategies = []
    if any(kw in text for kw in ["踩坑", "痛点", "问题", "怎么办"]): strategies.append("共鸣型")
    if any(kw in text for kw in ["成分", "配方", "浓度"]): strategies.append("成分党")
    if any(kw in text for kw in ["对比", "测评", "横评", "打分"]): strategies.append("对比测评")
    if any(kw in text for kw in ["教程", "步骤", "攻略", "怎么"]): strategies.append("教程型")
    if any(kw in text for kw in ["清单", "推荐", "合集", "盘点"]): strategies.append("清单型")
    if any(kw in text for kw in ["红黑榜", "千万别", "避坑"]): strategies.append("红黑榜型")
    if any(kw in text for kw in ["种草", "好用", "回购", "闭眼入"]): strategies.append("种草型")
    if not strategies: strategies = ["共鸣型"]

    # 结构类型 + 置信度
    structure_type, confidence = _detect_structure_type(text)

    structure_map = {
        "测评对比型": [
            {"name": "开头", "function": "痛点共鸣+选题引入", "ratio": 15},
            {"name": "产品/方案展示", "function": "逐一测评+数据对比", "ratio": 55},
            {"name": "总结推荐", "function": "排名/推荐+引导行动", "ratio": 30},
        ],
        "教程步骤型": [
            {"name": "开头", "function": "效果展示+价值承诺", "ratio": 10},
            {"name": "步骤拆解", "function": "分步讲解+注意事项", "ratio": 65},
            {"name": "结尾", "function": "总结+互动引导", "ratio": 25},
        ],
        "红黑榜型": [
            {"name": "开头", "function": "痛点共鸣+避坑引入", "ratio": 15},
            {"name": "红黑榜正文", "function": "逐一点评+数据支撑", "ratio": 55},
            {"name": "总结推荐", "function": "推荐清单+引导行动", "ratio": 30},
        ],
        "攻略清单型": [
            {"name": "开头", "function": "痛点引入+价值承诺", "ratio": 12},
            {"name": "清单正文", "function": "逐条推荐+核心卖点", "ratio": 63},
            {"name": "结尾", "function": "总结+互动+关注引导", "ratio": 25},
        ],
        "通用叙事型": [
            {"name": "开头", "function": "钩子引入+痛点共鸣", "ratio": 15},
            {"name": "主体", "function": "核心价值输出", "ratio": 60},
            {"name": "结尾", "function": "总结+引导行动", "ratio": 25},
        ],
    }

    emotion_map = {
        "测评对比型": "好奇→对比震惊→价值认同→行动",
        "教程步骤型": "困惑→清晰→跃跃欲试→行动",
        "红黑榜型": "焦虑→信任→如释重负→行动",
        "攻略清单型": "选择困难→清晰→信任→收藏/行动",
        "通用叙事型": "共鸣→好奇→认同→行动",
    }

    golden_pool = ["这个细节99%的人都忽略了", "用了3年才发现这个方法", "性价比天花板",
                   "闭眼入不会错", "回购了5次的好物", "用了就回不去了", "早知道早省钱",
                   "别再花冤枉钱了", "亲测有效才敢推荐", "效果惊艳到我"]
    data_pool = ["连续使用28天效果显著", "90%的用户反馈有效", "满意度评分4.8/5.0",
                 "销量突破10万件", "复购率高达65%", "用户好评率98%"]
    visual_pool = ["产品全景展示", "使用前后对比", "细节特写镜头", "成分表放大展示",
                   "使用手法演示", "效果数据可视化", "开箱第一视角"]

    import re
    clean_title = re.sub(r'[^一-鿿\w\s：:，,。.！!？?、]', '', title)
    topic = clean_title[:20] if clean_title else "素材主题"
    first_para = content.split('\n')[0] if content else ""
    core_point = first_para[:50] if len(first_para) > 10 else f"关于{title[:15]}的核心洞察"

    return {
        "l1_topic": topic,
        "l1_core_point": core_point,
        "l2_strategy": strategies[:3],
        "l2_emotion": emotion_map.get(structure_type, "共鸣→好奇→认同→行动"),
        "l3_structure": structure_map[structure_type],
        "l4_elements": {
            "title_formula": f"{topic}：90%的人都不知道的真相",
            "hook": f"关于{topic}，有些话我不得不说",
            "transition": "但是重点来了",
            "interaction": "你怎么看？评论区告诉我",
        },
        "l5_expressions": {
            "golden_sentences": random.sample(golden_pool, k=min(3, len(golden_pool))),
            "data_refs": random.sample(data_pool, k=min(2, len(data_pool))),
            "visual_desc": random.sample(visual_pool, k=min(3, len(visual_pool))),
        },
        "_meta": {
            "detected_category": category or detected_cat,
            "structure_type": structure_type,
            "platform": platform,
            "_fallback": True,
            "_confidence": confidence,
            "_needs_review": confidence == "low",
        }
    }


# ============================================================
# LongCat API 调用
# ============================================================

def _call_longcat(title: str, content: str, platform: str = "", category: str = "") -> Optional[dict]:
    """调用 LongCat API 进行 AI 拆解（带熔断保护）"""
    if not LONGCAT_API_KEY:
        logger.warning("LONGCAT_API_KEY 未配置，跳过 AI 调用")
        return None

    # 熔断器检查：连续失败 N 次后直接降级
    if _circuit_is_open():
        logger.warning("熔断器已打开，跳过 AI 调用，直接使用规则降级")
        return None

    user_message = f"请拆解以下营销素材：\n\n【标题】{title}"
    if platform:
        user_message += f"\n【平台】{platform}"
    if category:
        user_message += f"\n【品类】{category}"
    user_message += f"\n\n【内容】\n{content}"

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
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )

            if response.status_code != 200:
                logger.error(f"LongCat API 返回 {response.status_code}: {response.text[:500]}")
                _circuit_record_failure()
                return None

            resp_data = response.json()
            # 提取 text 内容
            text_content = ""
            for block in resp_data.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")

            if not text_content:
                logger.error("LongCat API 返回空内容")
                _circuit_record_failure()
                return None

            # 解析 JSON（去除可能的 markdown 代码块）
            json_str = text_content.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]  # 去掉 ```json
                json_str = json_str.rsplit("```", 1)[0]  # 去掉结尾 ```
                json_str = json_str.strip()

            result = json.loads(json_str)
            logger.info(f"LongCat AI 拆解成功: {result.get('_meta', {}).get('structure_type', '?')}")
            _circuit_record_success()
            return result

    except httpx.TimeoutException:
        logger.error("LongCat API 调用超时")
        _circuit_record_failure()
        return None
    except json.JSONDecodeError as e:
        logger.error(f"LongCat 返回 JSON 解析失败: {e}")
        _circuit_record_failure()
        return None
    except Exception as e:
        logger.error(f"LongCat API 调用异常: {e}")
        _circuit_record_failure()
        return None


# ============================================================
# 主入口
# ============================================================

def analyze_material(title: str, content: str, platform: str = "", category: str = "") -> dict:
    """
    AI 辅助拆解主函数。

    优先调用 LongCat-2.0-Preview 大模型，API 不可用时降级为规则引擎。

    参数：
        title:    素材标题
        content:  素材内容
        platform: 投放平台（可选）
        category: 品类（可选，不传则自动检测）

    返回：
        dict: L1-L5 拆解数据，格式与 DismantleCreate 一致
    """
    # 检查缓存
    key = _cache_key(title, content, platform, category)
    cached = _get_cached(key)
    if cached:
        logger.info("AI 拆解命中缓存")
        return cached

    # 优先调用 LongCat AI
    ai_result = _call_longcat(title, content, platform, category)
    if ai_result:
        # 确保 _meta 存在
        if "_meta" not in ai_result:
            ai_result["_meta"] = {}
        ai_result["_meta"]["platform"] = platform
        if not ai_result["_meta"].get("detected_category"):
            ai_result["_meta"]["detected_category"] = category or "通用"
        # AI 结果标记为 high 置信度（AI 直接输出）
        ai_result["_meta"]["_confidence"] = "high"
        ai_result["_meta"]["_needs_review"] = False
        ai_result["_meta"]["_fallback"] = False
        _set_cache(key, ai_result)
        return ai_result

    # 降级：规则引擎
    logger.info("使用规则引擎兜底拆解")
    result = _rule_based_analyze(title, content, platform, category)
    _set_cache(key, result)
    return result
