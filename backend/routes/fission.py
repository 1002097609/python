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
    prediction = _predict_performance(skeleton, data.fission_mode)

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
        output_title=f"{data.new_topic or '未命名'} — 裂变产出",
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

    当前实现了 replace_leaf（换叶子）模式：
      - 开头/痛点共鸣部分：自动将新主题嵌入模板句式
      - 主体/卖点部分：从 replacement 参数提取替换的金句
      - 结尾/互动部分：使用固定的互动引导语
      - 其余段落：输出占位符提示用户手动填写

    其他模式（replace_branch、replace_style）暂未实现完整逻辑，

    参数：
        fission_mode (str):  裂变模式，决定替换哪些层级。
        structure (list):    L3 结构层数据，包含各段落名称和功能描述。
        elements (dict):     L4 元素层数据，包含可插拔的元素（标题公式、钩子等）。
        strategy (str):      L2 策略层描述。
        new_topic (str):     新主题/品类名称，用于替换原主题内容。
        replacement (dict):  自定义替换内容字典。

    返回值：
        str: 填充后的素材文案，段落之间用换行符分隔。
    """
    content = []

    # 遍历结构层中的每个段落，逐段填充内容
    if isinstance(structure, list):
        for section in structure:
            section_name = section.get("name", "")        # 段落名称，如"开头"、"主体"
            section_func = section.get("function", "")     # 段落功能描述，如"痛点共鸣"
            content.append(f"【{section_name} — {section_func}】")

            # replace_leaf 模式：保持骨架（L2-L4）不变，替换 L1（主题）和 L5（表达）
            if fission_mode == "replace_leaf":
                # 开头段落：用新主题生成共鸣句式
                if section_name in ("开头", "痛点共鸣"):
                    content.append(f"打工人！{new_topic}相关问题是不是？")
                # 主体段落：从 replacement 中提取用户提供的新金句
                elif section_name in ("主体", "卖点"):
                    golden = replacement.get("L5", {}).get("golden_sentences", [])
                    if golden:
                        content.append(golden[0])  # 取第一条金句作为主体内容
                # 结尾段落：使用引导互动的固定话术
                elif section_name in ("结尾", "互动"):
                    content.append("评论区告诉我你的情况，我帮你选！")
                # 其他未处理的段落：输出占位符提示人工填写
                else:
                    content.append(f"[请填写{section_name}内容]")
            content.append("")

    return "\n".join(content)


def _predict_performance(skeleton, fission_mode) -> dict:
    """
    效果预测函数：基于母体骨架的历史平均效果数据，乘以裂变模式系数，预测新素材的表现范围。

    预测逻辑：
      1. 取骨架的 avg_roi 和 avg_ctr 作为基准值
      2. 根据裂变模式查表获取保留系数（replace_leaf=0.85, replace_branch=0.65, replace_style=0.70）
      3. 以 +/-10% 的波动范围给出预测区间

    参数：
        skeleton (Skeleton): 骨架 ORM 对象，需包含 avg_roi 和 avg_ctr 字段。
        fission_mode (str):  裂变模式，决定效果保留比例。

    返回值：
        dict: 包含两个预测字段：
            - ctr: 预测点击率范围字符串，格式 "X.X%-X.X%"
            - roi: 预测 ROI 范围字符串，格式 "X.Xx-X.Xx"
    """
    # 读取骨架的历史平均效果指标，若无数据则使用默认值
    base_roi = float(skeleton.avg_roi or 2.0)    # 默认 ROI 基准值 2.0x
    base_ctr = float(skeleton.avg_ctr or 1.5)    # 默认 CTR 基准值 1.5%

    # 不同裂变模式对应的效果保留系数（根据业务经验预设）
    factors = {
        "replace_leaf": 0.85,    # 换叶子：仅替换内容和表达，保留约 85% 效果
        "replace_branch": 0.65,  # 换枝杈：替换结构和元素，保留约 65% 效果
        "replace_style": 0.70,   # 换表达：替换策略和表达，保留约 70% 效果
    }
    factor = factors.get(fission_mode, 0.7)  # 未知模式使用保守系数 0.7

    # 计算预测范围：中心值 = 基准值 * 系数，波动范围为 +/-10%
    return {
        "ctr": f"{base_ctr * factor * 0.9:.1f}%-{base_ctr * factor * 1.1:.1f}%",
        "roi": f"{base_roi * factor * 0.8:.1f}x-{base_roi * factor * 1.1:.1f}x",
    }
