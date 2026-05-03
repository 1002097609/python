"""
拆解引擎路由模块（routes/dismantle.py）。

提供素材的五层拆解（L1-L5）相关接口，负责将营销素材从抽象到具体逐层拆分为：
  L1 主题层、L2 策略层、L3 结构层、L4 元素层、L5 表达层。
拆解完成后，素材状态自动更新为"已拆解"。

路由列表：
  POST /api/dismantle/                     - 创建拆解记录
  GET  /api/dismantle/{id}                 - 根据拆解 ID 查询拆解详情
  GET  /api/dismantle/by-material/{id}     - 根据素材 ID 查询对应的拆解记录
  PUT  /api/dismantle/{id}                 - 更新拆解记录
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.dismantle import Dismantle
from ..models.material import Material
from ..schemas.dismantle import DismantleCreate, DismantleUpdate, DismantleResponse
from ..services.ai_dismantle import analyze_material

# 创建拆解引擎专用路由器
router = APIRouter()


@router.post("/", response_model=DismantleResponse, status_code=201)
def create_dismantle(data: DismantleCreate, db: Session = Depends(get_db)):
    """
    为指定素材创建 L1-L5 拆解记录。

    首先校验关联素材是否存在，若存在则创建拆解记录，并将素材状态更新为"已拆解"（status=1）。
    素材与拆解记录为一对一关系。

    请求参数：
        data (DismantleCreate): 拆解数据模型，包含 material_id 和 L1-L5 各层字段。

    返回值：
        DismantleResponse: 创建成功的拆解记录对象。

    异常：
        HTTP 404: 当关联的素材 ID 不存在时抛出。
    """
    # 校验关联素材是否存在，确保拆解操作的数据完整性
    material = db.query(Material).filter(Material.id == data.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 创建拆解 ORM 实例并写入数据库
    dismantle = Dismantle(**data.model_dump())
    db.add(dismantle)

    # 同步更新素材状态为"已拆解"（1=已拆解，0=未拆解）
    material.status = 1

    db.commit()
    db.refresh(dismantle)
    return dismantle


@router.get("/{dismantle_id}", response_model=DismantleResponse)
def get_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    """
    根据拆解记录 ID 查询拆解详情。

    请求参数：
        dismantle_id (int): 拆解记录的唯一标识 ID。

    返回值：
        DismantleResponse: 完整的拆解记录，包含 L1-L5 各层数据。

    异常：
        HTTP 404: 当拆解记录不存在时抛出。
    """
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")
    return dismantle


@router.get("/by-material/{material_id}", response_model=DismantleResponse)
def get_dismantle_by_material(material_id: int, db: Session = Depends(get_db)):
    """
    根据素材 ID 查询对应的拆解记录。

    由于素材与拆解记录为一对一关系，此接口通过素材 ID 直接定位拆解数据，
    方便前端在查看素材详情时直接获取拆解信息。

    请求参数：
        material_id (int): 素材的唯一标识 ID。

    返回值：
        DismantleResponse: 该素材对应的拆解记录。

    异常：
        HTTP 404: 当该素材尚未拆解或素材不存在时抛出。
    """
    dismantle = db.query(Dismantle).filter(Dismantle.material_id == material_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="该素材尚未拆解")
    return dismantle


@router.get("/by-material/{material_id}/history")
def get_dismantle_history(material_id: int, db: Session = Depends(get_db)):
    """
    查询指定素材的所有拆解历史版本。

    返回该素材关联的所有拆解记录（含已归档的历史版本），
    按创建时间倒序排列，最近的版本在前。

    请求参数：
        material_id (int): 素材的唯一标识 ID。

    返回值:
        list[DismantleResponse]: 历史拆解记录列表。
    """
    items = db.query(Dismantle).filter(
        Dismantle.material_id == material_id
    ).order_by(Dismantle.created_at.desc()).all()
    return items


@router.put("/{dismantle_id}", response_model=DismantleResponse)
def update_dismantle(dismantle_id: int, data: DismantleUpdate, db: Session = Depends(get_db)):
    """
    更新拆解记录。支持部分更新（仅传入需要修改的字段）。

    可用于人工修正 AI 辅助拆解后的各层数据，或补充 skeleton_id 关联信息。

    请求参数：
        dismantle_id (int):        要更新的拆解记录 ID。
        data (DismantleUpdate):    更新模型，所有字段均为可选。

    返回值：
        DismantleResponse: 更新后的完整拆解记录。

    异常：
        HTTP 404: 当拆解记录不存在时抛出。
    """
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")

    # 仅更新调用方实际传入的字段（exclude_unset=True 保证部分更新语义）
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dismantle, key, value)

    db.commit()
    db.refresh(dismantle)
    return dismantle


# ============================================================
# AI 辅助拆解
# ============================================================

class AiAnalyzeRequest(BaseModel):
    """AI 辅助拆解请求模型"""
    title: str
    content: str
    platform: Optional[str] = ""
    category: Optional[str] = ""


class AiAnalyzeResponse(BaseModel):
    """AI 辅助拆解响应模型"""
    l1_topic: Optional[str] = None
    l1_core_point: Optional[str] = None
    l2_strategy: Optional[list] = None
    l2_emotion: Optional[str] = None
    l3_structure: Optional[list] = None
    l4_elements: Optional[dict] = None
    l5_expressions: Optional[dict] = None
    _meta: Optional[dict] = None


@router.post("/ai-analyze", response_model=AiAnalyzeResponse)
def ai_analyze_dismantle(
    data: AiAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    AI 辅助拆解接口。

    根据素材标题和内容，自动分析生成 L1-L5 五层拆解数据。
    返回的拆解数据可直接用于填充拆解表单，用户可在此基础上人工修正。

    请求参数：
        title (str):     素材标题（必填）
        content (str):   素材内容/脚本（必填）
        platform (str):  投放平台（可选）
        category (str):  品类（可选，不传则自动检测）

    返回值：
        AiAnalyzeResponse: L1-L5 拆解数据 + 元信息（检测到的品类、结构类型等）

    注意：
        此接口仅生成拆解数据，不保存到数据库。
        前端获取结果后，用户确认/修正后调用 POST /api/dismantle/ 保存。
    """
    if not data.title and not data.content:
        raise HTTPException(status_code=400, detail="标题和内容不能同时为空")

    result = analyze_material(
        title=data.title or "",
        content=data.content or "",
        platform=data.platform or "",
        category=data.category or "",
    )

    # 校验 meta 中的 category 是否存在于 option 表
    if result.get("_meta", {}).get("detected_category"):
        from ..models.option import Option
        cat = result["_meta"]["detected_category"]
        existing_cat = db.query(Option).filter(
            Option.group_key == "category", Option.value == cat, Option.is_active == 1
        ).first()
        if not existing_cat:
            result["_meta"]["detected_category"] = "通用"

    return AiAnalyzeResponse(**result)
