"""
选项数据初始化种子脚本

用途：
  将系统中所有下拉框的默认选项数据写入数据库。
  包括：平台、品类、风格、策略、骨架类型、裂变模式、金句、数据引用、视觉描述等。

用法：
  方式1（推荐）: python -c "from backend.seed_options import seed; seed()"
  方式2: python backend/seed_options.py

注意：
  seed() 会先清空 option 表中的所有现有数据，再重新插入默认值。
  如需保留已有数据并追加新数据，请直接调用 db.add(Option(**item)) 而不调用 delete。
"""
from backend.database import SessionLocal
from backend.models.option import Option


# ============================================================
# 默认选项数据
# ============================================================
# 按 group_key 分组，每个选项包含：
#   - group_key: 分组标识，对应前端 options 对象的 key
#   - label:    显示给用户看的文本
#   - value:    程序内部使用的实际值（通常与 label 相同，英文标识则不同）
#   - sort_order: 排序权重，数值越小越靠前
#
# 当前共 86 条数据，覆盖 9 个分组
# ============================================================

DEFAULT_OPTIONS = [
    # ----------------------------------------------------------
    # 平台 (platform) — 素材来源平台
    # ----------------------------------------------------------
    {"group_key": "platform", "label": "抖音", "value": "抖音", "sort_order": 1},
    {"group_key": "platform", "label": "小红书", "value": "小红书", "sort_order": 2},
    {"group_key": "platform", "label": "快手", "value": "快手", "sort_order": 3},

    # ----------------------------------------------------------
    # 品类 (category) — 素材所属商品品类
    # ----------------------------------------------------------
    {"group_key": "category", "label": "护肤", "value": "护肤", "sort_order": 1},
    {"group_key": "category", "label": "彩妆", "value": "彩妆", "sort_order": 2},
    {"group_key": "category", "label": "零食", "value": "零食", "sort_order": 3},
    {"group_key": "category", "label": "母婴", "value": "母婴", "sort_order": 4},
    {"group_key": "category", "label": "户外", "value": "户外", "sort_order": 5},

    # ----------------------------------------------------------
    # 风格 (style) — 素材内容风格类型
    # ----------------------------------------------------------
    {"group_key": "style", "label": "成分党", "value": "成分党", "sort_order": 1},
    {"group_key": "style", "label": "闺蜜聊天", "value": "闺蜜聊天", "sort_order": 2},
    {"group_key": "style", "label": "毒舌测评", "value": "毒舌测评", "sort_order": 3},
    {"group_key": "style", "label": "温柔种草", "value": "温柔种草", "sort_order": 4},
    {"group_key": "style", "label": "教程型", "value": "教程型", "sort_order": 5},
    {"group_key": "style", "label": "清单型", "value": "清单型", "sort_order": 6},
    {"group_key": "style", "label": "红黑榜型", "value": "红黑榜型", "sort_order": 7},
    {"group_key": "style", "label": "对比测评", "value": "对比测评", "sort_order": 8},
    {"group_key": "style", "label": "种草型", "value": "种草型", "sort_order": 9},
    {"group_key": "style", "label": "攻略型", "value": "攻略型", "sort_order": 10},

    # ----------------------------------------------------------
    # 策略标签 (strategy) — 素材使用的营销策略
    # ----------------------------------------------------------
    {"group_key": "strategy", "label": "共鸣型", "value": "共鸣型", "sort_order": 1},
    {"group_key": "strategy", "label": "成分党", "value": "成分党", "sort_order": 2},
    {"group_key": "strategy", "label": "对比测评", "value": "对比测评", "sort_order": 3},
    {"group_key": "strategy", "label": "悬念型", "value": "悬念型", "sort_order": 4},
    {"group_key": "strategy", "label": "教程型", "value": "教程型", "sort_order": 5},
    {"group_key": "strategy", "label": "清单型", "value": "清单型", "sort_order": 6},
    {"group_key": "strategy", "label": "红黑榜型", "value": "红黑榜型", "sort_order": 7},
    {"group_key": "strategy", "label": "种草型", "value": "种草型", "sort_order": 8},
    {"group_key": "strategy", "label": "攻略型", "value": "攻略型", "sort_order": 9},
    {"group_key": "strategy", "label": "误区纠正型", "value": "误区纠正型", "sort_order": 10},

    # ----------------------------------------------------------
    # 骨架类型 (skeleton_type) — 骨架的结构分类
    # ----------------------------------------------------------
    {"group_key": "skeleton_type", "label": "通用型", "value": "通用型", "sort_order": 1},
    {"group_key": "skeleton_type", "label": "测评对比型", "value": "测评对比型", "sort_order": 2},
    {"group_key": "skeleton_type", "label": "红黑榜型", "value": "红黑榜型", "sort_order": 3},
    {"group_key": "skeleton_type", "label": "误区纠正型", "value": "误区纠正型", "sort_order": 4},
    {"group_key": "skeleton_type", "label": "教程步骤型", "value": "教程步骤型", "sort_order": 5},

    # ----------------------------------------------------------
    # 裂变模式 (fission_mode) — 素材裂变的三种策略
    # ----------------------------------------------------------
    # replace_leaf:   换叶子 — 替换 L1(主题)+L5(表达)，骨架不变，效果保留约 85%
    # replace_style:  换表达 — 替换 L2(策略)+L5(表达)，骨架不变，效果保留约 70%
    # replace_branch: 换枝杈 — 替换 L3(结构)+L4(元素)，主题不变，效果保留约 65%
    {"group_key": "fission_mode", "label": "换叶子（同构异内容）", "value": "replace_leaf", "sort_order": 1},
    {"group_key": "fission_mode", "label": "换表达（跨风格移植）", "value": "replace_style", "sort_order": 2},
    {"group_key": "fission_mode", "label": "换枝杈（同内容异结构）", "value": "replace_branch", "sort_order": 3},

    # ----------------------------------------------------------
    # 金句预设 (golden_sentence) — 各行业常用营销金句
    # 覆盖护肤、母婴、零食、户外等品类
    # ----------------------------------------------------------
    {"group_key": "golden_sentence", "label": "含酒精香精的面霜，敏感肌千万别碰", "value": "含酒精香精的面霜，敏感肌千万别碰", "sort_order": 1},
    {"group_key": "golden_sentence", "label": "神经酰胺+胆固醇=屏障修复黄金搭档", "value": "神经酰胺+胆固醇=屏障修复黄金搭档", "sort_order": 2},
    {"group_key": "golden_sentence", "label": "硅酮填平毛孔是物理遮盖，不是真的收缩毛孔", "value": "硅酮填平毛孔是物理遮盖，不是真的收缩毛孔", "sort_order": 3},
    {"group_key": "golden_sentence", "label": "水杨酸控油还能祛痘，油痘肌亲妈", "value": "水杨酸控油还能祛痘，油痘肌亲妈", "sort_order": 4},
    {"group_key": "golden_sentence", "label": "第一口辅食一定是高铁米粉", "value": "第一口辅食一定是高铁米粉", "sort_order": 5},
    {"group_key": "golden_sentence", "label": "从稀到稠，从少到多，每次只加一种新食物", "value": "从稀到稠，从少到多，每次只加一种新食物", "sort_order": 6},
    {"group_key": "golden_sentence", "label": "热水一浇就能吃，懒人福音", "value": "热水一浇就能吃，懒人福音", "sort_order": 7},
    {"group_key": "golden_sentence", "label": "打工人的快乐就是这么简单", "value": "打工人的快乐就是这么简单", "sort_order": 8},
    {"group_key": "golden_sentence", "label": "早八人再也不用空腹上课了", "value": "早八人再也不用空腹上课了", "sort_order": 9},
    {"group_key": "golden_sentence", "label": "一口下去精神百倍", "value": "一口下去精神百倍", "sort_order": 10},
    {"group_key": "golden_sentence", "label": "90%的新手都踩过这5个坑", "value": "90%的新手都踩过这5个坑", "sort_order": 11},
    {"group_key": "golden_sentence", "label": "硅尼龙帐篷，轻到可以塞进书包", "value": "硅尼龙帐篷，轻到可以塞进书包", "sort_order": 12},
    {"group_key": "golden_sentence", "label": "鹅绒睡袋，保暖重量比的天花板", "value": "鹅绒睡袋，保暖重量比的天花板", "sort_order": 13},
    {"group_key": "golden_sentence", "label": "氨基酸洁面是油皮的最爱", "value": "氨基酸洁面是油皮的最爱", "sort_order": 14},
    {"group_key": "golden_sentence", "label": "粉底不是涂越多越好，轻薄才是王道", "value": "粉底不是涂越多越好，轻薄才是王道", "sort_order": 15},
    {"group_key": "golden_sentence", "label": "眉头浅眉尾深，自然又立体", "value": "眉头浅眉尾深，自然又立体", "sort_order": 16},

    # ----------------------------------------------------------
    # 数据引用预设 (data_ref) — 各行业常用数据论据
    # 用于增强素材说服力
    # ----------------------------------------------------------
    {"group_key": "data_ref", "label": "持妆8小时后，T区出油量减少60%", "value": "持妆8小时后，T区出油量减少60%", "sort_order": 1},
    {"group_key": "data_ref", "label": "连续使用28天，皮肤含水量提升40%", "value": "连续使用28天，皮肤含水量提升40%", "sort_order": 2},
    {"group_key": "data_ref", "label": "连续使用28天，泛红减少45%", "value": "连续使用28天，泛红减少45%", "sort_order": 3},
    {"group_key": "data_ref", "label": "6个月宝宝每天需要11mg铁", "value": "6个月宝宝每天需要11mg铁", "sort_order": 4},
    {"group_key": "data_ref", "label": "每样新食物观察3天不过敏再加下一样", "value": "每样新食物观察3天不过敏再加下一样", "sort_order": 5},
    {"group_key": "data_ref", "label": "1-3岁每天需要约1000大卡热量", "value": "1-3岁每天需要约1000大卡热量", "sort_order": 6},
    {"group_key": "data_ref", "label": "均价3块钱一顿", "value": "均价3块钱一顿", "sort_order": 7},
    {"group_key": "data_ref", "label": "保质期长达12个月", "value": "保质期长达12个月", "sort_order": 8},
    {"group_key": "data_ref", "label": "含糖量低于5g", "value": "含糖量低于5g", "sort_order": 9},
    {"group_key": "data_ref", "label": "热量仅100大卡", "value": "热量仅100大卡", "sort_order": 10},
    {"group_key": "data_ref", "label": "整套装备控制在5kg以内", "value": "整套装备控制在5kg以内", "sort_order": 11},
    {"group_key": "data_ref", "label": "硅尼龙比普通尼龙轻40%", "value": "硅尼龙比普通尼龙轻40%", "sort_order": 12},
    {"group_key": "data_ref", "label": "碳纤维登山杖，每根仅180g", "value": "碳纤维登山杖，每根仅180g", "sort_order": 13},
    {"group_key": "data_ref", "label": "SPF50+ PA++++ 适合户外暴晒场景", "value": "SPF50+ PA++++ 适合户外暴晒场景", "sort_order": 14},

    # ----------------------------------------------------------
    # 视觉描述预设 (visual_desc) — 素材拍摄/呈现的视觉建议
    # ----------------------------------------------------------
    {"group_key": "visual_desc", "label": "质地特写镜头", "value": "质地特写镜头", "sort_order": 1},
    {"group_key": "visual_desc", "label": "上脸推开效果", "value": "上脸推开效果", "sort_order": 2},
    {"group_key": "visual_desc", "label": "前后对比图", "value": "前后对比图", "sort_order": 3},
    {"group_key": "visual_desc", "label": "半脸对比效果", "value": "半脸对比效果", "sort_order": 4},
    {"group_key": "visual_desc", "label": "8小时后持妆对比", "value": "8小时后持妆对比", "sort_order": 5},
    {"group_key": "visual_desc", "label": "米粉冲泡对比图", "value": "米粉冲泡对比图", "sort_order": 6},
    {"group_key": "visual_desc", "label": "不同月龄食物质地展示", "value": "不同月龄食物质地展示", "sort_order": 7},
    {"group_key": "visual_desc", "label": "过敏红疹警示图", "value": "过敏红疹警示图", "sort_order": 8},
    {"group_key": "visual_desc", "label": "速食开箱合集", "value": "速食开箱合集", "sort_order": 9},
    {"group_key": "visual_desc", "label": "冲泡过程快剪", "value": "冲泡过程快剪", "sort_order": 10},
    {"group_key": "visual_desc", "label": "宿舍桌面场景", "value": "宿舍桌面场景", "sort_order": 11},
    {"group_key": "visual_desc", "label": "红黑榜对比表格", "value": "红黑榜对比表格", "sort_order": 12},
    {"group_key": "visual_desc", "label": "成分表特写", "value": "成分表特写", "sort_order": 13},
    {"group_key": "visual_desc", "label": "上脸试用展示", "value": "上脸试用展示", "sort_order": 14},
    {"group_key": "visual_desc", "label": "错误vs正确对比图", "value": "错误vs正确对比图", "sort_order": 15},
    {"group_key": "visual_desc", "label": "新手化妆前后对比", "value": "新手化妆前后对比", "sort_order": 16},
    {"group_key": "visual_desc", "label": "工具使用演示", "value": "工具使用演示", "sort_order": 17},
    {"group_key": "visual_desc", "label": "装备全家福", "value": "装备全家福", "sort_order": 18},
    {"group_key": "visual_desc", "label": "重量对比展示", "value": "重量对比展示", "sort_order": 19},
    {"group_key": "visual_desc", "label": "户外使用场景", "value": "户外使用场景", "sort_order": 20},
]


def seed():
    """
    执行数据初始化

    流程：
    1. 创建数据库会话
    2. 清空 option 表所有现有数据（DELETE FROM option）
    3. 批量插入 DEFAULT_OPTIONS 中的所有默认数据
    4. 提交事务

    异常处理：
    - 如果插入过程中发生任何错误，回滚事务并打印错误信息
    - 数据库连接在 finally 块中确保关闭

    Note:
        此函数是幂等操作——多次执行结果相同（先清空再重建）。
    """
    db = SessionLocal()
    try:
        # Step 1: 清空旧数据，确保每次初始化都是干净的状态
        db.query(Option).delete()

        # Step 2: 批量插入所有默认选项
        for opt in DEFAULT_OPTIONS:
            db.add(Option(**opt))

        # Step 3: 提交事务，一次性写入所有数据
        db.commit()
        print(f"[OK] 已初始化 {len(DEFAULT_OPTIONS)} 条选项数据")
    except Exception as e:
        # 发生异常时回滚，避免数据库处于不一致状态
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        # 无论成功还是失败，都要关闭数据库连接
        db.close()


# ============================================================
# 直接运行入口
# ============================================================
if __name__ == "__main__":
    # 当直接运行此脚本时，执行 seed() 初始化数据
    seed()
