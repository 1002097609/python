"""
批量测试数据生成脚本（backend/seed_data.py）。

用途：
  向数据库中批量插入逼真的测试数据，用于开发演示和接口测试。
  包含：标签、素材、拆解、骨架、裂变、效果数据、素材标签关联。

用法：
  python -c "from backend.seed_data import seed_all; seed_all()"

注意：
  - 所有插入操作使用"存在则跳过"策略，不会重复插入相同数据
  - 依赖 seed_options.py 中的选项数据（需先运行 seed_options.seed()）
  - 数据库中已有的数据不会被删除或修改
"""

import random
from datetime import date, timedelta
from backend.database import SessionLocal
from backend.models.tag import Tag, MaterialTag
from backend.models.material import Material
from backend.models.dismantle import Dismantle
from backend.models.skeleton import Skeleton
from backend.models.fission import Fission
from backend.models.effect_data import EffectData
from backend.models.option import Option


# ============================================================
# 标签数据
# ============================================================

# 所有品类列表（用于随机选择）
ALL_CATEGORIES = [
    "护肤", "彩妆", "零食", "母婴", "户外", "数码", "家居", "服饰", "宠物", "健身",
    "食品饮料", "家电", "汽车", "教育培训", "金融理财", "医疗健康", "旅游出行",
    "房产", "游戏", "文化娱乐", "企业服务", "农业",
]

TAGS = [
    # 平台标签
    ("抖音", "platform"),
    ("小红书", "platform"),
    ("快手", "platform"),
    ("B站", "platform"),
    ("微信视频号", "platform"),
    # 品类标签（与 ALL_CATEGORIES 保持一致）
    ("护肤", "category"),
    ("彩妆", "category"),
    ("零食", "category"),
    ("母婴", "category"),
    ("户外", "category"),
    ("数码", "category"),
    ("家居", "category"),
    ("服饰", "category"),
    ("宠物", "category"),
    ("健身", "category"),
    ("食品饮料", "category"),
    ("家电", "category"),
    ("汽车", "category"),
    ("教育培训", "category"),
    ("金融理财", "category"),
    ("医疗健康", "category"),
    ("旅游出行", "category"),
    ("房产", "category"),
    ("游戏", "category"),
    ("文化娱乐", "category"),
    ("企业服务", "category"),
    ("农业", "category"),
    # 风格标签
    ("专业感", "style"),
    ("亲和力", "style"),
    ("紧迫感", "style"),
    ("幽默感", "style"),
    ("治愈系", "style"),
    ("高端感", "style"),
    ("接地气", "style"),
    ("科技感", "style"),
    # 策略标签
    ("共鸣型", "strategy"),
    ("成分党", "strategy"),
    ("对比测评", "strategy"),
    ("悬念型", "strategy"),
    ("教程型", "strategy"),
    ("清单型", "strategy"),
    ("红黑榜型", "strategy"),
    ("种草型", "strategy"),
    ("攻略型", "strategy"),
    ("误区纠正型", "strategy"),
]


# ============================================================
# 素材数据
# ============================================================

