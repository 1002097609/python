from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_all_options():
    """返回所有下拉框选项数据"""
    return {
        "platforms": [
            {"label": "抖音", "value": "抖音"},
            {"label": "小红书", "value": "小红书"},
            {"label": "快手", "value": "快手"},
        ],
        "categories": [
            {"label": "护肤", "value": "护肤"},
            {"label": "彩妆", "value": "彩妆"},
            {"label": "零食", "value": "零食"},
            {"label": "母婴", "value": "母婴"},
            {"label": "户外", "value": "户外"},
        ],
        "styles": [
            {"label": "成分党", "value": "成分党"},
            {"label": "闺蜜聊天", "value": "闺蜜聊天"},
            {"label": "毒舌测评", "value": "毒舌测评"},
            {"label": "温柔种草", "value": "温柔种草"},
            {"label": "教程型", "value": "教程型"},
            {"label": "清单型", "value": "清单型"},
            {"label": "红黑榜型", "value": "红黑榜型"},
            {"label": "对比测评", "value": "对比测评"},
            {"label": "种草型", "value": "种草型"},
            {"label": "攻略型", "value": "攻略型"},
        ],
        "strategies": [
            {"label": "共鸣型", "value": "共鸣型"},
            {"label": "成分党", "value": "成分党"},
            {"label": "对比测评", "value": "对比测评"},
            {"label": "悬念型", "value": "悬念型"},
            {"label": "教程型", "value": "教程型"},
            {"label": "清单型", "value": "清单型"},
            {"label": "红黑榜型", "value": "红黑榜型"},
            {"label": "种草型", "value": "种草型"},
            {"label": "攻略型", "value": "攻略型"},
            {"label": "误区纠正型", "value": "误区纠正型"},
        ],
        "skeleton_types": [
            {"label": "通用型", "value": "通用型"},
            {"label": "测评对比型", "value": "测评对比型"},
            {"label": "红黑榜型", "value": "红黑榜型"},
            {"label": "误区纠正型", "value": "误区纠正型"},
            {"label": "教程步骤型", "value": "教程步骤型"},
        ],
        "fission_modes": [
            {"label": "换叶子（同构异内容）", "value": "replace_leaf", "desc": "L1+L5 替换，骨架不变，效果保留 ~85%"},
            {"label": "换表达（跨风格移植）", "value": "replace_style", "desc": "L2+L5 替换，骨架不变，效果保留 ~70%"},
            {"label": "换枝杈（同内容异结构）", "value": "replace_branch", "desc": "L3+L4 替换，主题不变，效果保留 ~65%"},
        ],
    }
