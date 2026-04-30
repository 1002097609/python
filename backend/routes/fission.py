from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.fission import Fission
from ..models.skeleton import Skeleton

router = APIRouter()


class FissionRequest(BaseModel):
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
    # 获取骨架
    skeleton = db.query(Skeleton).filter(Skeleton.id == data.skeleton_id).first()
    if not skeleton:
        raise HTTPException(status_code=404, detail="骨架不存在")

    import json

    structure = skeleton.structure_json
    elements = skeleton.elements_json
    strategy = skeleton.strategy_desc

    if isinstance(structure, str):
        structure = json.loads(structure)
    if isinstance(elements, str):
        elements = json.loads(elements)

    replacement = data.replacement or {}

    # 根据裂变模式组合输出
    output_content = _generate_output(
        fission_mode=data.fission_mode,
        structure=structure,
        elements=elements,
        strategy=strategy,
        new_topic=data.new_topic or "",
        replacement=replacement,
    )

    # 效果预测
    prediction = _predict_performance(skeleton, data.fission_mode)

    # 保存裂变记录
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
        output_status=0,
        predicted_ctr=prediction["ctr"],
        predicted_roi=prediction["roi"],
    )
    db.add(fission)

    # 更新骨架使用次数
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
    """模板填充引擎"""
    content = []
    if isinstance(structure, list):
        for section in structure:
            section_name = section.get("name", "")
            section_func = section.get("function", "")
            content.append(f"【{section_name} — {section_func}】")

            if fission_mode == "replace_leaf":
                # 替换 L1 + L5，骨架不变
                if section_name in ("开头", "痛点共鸣"):
                    content.append(f"打工人！{new_topic}相关问题是不是？")
                elif section_name in ("主体", "卖点"):
                    golden = replacement.get("L5", {}).get("golden_sentences", [])
                    if golden:
                        content.append(golden[0])
                elif section_name in ("结尾", "互动"):
                    content.append("评论区告诉我你的情况，我帮你选！")
                else:
                    content.append(f"[请填写{section_name}内容]")
            content.append("")
    return "\n".join(content)


def _predict_performance(skeleton, fission_mode) -> dict:
    """基于母体骨架效果预测"""
    base_roi = float(skeleton.avg_roi or 2.0)
    base_ctr = float(skeleton.avg_ctr or 1.5)

    factors = {
        "replace_leaf": 0.85,
        "replace_branch": 0.65,
        "replace_style": 0.70,
    }
    factor = factors.get(fission_mode, 0.7)

    return {
        "ctr": f"{base_ctr * factor * 0.9:.1f}%-{base_ctr * factor * 1.1:.1f}%",
        "roi": f"{base_roi * factor * 0.8:.1f}x-{base_roi * factor * 1.1:.1f}x",
    }