MATERIALS = [
    # 护肤类
    ("秋冬保湿面霜成分测评：神经酰胺真的有用吗？", "护肤", "抖音", "video",
     "今天实测5款含神经酰胺的面霜，从成分浓度到上脸效果全拆解。第一款A牌，成分表排名第3位，实测保湿度提升30%；第二款B牌主打复合神经酰胺..."),
    ("敏感肌修护红黑榜：这3款产品千万别买", "护肤", "小红书", "image",
     "作为敏感肌踩坑大户，今天给大家整理一份真实红黑榜。黑榜：某大牌修护面霜含香精酒精，上脸刺痛；某网红面膜防腐剂超标..."),
    ("油皮夏日控油指南：从洁面到定妆全流程", "护肤", "抖音", "video",
     "油皮姐妹看过来！夏天脱妆斑驳真的太烦了。今天分享我的控油全流程：氨基酸洁面→控油爽肤水→轻薄精华→无油防晒→定妆喷雾..."),
    ("抗老精华怎么选？3款热门产品横向对比", "护肤", "快手", "video",
     "25岁以后抗老必须提上日程！今天对比3款热门抗老精华：A醇类、胜肽类、玻色因类，从成分到质地到效果全部分享..."),
    # 彩妆类
    ("新手化妆5大误区：你中了几个？", "彩妆", "抖音", "video",
     "新手化妆最容易踩的5个坑！第一，粉底越厚越好错！轻薄才是王道；第二，眉毛画太深..."),
    ("干皮秋冬滋润粉底液横评：哪款不卡粉？", "彩妆", "小红书", "image",
     "干皮姐妹的福音来了！实测6款滋润型粉底液，从滋润度到持妆力全部打分。A牌水润感十足但持妆一般..."),
    ("眼妆教程：3种眼型的修饰技巧", "彩妆", "B站", "video",
     "单眼皮、内双、肿眼泡各有各的修法。今天用同一盘眼影演示3种眼型的不同画法..."),
    # 零食类
    ("办公室解压零食TOP10：打工人续命清单", "零食", "抖音", "video",
     "打工人摸鱼必备！测评了20款办公室零食，精选出TOP10。第一名：独立包装坚果，方便又不脏手..."),
    ("宿舍党速食天花板：热水一泡就能吃", "零食", "快手", "video",
     "早八人再也不用空腹上课了！测评10款速食，从泡面到自热饭到冲泡粥，哪款最值得囤..."),
    ("减脂期低卡零食推荐：好吃不胖的秘密", "零食", "小红书", "image",
     "减脂期嘴馋怎么办？整理了15款低卡零食，热量全部标注。黑巧克力、海苔、无糖酸奶..."),
    # 母婴类
    ("0-1岁宝宝辅食添加全攻略：按月龄详解", "母婴", "小红书", "image",
     "宝宝多大开始加辅食？每阶段吃什么？这份全攻略帮你搞定。6个月高铁米粉→7个月蔬菜泥→8个月肉泥..."),
    ("宝宝红屁屁怎么办？护臀霜测评+护理方法", "母婴", "抖音", "video",
     "红屁屁是新手爸妈最头疼的问题！今天测评5款热门护臀霜，从成分到效果全部分享，还有3个预防红屁屁的关键技巧..."),
    ("婴儿推车怎么选？5款热门车型横评", "母婴", "B站", "video",
     "从轻便型到高景观，5款热门婴儿推车全部实测。重量、折叠、避震、储物空间全部打分..."),
    # 户外类
    ("露营装备轻量化攻略：背包控制在5kg以内", "户外", "B站", "video",
     "轻量化露营才是王道！今天分享我的5kg装备清单：硅尼龙帐篷、碳纤维登山杖、鹅绒睡袋..."),
    ("一日徒步装备清单：新手必看", "户外", "小红书", "image",
     "第一次徒步要带什么？这份清单帮你准备齐全。必备：登山鞋、速干衣、头灯、急救包..."),
    ("防晒霜横评：户外暴晒哪款不晒黑？", "户外", "抖音", "video",
     "夏天户外防晒太重要了！实测8款高倍防晒，从SPF值到防水力到肤感全部测评..."),
    # 数码类
    ("2024年TWS耳机横评：从99到999怎么选", "数码", "B站", "video",
     "从入门到旗舰，10款TWS耳机全部实测。音质、降噪、续航、佩戴舒适度全部打分..."),
    ("手机摄影技巧：不用修图也能出大片", "数码", "抖音", "video",
     "不用修图APP，手机直出大片！分享5个构图技巧和3个光线运用方法..."),
    # 家居类
    ("小户型收纳神器：10件让家大一倍的好物", "家居", "小红书", "image",
     "小户型收纳是门学问！分享10件实测好用的收纳神器：真空压缩袋、置物架、抽屉分隔盒..."),
    ("租房改造：1000元打造ins风小窝", "家居", "抖音", "video",
     "租房也能住出幸福感！1000元预算改造出租墙：挂布、置物架、氛围灯、收纳盒..."),
    # 服饰类
    ("秋冬穿搭公式：3件单品搞定一周穿搭", "服饰", "小红书", "image",
     "懒人穿搭公式来了！一件大衣+一件卫衣+一条裤子，通过配饰和穿法变化搞定一周不重样..."),
    ("微胖女生穿搭技巧：显瘦10斤的穿搭法则", "服饰", "抖音", "video",
     "微胖女生看过来！分享5个显瘦穿搭法则：高腰线、V领、垂感面料、同色系、适当露肤..."),
    # 宠物类
    ("猫粮怎么选？5款热门猫粮横评", "宠物", "B站", "video",
     "选猫粮看什么？蛋白含量、配料表、价格。今天横评5款热门猫粮，从成分到猫咪适口性全部测评..."),
    ("新手养猫攻略：从接猫到日常护理", "宠物", "小红书", "image",
     "第一次养猫要做哪些准备？这份攻略帮你搞定：接猫注意事项、疫苗驱虫时间表、日常护理..."),
    # 健身类
    ("居家健身：哑铃训练全攻略", "健身", "抖音", "video",
     "一对哑铃练全身！今天分享8个动作：哑铃深蹲、哑铃划船、哑铃推举、哑铃弯举..."),
    ("跑步新手指南：从0到5公里的训练计划", "健身", "B站", "video",
     "跑步小白如何科学开跑？12周训练计划，从跑走结合到轻松跑完5公里..."),
    # 补充素材
    ("成分党必看：烟酰胺浓度越高越好吗？", "护肤", "小红书", "image",
     "烟酰胺到底怎么选？2%、5%、10%浓度实测对比。高浓度不等于效果好，关键看配方体系..."),
    ("油皮夏日控油妆前乳横评：哪款不搓泥？", "彩妆", "抖音", "video",
     "油皮夏天妆前太重要了！测评6款控油妆前乳，从控油力到搓泥情况到持妆效果全部打分..."),
    ("考研党熬夜零食清单：提神不胖", "零食", "快手", "video",
     "考研熬夜必备零食！咖啡、黑巧克力、坚果、低糖能量棒，提神又不胖..."),
    ("宝宝安全座椅怎么选？4款热门型号横评", "母婴", "B站", "video",
     "安全座椅是宝宝出行的必需品！实测4款热门型号：安装便利性、舒适度、安全性全部对比..."),
    ("冬季露营装备清单：零下10度怎么保暖", "户外", "小红书", "image",
     "冬天露营保暖是关键！分享我的装备清单：四季帐篷、-15度睡袋、防潮垫、暖宝宝..."),
    ("机械键盘入门指南：从轴体到配列怎么选", "数码", "B站", "video",
     "机械键盘水太深！红轴、茶轴、青轴、静音轴全部试一遍，告诉你哪种最适合你..."),
    ("厨房收纳神器：让台面空无一物的秘诀", "家居", "抖音", "video",
     "厨房乱？收纳做对了就不乱！分享8件厨房收纳神器：磁吸刀架、调料置物架、水槽置物架..."),
    ("胶囊衣橱：20件单品搞定四季穿搭", "服饰", "小红书", "image",
     "少而精的衣橱才是王道！分享我的胶囊衣橱20件单品清单和搭配公式..."),
    ("狗狗零食测评：天然零食vs加工零食", "宠物", "抖音", "video",
     "狗狗零食到底怎么选？天然风干零食vs加工零食，从成分到狗狗适口性全部对比..."),
    ("瑜伽入门：每天15分钟改善体态", "健身", "小红书", "image",
     "久坐党体态问题怎么改善？15分钟瑜伽跟练：猫牛式、下犬式、眼镜蛇式、婴儿式..."),
    # 食品饮料类
    ("奶茶红黑榜：这5款奶茶热量爆表你还天天喝", "食品饮料", "抖音", "video",
     "奶茶续命？先看看热量榜！测评10款热门奶茶，从含糖量到热量全部标注。第一名热量相当于3碗米饭..."),
    ("咖啡入门指南：从速溶到手冲的完整攻略", "食品饮料", "B站", "video",
     "咖啡小白如何入门？从速溶到手冲，从意式到美式，一篇讲清楚咖啡豆产区、烘焙度、冲煮方式..."),
    # 家电类
    ("扫地机器人横评：2000元和5000元差在哪", "家电", "B站", "video",
     "扫地机器人到底怎么选？实测6款热门机型，从避障能力到清洁力到噪音全部打分..."),
    ("小家电推荐：提升幸福感的10件厨房神器", "家电", "小红书", "image",
     "厨房小白也能变大厨！分享10件实测好用的小家电：空气炸锅、破壁机、电压力锅..."),
    # 汽车类
    ("10万以内买什么车？5款热门车型对比", "汽车", "B站", "video",
     "预算10万怎么选车？实测5款热门车型：动力、空间、油耗、配置全部对比..."),
    ("新手买车避坑指南：这5个配置千万别选", "汽车", "抖音", "video",
     "4S店的坑太多了！分享新手买车最容易踩的5个坑：低配加装、延保套餐、金融服务费..."),
    # 教育培训类
    ("Python零基础入门：30天学习路线图", "教育培训", "B站", "video",
     "零基础学Python怎么入门？30天学习计划，从环境搭建到项目实战，每天1小时就够了..."),
    ("在线教育平台对比：哪家网课值得买", "教育培训", "小红书", "image",
     "网课平台太多了！对比5大在线教育平台：课程质量、价格、师资、服务全部测评..."),
    # 金融理财类
    ("基金定投新手指南：每月500元也能理财", "金融理财", "小红书", "image",
     "月光族如何开始理财？基金定投入门：选什么基金、什么时候买、什么时候卖..."),
    ("保险怎么买不踩坑：重疾险vs医疗险怎么选", "金融理财", "抖音", "video",
     "保险水太深！一篇讲清楚重疾险、医疗险、意外险、寿险的区别和选购要点..."),
    # 医疗健康类
    ("体检报告怎么看？5个关键指标解读", "医疗健康", "小红书", "image",
     "每次体检报告都看不懂？教你看5个关键指标：血糖、血脂、肝功、肾功、血常规..."),
    ("失眠怎么办？科学助眠的10个方法", "医疗健康", "抖音", "video",
     "失眠太痛苦了！分享10个科学验证过的助眠方法：睡眠卫生、认知行为疗法、放松训练..."),
    # 旅游出行类
    ("云南旅游全攻略：7天6晚人均3000元", "旅游出行", "小红书", "image",
     "云南怎么玩最划算？7天6晚行程规划：昆明→大理→丽江→香格里拉，住宿交通全攻略..."),
    ("机票怎么买最便宜？5个省钱技巧", "旅游出行", "抖音", "video",
     "买机票别再当冤大头！分享5个省钱技巧：比价网站、廉航会员、中转联程、提前购票..."),
    # 房产类
    ("第一次买房必看：二手房交易全流程", "房产", "B站", "video",
     "第一次买房不知道从哪下手？二手房交易全流程：看房→签约→贷款→过户，每步都有坑..."),
    ("租房避坑指南：这5类房子千万别租", "房产", "抖音", "video",
     "租房踩坑血泪史！5类房子千万别租：隔断房、消防隐患房、产权不清房..."),
    # 游戏类
    ("2024年手游推荐：10款值得玩的新游戏", "游戏", "B站", "video",
     "2024年有哪些值得玩的手游？从RPG到策略到休闲，10款新游戏全部试玩评测..."),
    ("游戏本怎么选？5款热门游戏本横评", "游戏", "B站", "video",
     "打游戏用什么电脑？5款热门游戏本实测对比：帧率、散热、屏幕、键盘手感全部打分..."),
    # 文化娱乐类
    ("2024年必看韩剧推荐：追剧清单来了", "文化娱乐", "小红书", "image",
     "2024年韩剧推荐清单：从悬疑到浪漫到职场，10部高分韩剧全部整理..."),
    ("剧本杀入门指南：新手第一次怎么玩", "文化娱乐", "抖音", "video",
     "剧本杀小白第一次怎么玩？选本技巧、角色扮演、推理思路全部分享..."),
    # 企业服务类
    ("中小企业数字化转型：从0到1全攻略", "企业服务", "B站", "video",
     "中小企业如何做数字化转型？从CRM到ERP到数据分析，一篇讲清楚实施路径..."),
    ("SaaS工具推荐：提升团队效率的15款工具", "企业服务", "小红书", "image",
     "远程办公效率太低？推荐15款SaaS工具：项目管理、协作文档、视频会议、设计工具..."),
    # 农业类
    ("阳台种菜攻略：新手也能种出有机蔬菜", "农业", "抖音", "video",
     "城市阳台也能种菜！分享10种适合阳台种植的蔬菜：土壤、花盆、浇水、施肥全攻略..."),
    ("农产品电商怎么做？从产地到餐桌的全链路", "农业", "B站", "video",
     "农产品如何卖出去？农产品电商全链路：品控、物流、营销、售后全部拆解..."),
]


