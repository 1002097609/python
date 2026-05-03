"""
AI 辅助拆解服务（services/ai_dismantle.py）。

基于规则 + 关键词匹配的智能拆解引擎，根据素材标题和内容自动生成 L1-L5 五层拆解数据。
后续可替换为真实 LLM API 调用。

用法：
    from backend.services.ai_dismantle import analyze_material
    result = analyze_material(title="...", content="...")
"""

import re
import random
from typing import Optional


# ============================================================
# 品类关键词映射
# ============================================================

CATEGORY_KEYWORDS = {
    "护肤": ["护肤", "面霜", "精华", "保湿", "抗老", "敏感肌", "油皮", "干皮", "防晒", "美白", "成分", "神经酰胺", "烟酰胺", "A醇", "胜肽", "玻色因"],
    "彩妆": ["彩妆", "粉底", "口红", "眼影", "化妆", "妆容", "底妆", "遮瑕", "腮红", "眉笔", "睫毛膏", "卸妆"],
    "零食": ["零食", "办公室零食", "速食", "奶茶", "巧克力", "坚果", "低卡零食", "减脂零食", "熬夜零食", "宿舍零食"],
    "母婴": ["母婴", "宝宝", "婴儿", "辅食", "奶瓶", "推车", "安全座椅", "红屁屁", "护臀", "产妇", "孕期"],
    "户外": ["户外", "露营", "徒步", "防晒", "登山", "钓鱼", "烧烤", "野餐", "装备"],
    "数码": ["数码", "手机", "耳机", "电脑", "键盘", "鼠标", "平板", "相机", "充电", "数据线", "手机摄影"],
    "家居": ["家居", "收纳", "清洁", "厨房", "租房", "改造", "好物", "神器", "台面", "小户型"],
    "服饰": ["服饰", "穿搭", "显瘦", "秋冬", "春夏", "大衣", "卫衣", "裤子", "胶囊衣橱", "微胖"],
    "宠物": ["宠物", "猫", "狗", "猫粮", "狗粮", "猫咪", "狗狗", "零食", "养猫", "养狗"],
    "健身": ["健身", "跑步", "瑜伽", "哑铃", "减肥", "减脂", "增肌", "体态", "久坐", "居家健身"],
    "食品饮料": ["奶茶", "咖啡", "饮料", "食品", "饮料", "手冲", "咖啡豆", "热量"],
    "家电": ["家电", "扫地机器人", "破壁机", "空气炸锅", "电饭煲", "小家电", "厨房电器"],
    "汽车": ["汽车", "买车", "选车", "车型", "驾照", "行车", "4S店"],
    "教育培训": ["教育", "培训", "Python", "学习", "考研", "网课", "编程", "零基础"],
    "金融理财": ["理财", "基金", "保险", "定投", "月光族", "存款", "股票"],
    "医疗健康": ["健康", "体检", "失眠", "助眠", "医疗", "养生", "熬夜"],
    "旅游出行": ["旅游", "出行", "机票", "酒店", "云南", "旅行", "攻略", "省钱"],
    "房产": ["房产", "买房", "租房", "二手房", "交易", "装修"],
    "游戏": ["游戏", "手游", "游戏本", "电竞", "玩家"],
    "文化娱乐": ["文化", "娱乐", "韩剧", "剧本杀", "追剧", "电影"],
    "企业服务": ["企业", "数字化", "SaaS", "工具", "团队", "效率", "远程办公"],
    "农业": ["农业", "种菜", "阳台种菜", "农产品", "电商"],
}


# ============================================================
# 策略关键词映射
# ============================================================

