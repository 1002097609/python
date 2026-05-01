"""
选项数据初始化种子脚本（Upsert 模式）

用途：
  将系统中所有下拉框的默认选项数据写入数据库。
  包括：平台、品类、风格、策略、骨架类型、裂变模式、金句、数据引用、视觉描述、
        裂变记录状态、素材状态等共 12 个分组。

用法：
  方式1（推荐）: python -c "from backend.seed_options import seed; seed()"
  方式2: python backend/seed_options.py

注意：
  seed() 使用 upsert（merge）模式：对每条默认选项，若 (group_key, value) 已存在则
  更新 label/sort_order，不存在则插入。不会删除用户手动添加的自定义选项。
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
# 覆盖 12 个分组
# ============================================================

DEFAULT_OPTIONS = [
    # ----------------------------------------------------------
    # 平台 (platform) — 素材来源平台
    # ----------------------------------------------------------
    {"group_key": "platform", "label": "抖音", "value": "抖音", "sort_order": 1},
    {"group_key": "platform", "label": "小红书", "value": "小红书", "sort_order": 2},
    {"group_key": "platform", "label": "快手", "value": "快手", "sort_order": 3},
    {"group_key": "platform", "label": "B站", "value": "B站", "sort_order": 4},
    {"group_key": "platform", "label": "微信视频号", "value": "微信视频号", "sort_order": 5},

    # ----------------------------------------------------------
    # 品类 (category) — 素材所属商品/服务品类
    # 覆盖消费品、耐用品、虚拟服务等多个行业
    # ----------------------------------------------------------
    {"group_key": "category", "label": "护肤", "value": "护肤", "sort_order": 1},
    {"group_key": "category", "label": "彩妆", "value": "彩妆", "sort_order": 2},
    {"group_key": "category", "label": "零食", "value": "零食", "sort_order": 3},
    {"group_key": "category", "label": "母婴", "value": "母婴", "sort_order": 4},
    {"group_key": "category", "label": "户外", "value": "户外", "sort_order": 5},
    {"group_key": "category", "label": "数码", "value": "数码", "sort_order": 6},
    {"group_key": "category", "label": "家居", "value": "家居", "sort_order": 7},
    {"group_key": "category", "label": "服饰", "value": "服饰", "sort_order": 8},
    {"group_key": "category", "label": "宠物", "value": "宠物", "sort_order": 9},
    {"group_key": "category", "label": "健身", "value": "健身", "sort_order": 10},
    {"group_key": "category", "label": "食品饮料", "value": "食品饮料", "sort_order": 11},
    {"group_key": "category", "label": "家电", "value": "家电", "sort_order": 12},
    {"group_key": "category", "label": "汽车", "value": "汽车", "sort_order": 13},
    {"group_key": "category", "label": "教育培训", "value": "教育培训", "sort_order": 14},
    {"group_key": "category", "label": "金融理财", "value": "金融理财", "sort_order": 15},
    {"group_key": "category", "label": "医疗健康", "value": "医疗健康", "sort_order": 16},
    {"group_key": "category", "label": "旅游出行", "value": "旅游出行", "sort_order": 17},
    {"group_key": "category", "label": "房产", "value": "房产", "sort_order": 18},
    {"group_key": "category", "label": "游戏", "value": "游戏", "sort_order": 19},
    {"group_key": "category", "label": "文化娱乐", "value": "文化娱乐", "sort_order": 20},
    {"group_key": "category", "label": "企业服务", "value": "企业服务", "sort_order": 21},
    {"group_key": "category", "label": "农业", "value": "农业", "sort_order": 22},

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
    # 裂变记录状态 (fission_status) — 素材裂变产出的状态流转
    # ----------------------------------------------------------
    {"group_key": "fission_status", "label": "草稿", "value": "0", "sort_order": 1},
    {"group_key": "fission_status", "label": "待审核", "value": "1", "sort_order": 2},
    {"group_key": "fission_status", "label": "已采用", "value": "2", "sort_order": 3},
    {"group_key": "fission_status", "label": "已投放", "value": "3", "sort_order": 4},

    # ----------------------------------------------------------
    # 素材状态 (material_status) — 素材的拆解状态流转
    # ----------------------------------------------------------
    {"group_key": "material_status", "label": "未拆解", "value": "0", "sort_order": 1},
    {"group_key": "material_status", "label": "已拆解", "value": "1", "sort_order": 2},
    {"group_key": "material_status", "label": "已归档", "value": "2", "sort_order": 3},

    # ----------------------------------------------------------
    # 裂变模式 (fission_mode) — 素材裂变的三种策略
    # ----------------------------------------------------------
    # replace_leaf:   换叶子 — 替换 L1(主题)+L5(表达)，骨架不变，效果保留约 85%
    # replace_style:  换表达 — 替换 L2(策略)+L5(表达)，骨架不变，效果保留约 70%
    # replace_branch: 换枝杈 — 替换 L3(结构)+L4(元素)，主题不变，效果保留约 65%
    {"group_key": "fission_mode", "label": "换叶子|🍃|效果保留85%", "value": "replace_leaf", "sort_order": 1},
    {"group_key": "fission_mode", "label": "换表达|🎨|效果保留70%", "value": "replace_style", "sort_order": 2},
    {"group_key": "fission_mode", "label": "换枝杈|🌿|效果保留65%", "value": "replace_branch", "sort_order": 3},

    # ----------------------------------------------------------
    # 金句预设 (golden_sentence) — 各行业常用营销金句
    # 覆盖22个品类：护肤/彩妆/零食/母婴/户外/数码/家居/服饰/宠物/健身/食品饮料/家电/汽车/教育培训/金融理财/医疗健康/旅游出行/房产/游戏/文化娱乐/企业服务/农业
    # ----------------------------------------------------------
    {"group_key": "golden_sentence", "label": "这个细节99%的人都忽略了", "value": "这个细节99%的人都忽略了", "sort_order": 1},
    {"group_key": "golden_sentence", "label": "用了3年才发现这个方法", "value": "用了3年才发现这个方法", "sort_order": 2},
    {"group_key": "golden_sentence", "label": "花了一个月测试出来的结论", "value": "花了一个月测试出来的结论", "sort_order": 3},
    {"group_key": "golden_sentence", "label": "对比了10款之后的选择", "value": "对比了10款之后的选择", "sort_order": 4},
    {"group_key": "golden_sentence", "label": "后悔没早点知道", "value": "后悔没早点知道", "sort_order": 5},
    {"group_key": "golden_sentence", "label": "别再踩我踩过的坑了", "value": "别再踩我踩过的坑了", "sort_order": 6},
    {"group_key": "golden_sentence", "label": "效果因人而异，但值得一试", "value": "效果因人而异，但值得一试", "sort_order": 7},
    {"group_key": "golden_sentence", "label": "不是广告，纯分享", "value": "不是广告，纯分享", "sort_order": 8},
    {"group_key": "golden_sentence", "label": "性价比天花板", "value": "性价比天花板", "sort_order": 9},
    {"group_key": "golden_sentence", "label": "闭眼入不会错", "value": "闭眼入不会错", "sort_order": 10},
    {"group_key": "golden_sentence", "label": "回购了5次的好物", "value": "回购了5次的好物", "sort_order": 11},
    {"group_key": "golden_sentence", "label": "用了就回不去了", "value": "用了就回不去了", "sort_order": 12},
    {"group_key": "golden_sentence", "label": "平价替代天花板", "value": "平价替代天花板", "sort_order": 13},
    {"group_key": "golden_sentence", "label": "专业人士都在用", "value": "专业人士都在用", "sort_order": 14},
    {"group_key": "golden_sentence", "label": "被问了无数次的好物", "value": "被问了无数次的好物", "sort_order": 15},
    {"group_key": "golden_sentence", "label": "一次就见效", "value": "一次就见效", "sort_order": 16},

    # ----------------------------------------------------------
    # 数据引用预设 (data_ref) — 各行业常用数据论据
    # 用于增强素材说服力
    # ----------------------------------------------------------
    {"group_key": "data_ref", "label": "连续使用28天，效果显著提升", "value": "连续使用28天，效果显著提升", "sort_order": 1},
    {"group_key": "data_ref", "label": "对比同类产品，性价比高出30%", "value": "对比同类产品，性价比高出30%", "sort_order": 2},
    {"group_key": "data_ref", "label": "90%的用户反馈有效", "value": "90%的用户反馈有效", "sort_order": 3},
    {"group_key": "data_ref", "label": "经过3个月实测验证", "value": "经过3个月实测验证", "sort_order": 4},
    {"group_key": "data_ref", "label": "每单位成本降低40%", "value": "每单位成本降低40%", "sort_order": 5},
    {"group_key": "data_ref", "label": "满意度评分4.8/5.0", "value": "满意度评分4.8/5.0", "sort_order": 6},
    {"group_key": "data_ref", "label": "复购率达到65%", "value": "复购率达到65%", "sort_order": 7},
    {"group_key": "data_ref", "label": "使用周期长达12个月", "value": "使用周期长达12个月", "sort_order": 8},
    {"group_key": "data_ref", "label": "比传统方案节省50%时间", "value": "比传统方案节省50%时间", "sort_order": 9},
    {"group_key": "data_ref", "label": "有效成分含量达95%", "value": "有效成分含量达95%", "sort_order": 10},
    {"group_key": "data_ref", "label": "0不良反应报告", "value": "0不良反应报告", "sort_order": 11},
    {"group_key": "data_ref", "label": "平均见效时间7天", "value": "平均见效时间7天", "sort_order": 12},
    {"group_key": "data_ref", "label": "适用于99%的肤质/场景", "value": "适用于99%的肤质/场景", "sort_order": 13},
    {"group_key": "data_ref", "label": "行业推荐标准", "value": "行业推荐标准", "sort_order": 14},

    # ----------------------------------------------------------
    # 视觉描述预设 (visual_desc) — 素材拍摄/呈现的视觉建议
    # ----------------------------------------------------------
    {"group_key": "visual_desc", "label": "产品全景展示", "value": "产品全景展示", "sort_order": 1},
    {"group_key": "visual_desc", "label": "使用前后对比", "value": "使用前后对比", "sort_order": 2},
    {"group_key": "visual_desc", "label": "细节特写镜头", "value": "细节特写镜头", "sort_order": 3},
    {"group_key": "visual_desc", "label": "步骤分解演示", "value": "步骤分解演示", "sort_order": 4},
    {"group_key": "visual_desc", "label": "场景化使用展示", "value": "场景化使用展示", "sort_order": 5},
    {"group_key": "visual_desc", "label": "成分/参数特写", "value": "成分/参数特写", "sort_order": 6},
    {"group_key": "visual_desc", "label": "开箱体验", "value": "开箱体验", "sort_order": 7},
    {"group_key": "visual_desc", "label": "多角度展示", "value": "多角度展示", "sort_order": 8},
    {"group_key": "visual_desc", "label": "真人试用展示", "value": "真人试用展示", "sort_order": 9},
    {"group_key": "visual_desc", "label": "数据图表可视化", "value": "数据图表可视化", "sort_order": 10},
    {"group_key": "visual_desc", "label": "错误vs正确对比", "value": "错误vs正确对比", "sort_order": 11},
    {"group_key": "visual_desc", "label": "时间线对比", "value": "时间线对比", "sort_order": 12},
    {"group_key": "visual_desc", "label": "同类产品横向对比", "value": "同类产品横向对比", "sort_order": 13},
    {"group_key": "visual_desc", "label": "使用场景合集", "value": "使用场景合集", "sort_order": 14},
    {"group_key": "visual_desc", "label": "效果延时摄影", "value": "效果延时摄影", "sort_order": 15},
    {"group_key": "visual_desc", "label": "工具/道具展示", "value": "工具/道具展示", "sort_order": 16},
    {"group_key": "visual_desc", "label": "文字标注说明", "value": "文字标注说明", "sort_order": 17},
    {"group_key": "visual_desc", "label": "分屏对比效果", "value": "分屏对比效果", "sort_order": 18},
    {"group_key": "visual_desc", "label": "用户反馈截图", "value": "用户反馈截图", "sort_order": 19},
    {"group_key": "visual_desc", "label": "品牌标识展示", "value": "品牌标识展示", "sort_order": 20},
]


def seed():
    """
    执行数据初始化（Upsert / Merge 模式）

    流程：
    1. 创建数据库会话
    2. 遍历 DEFAULT_OPTIONS 中的每条默认数据：
       a. 根据 (group_key, value) 查询是否已存在
       b. 若存在：更新 label 和 sort_order
       c. 若不存在：插入新记录
    3. 提交事务

    异常处理：
    - 如果操作过程中发生任何错误，回滚事务并打印错误信息
    - 数据库连接在 finally 块中确保关闭

    Note:
        此函数是幂等操作——多次执行结果相同。
        不会删除用户手动添加的自定义选项（非 DEFAULT_OPTIONS 中的记录不受影响）。
    """
    db = SessionLocal()
    try:
        inserted = 0
        updated = 0

        for opt in DEFAULT_OPTIONS:
            # 查找是否已存在相同 (group_key, value) 的记录
            existing = (
                db.query(Option)
                .filter(Option.group_key == opt["group_key"], Option.value == opt["value"])
                .first()
            )

            if existing:
                # 已存在：更新 label 和 sort_order
                existing.label = opt["label"]
                existing.sort_order = opt["sort_order"]
                updated += 1
            else:
                # 不存在：插入新记录
                db.add(Option(**opt))
                inserted += 1

        db.commit()
        print(f"[OK] 已初始化选项数据：插入 {inserted} 条，更新 {updated} 条，共 {len(DEFAULT_OPTIONS)} 条")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()


# ============================================================
# 直接运行入口
# ============================================================
if __name__ == "__main__":
    # 当直接运行此脚本时，执行 seed() 初始化数据
    seed()