# ============================================================
# 拆解数据模板
# ============================================================

def build_dismantle_data(material_title, category):
    """根据素材标题和品类生成拆解数据"""
    return {
        "l1_topic": material_title[:20],
        "l1_core_point": f"{category}领域的核心洞察与实操方案",
        "l2_strategy": random.sample(["共鸣型", "成分党", "对比测评", "教程型", "种草型"], k=2),
        "l2_emotion": random.choice(["焦虑→信任→行动", "好奇→惊喜→认同", "困惑→清晰→行动"]),
        "l3_structure": [
            {"name": "开头", "function": "痛点共鸣", "ratio": random.randint(10, 20)},
            {"name": "主体", "function": "价值输出", "ratio": random.randint(50, 65)},
            {"name": "结尾", "function": "引导行动", "ratio": random.randint(15, 25)},
        ],
        "l4_elements": {
            "title_formula": "痛点+数字+结果",
            "hook": random.choice(["我踩了N个坑才找到", "90%的人都忽略了这个问题", "用了3年才发现"]),
            "transition": random.choice(["但是重点来了", "接下来才是关键", "划重点"]),
            "interaction": random.choice(["评论区告诉我你的情况", "你用过哪款？评论区聊聊", "点赞收藏慢慢看"]),
        },
        "l5_expressions": {
            "golden_sentences": random.sample(["这个细节99%的人都忽略了", "用了3年才发现这个方法", "性价比天花板"], k=2),
            "data_refs": random.sample(["连续使用28天效果显著", "90%的用户反馈有效"], k=1),
            "visual_desc": random.sample(["产品全景展示", "使用前后对比", "细节特写镜头"], k=2),
        },
    }