STRATEGY_KEYWORDS = {
    "共鸣型": ["踩坑", "痛点", "头疼", "困扰", "问题", "怎么办", "太难了", "烦"],
    "成分党": ["成分", "配方", "浓度", "含量", "表排名第", "实测", "数据"],
    "对比测评": ["对比", "测评", "横评", "实测", "打分", "排名", "TOP", "红黑榜", "哪款"],
    "悬念型": ["真相", "秘密", "你不知道", "才发现", "居然", "竟然", "没想到"],
    "教程型": ["教程", "攻略", "步骤", "流程", "方法", "技巧", "指南", "新手", "入门"],
    "清单型": ["清单", "TOP", "推荐", "必备", "大全", "合集", "盘点"],
    "红黑榜型": ["红黑榜", "千万别", "避坑", "踩雷", "推荐", "不推荐"],
    "种草型": ["种草", "好用", "回购", "闭眼入", "性价比", "天花板", "yyds"],
    "攻略型": ["攻略", "全攻略", "必看", "看这一篇", "一篇讲清楚"],
    "误区纠正型": ["误区", "错误", "千万别", "不要", "错", "踩坑"],
}


# ============================================================
# 结构模板（按内容类型）
# ============================================================

STRUCTURE_TEMPLATES = {
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
        {"name": "开头", "function": "背景引入+痛点共鸣", "ratio": 12},
        {"name": "红榜推荐", "function": "好物推荐+使用感受", "ratio": 40},
        {"name": "黑榜避雷", "function": "踩坑产品+原因分析", "ratio": 33},
        {"name": "总结", "function": "选购建议+互动引导", "ratio": 15},
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


# ============================================================
# L4 元素模板
# ============================================================

L4_TEMPLATES = {
    "测评对比型": {
        "title_formula": "XX测评：{topic}到底怎么选？",
        "hook": "实测了N款{topic}，差距竟然这么大",
        "transition": "但是重点来了",
        "interaction": "你用过哪款？评论区聊聊",
    },
    "教程步骤型": {
        "title_formula": "手把手教你{topic}，看完就会",
        "hook": "学会这{topic}技巧，直接省下一笔",
        "transition": "接下来是关键步骤",
        "interaction": "学会了的点赞，有问题的评论区问我",
    },
    "红黑榜型": {
        "title_formula": "{topic}红黑榜：这几款千万别买",
        "hook": "踩了N个坑才总结出的{topic}红黑榜",
        "transition": "先说红榜",
        "interaction": "你踩过哪些坑？评论区分享",
    },
    "攻略清单型": {
        "title_formula": "{topic}清单：不看后悔系列",
        "hook": "花了3天整理的{topic}全攻略",
        "transition": "直接上干货",
        "interaction": "觉得有用记得收藏，有问题评论区见",
    },
    "通用叙事型": {
        "title_formula": "{topic}：90%的人都不知道的真相",
        "hook": "关于{topic}，有些话我不得不说",
        "transition": "但是重点来了",
        "interaction": "你怎么看？评论区告诉我",
    },
}


# ============================================================
# L5 表达素材库
# ============================================================

GOLDEN_SENTENCES = [
    "这个细节99%的人都忽略了",
    "用了3年才发现这个方法",
    "性价比天花板",
    "闭眼入不会错",
    "回购了5次的好物",
    "用了就回不去了",
    "早知道早省钱",
    "这个真的一分钱一分货",
    "别再花冤枉钱了",
    "亲测有效才敢推荐",
    "这是我今年最值的投资",
    "效果惊艳到我",
    "原来差距这么大",
    "早知道就不踩坑了",
    "这才是正确的打开方式",
]

DATA_REFS = [
    "连续使用28天效果显著",
    "90%的用户反馈有效",
    "满意度评分4.8/5.0",
    "销量突破10万件",
    "复购率高达65%",
    "成分浓度提升30%",
    "实测保湿度提升40%",
    "用户好评率98%",
]

VISUAL_DESCS = [
    "产品全景展示",
    "使用前后对比",
    "细节特写镜头",
    "成分表放大展示",
    "使用手法演示",
    "效果数据可视化",
    "开箱第一视角",
    "场景化使用展示",
]


# ============================================================
# 情绪策略模板
# ============================================================

EMOTION_TEMPLATES = {
    "测评对比型": "好奇→对比震惊→价值认同→行动",
    "教程步骤型": "困惑→清晰→跃跃欲试→行动",
    "红黑榜型": "焦虑→信任→如释重负→行动",
    "攻略清单型": "选择困难→清晰→信任→收藏/行动",
    "通用叙事型": "共鸣→好奇→认同→行动",
}


# ============================================================
# 核心分析函数
# ============================================================

def _detect_category(title: str, content: str) -> str:
    """根据标题和内容检测品类"""
    text = (title + content).lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return "通用"


def _detect_strategies(title: str, content: str) -> list:
    """检测素材使用的策略标签"""
    text = title + content
    matched = []
    for strategy, keywords in STRATEGY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matched.append(strategy)
    return matched[:3] if matched else ["共鸣型"]


def _detect_structure_type(title: str, content: str) -> str:
    """检测内容结构类型"""
    text = title + content
    if any(kw in text for kw in ["测评", "横评", "对比", "红黑榜", "打分", "排名", "TOP"]):
        if "红黑" in text or "千万别" in text or "避坑" in text:
            return "红黑榜型"
        return "测评对比型"
    if any(kw in text for kw in ["教程", "攻略", "步骤", "流程", "手把手", "怎么"]):
        return "教程步骤型"
    if any(kw in text for kw in ["清单", "推荐", "合集", "盘点", "大全", "必看"]):
        return "攻略清单型"
    return "通用叙事型"


def _extract_topic(title: str, content: str) -> str:
    """从标题中提取主题"""
    # 清理标题中的 emoji 和特殊字符
    clean = re.sub(r'[^一-鿿\w\s：:，,。.！!？?、]', '', title)
    # 取前20字作为主题
    return clean[:20] if clean else "素材主题"


def _extract_core_point(title: str, content: str) -> str:
    """提取核心卖点"""
    # 从内容第一段提取
    first_para = content.split('\n')[0] if content else ""
    if len(first_para) > 10:
        return first_para[:50]
    # 从标题推断
    return f"关于{title[:15]}的核心洞察与实操方案"


def _generate_l4(topic: str, structure_type: str) -> dict:
    """生成 L4 元素"""
    template = L4_TEMPLATES.get(structure_type, L4_TEMPLATES["通用叙事型"])
    return {
        "title_formula": template["title_formula"].replace("{topic}", topic[:10]),
        "hook": template["hook"].replace("{topic}", topic[:10]),
        "transition": template["transition"],
        "interaction": template["interaction"],
    }


def _generate_l5() -> dict:
    """生成 L5 表达素材"""
    return {
        "golden_sentences": random.sample(GOLDEN_SENTENCES, k=min(3, len(GOLDEN_SENTENCES))),
        "data_refs": random.sample(DATA_REFS, k=min(2, len(DATA_REFS))),
        "visual_desc": random.sample(VISUAL_DESCS, k=min(3, len(VISUAL_DESCS))),
    }


def analyze_material(title: str, content: str, platform: str = "", category: str = "") -> dict:
    """
    AI 辅助拆解主函数。

    根据素材标题和内容，自动生成 L1-L5 五层拆解数据。

    参数：
        title:    素材标题
        content:  素材内容
        platform: 投放平台（可选）
        category: 品类（可选，不传则自动检测）

    返回：
        dict: L1-L5 拆解数据，格式与 DismantleCreate 一致
    """
    # 自动检测品类
    detected_category = category or _detect_category(title, content)

    # 提取主题和核心卖点
    topic = _extract_topic(title, content)
    core_point = _extract_core_point(title, content)

    # 检测策略
    strategies = _detect_strategies(title, content)

    # 检测结构类型
    structure_type = _detect_structure_type(title, content)
    structure = STRUCTURE_TEMPLATES[structure_type]

    # 情绪策略
    emotion = EMOTION_TEMPLATES.get(structure_type, EMOTION_TEMPLATES["通用叙事型"])

    # L4 元素
    l4 = _generate_l4(topic, structure_type)

    # L5 表达
    l5 = _generate_l5()

    return {
        "l1_topic": topic,
        "l1_core_point": core_point,
        "l2_strategy": strategies,
        "l2_emotion": emotion,
        "l3_structure": structure,
        "l4_elements": l4,
        "l5_expressions": l5,
        "_meta": {
            "detected_category": detected_category,
            "structure_type": structure_type,
            "platform": platform,
        }
    }