# ============================================================
# 裂变数据模板
# ============================================================

FISSION_CONFIGS = [
    ("replace_leaf", "换品类延伸"),
    ("replace_branch", "换结构重组"),
    ("replace_style", "换风格移植"),
]


# ============================================================
# 效果数据模板
# ============================================================

def build_effect_data(fission_id, platform):
    """生成效果数据"""
    impressions = random.randint(50000, 500000)
    ctr = round(random.uniform(0.8, 4.5), 2)
    clicks = int(impressions * ctr / 100)
    cvr = round(random.uniform(1.0, 8.0), 2)
    conversions = int(clicks * cvr / 100)
    cost = round(random.uniform(500, 5000), 2)
    revenue = round(cost * random.uniform(1.2, 5.0), 2)
    roi = round(revenue / cost, 2)
    cpa = round(cost / max(conversions, 1), 2)

    return {
        "fission_id": fission_id,
        "platform": platform,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr,
        "conversions": conversions,
        "cvr": cvr,
        "cost": cost,
        "revenue": revenue,
        "roi": roi,
        "cpa": cpa,
        "stat_date": str(date.today() - timedelta(days=random.randint(1, 30))),
    }


# ============================================================
# 主函数
# ============================================================

def seed_all():
    """
    执行全部数据初始化。

    流程：
    1. 创建标签
    2. 创建素材（30+ 条）
    3. 创建拆解记录（覆盖已有素材）
    4. 创建骨架（从拆解自动提取 + 手动创建）
    5. 创建裂变记录（每种模式都有）
    6. 创建效果数据
    7. 创建素材标签关联

    所有操作使用"存在则跳过"策略，不会重复插入。
    """
    db = SessionLocal()
    try:
        stats = {"tags": 0, "materials": 0, "dismantles": 0, "skeletons": 0, "fissions": 0, "effects": 0, "material_tags": 0}

        # --------------------------------------------------
        # Step 1: 创建标签（通过 option 表关联）
        # --------------------------------------------------
        # 先确保 option 数据已存在（依赖 seed_options.py）
        # 对于 TAGS 中每个标签，尝试从 option 表查找匹配记录并关联
        for name, tag_type in TAGS:
            existing = db.query(Tag).filter(Tag.name == name, Tag.type == tag_type).first()
            if not existing:
                # 查找 option 表中匹配的记录
                opt = (
                    db.query(Option)
                    .filter(Option.group_key == tag_type, Option.value == name, Option.is_active == 1)
                    .first()
                )
                db.add(Tag(name=name, type=tag_type, option_id=opt.id if opt else None))
                stats["tags"] += 1
        db.commit()
        print(f"[OK] 标签: 新增 {stats['tags']} 条")

        # --------------------------------------------------
        # Step 2: 创建素材
        # --------------------------------------------------
        for title, category, platform, media_type, content in MATERIALS:
            existing = db.query(Material).filter(Material.title == title).first()
            if not existing:
                db.add(Material(
                    title=title,
                    content=content,
                    platform=platform,
                    category=category,
                    media_type=media_type,
                    source_url=f"https://example.com/{platform.lower()}/{random.randint(10000, 99999)}",
                    status=random.choice([0, 0, 1, 1, 1, 2]),  # 大部分已拆解
                ))
                stats["materials"] += 1
        db.commit()
        print(f"[OK] 素材: 新增 {stats['materials']} 条")

        # --------------------------------------------------
        # Step 3: 创建拆解记录
        # --------------------------------------------------
        materials = db.query(Material).all()
        for mat in materials:
            # 检查是否已有拆解记录
            existing = db.query(Dismantle).filter(Dismantle.material_id == mat.id).first()
            if not existing and mat.status >= 1:
                data = build_dismantle_data(mat.title, mat.category)
                db.add(Dismantle(
                    material_id=mat.id,
                    l1_topic=data["l1_topic"],
                    l1_core_point=data["l1_core_point"],
                    l2_strategy=data["l2_strategy"],
                    l2_emotion=data["l2_emotion"],
                    l3_structure=data["l3_structure"],
                    l4_elements=data["l4_elements"],
                    l5_expressions=data["l5_expressions"],
                ))
                stats["dismantles"] += 1
        db.commit()
        print(f"[OK] 拆解: 新增 {stats['dismantles']} 条")

        # --------------------------------------------------
        # Step 4: 创建骨架
        # --------------------------------------------------
        dismantles = db.query(Dismantle).all()
        skeleton_names = set()
        for d in dismantles:
            if d.skeleton_id:
                continue  # 已有骨架
            sk_type = random.choice(["通用型", "测评对比型", "红黑榜型", "误区纠正型", "教程步骤型"])
            name = f"{sk_type} — {d.l1_topic[:15]}"
            if name not in skeleton_names:
                skeleton_names.add(name)
                sk = Skeleton(
                    name=name,
                    skeleton_type=sk_type,
                    source_material_id=d.material_id,
                    strategy_desc=d.l2_emotion,
                    structure_json=d.l3_structure,
                    elements_json=d.l4_elements,
                    style_tags=d.l2_strategy,
                    usage_count=random.randint(0, 8),
                    avg_roi=round(random.uniform(1.0, 4.5), 2),
                    avg_ctr=round(random.uniform(0.8, 3.5), 2),
                    platform=random.choice(["抖音", "小红书", "快手"]),
                )
                db.add(sk)
                db.flush()  # 获取 ID
                d.skeleton_id = sk.id
                stats["skeletons"] += 1
        db.commit()
        print(f"[OK] 骨架: 新增 {stats['skeletons']} 条")

        # --------------------------------------------------
        # Step 5: 创建裂变记录
        # --------------------------------------------------
        skeletons = db.query(Skeleton).all()
        fission_count = db.query(Fission).count()
        target_fissions = max(0, 25 - fission_count)  # 目标至少 25 条

        for i in range(target_fissions):
            sk = random.choice(skeletons)
            mode = random.choice(["replace_leaf", "replace_branch", "replace_style"])
            new_topic = random.choice(["新手入门指南", "进阶技巧分享", "避坑大全", "好物推荐", "对比测评", "使用教程", "选购攻略"])

            db.add(Fission(
                skeleton_id=sk.id,
                source_material_id=sk.source_material_id,
                fission_mode=mode,
                new_topic=new_topic,
                new_category=random.choice(ALL_CATEGORIES),
                new_platform=random.choice(["抖音", "小红书", "快手"]),
                output_title=f"{new_topic}",
                output_content=f"【开头 — 痛点共鸣】\n{new_topic}相关内容分享\n\n【主体 — 价值输出】\n{mode}模式生成的内容\n\n【结尾 — 引导行动】\n欢迎评论区交流！",
                output_status=random.choice([0, 0, 1, 2, 3, 3]),
                predicted_ctr=f"{random.uniform(1.0, 3.0):.1f}%-{random.uniform(3.0, 5.0):.1f}%",
                predicted_roi=f"{random.uniform(1.5, 3.0):.1f}x-{random.uniform(3.0, 5.0):.1f}x",
            ))
            stats["fissions"] += 1
        db.commit()
        print(f"[OK] 裂变: 新增 {stats['fissions']} 条")

        # --------------------------------------------------
        # Step 6: 创建效果数据
        # --------------------------------------------------
        fissions = db.query(Fission).filter(Fission.output_status >= 2).all()
        for f in fissions:
            # 检查是否已有效果数据
            existing_count = db.query(EffectData).filter(EffectData.fission_id == f.id).count()
            if existing_count == 0:
                effect = build_effect_data(f.id, f.new_platform or "抖音")
                db.add(EffectData(**effect))
                stats["effects"] += 1
        db.commit()
        print(f"[OK] 效果: 新增 {stats['effects']} 条")

        # --------------------------------------------------
        # Step 7: 创建素材标签关联
        # --------------------------------------------------
        all_tags = db.query(Tag).all()
        for mat in materials:
            # 每个素材随机打 2-4 个标签
            num_tags = random.randint(2, 4)
            selected_tags = random.sample(all_tags, min(num_tags, len(all_tags)))
            for tag in selected_tags:
                existing = db.query(MaterialTag).filter(
                    MaterialTag.material_id == mat.id,
                    MaterialTag.tag_id == tag.id,
                ).first()
                if not existing:
                    db.add(MaterialTag(material_id=mat.id, tag_id=tag.id))
                    stats["material_tags"] += 1
        db.commit()
        print(f"[OK] 素材标签: 新增 {stats['material_tags']} 条")

        # --------------------------------------------------
        # 汇总
        # --------------------------------------------------
        print(f"\n{'='*50}")
        print(f"数据初始化完成！")
        print(f"  标签: {db.query(Tag).count()} 条")
        print(f"  素材: {db.query(Material).count()} 条")
        print(f"  拆解: {db.query(Dismantle).count()} 条")
        print(f"  骨架: {db.query(Skeleton).count()} 条")
        print(f"  裂变: {db.query(Fission).count()} 条")
        print(f"  效果: {db.query(EffectData).count()} 条")
        print(f"  素材标签: {db.query(MaterialTag).count()} 条")
        print(f"{'='*50}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
