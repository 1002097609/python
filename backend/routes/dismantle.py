from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.dismantle import Dismantle
from ..models.material import Material
from ..schemas.dismantle import DismantleCreate, DismantleUpdate, DismantleResponse

router = APIRouter()


@router.post("/", response_model=DismantleResponse, status_code=201)
def create_dismantle(data: DismantleCreate, db: Session = Depends(get_db)):
    # 检查素材是否存在
    material = db.query(Material).filter(Material.id == data.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    dismantle = Dismantle(**data.model_dump())
    db.add(dismantle)

    # 更新素材状态为"已拆解"
    material.status = 1

    db.commit()
    db.refresh(dismantle)
    return dismantle


@router.get("/{dismantle_id}", response_model=DismantleResponse)
def get_dismantle(dismantle_id: int, db: Session = Depends(get_db)):
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")
    return dismantle


@router.get("/by-material/{material_id}", response_model=DismantleResponse)
def get_dismantle_by_material(material_id: int, db: Session = Depends(get_db)):
    dismantle = db.query(Dismantle).filter(Dismantle.material_id == material_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="该素材尚未拆解")
    return dismantle


@router.put("/{dismantle_id}", response_model=DismantleResponse)
def update_dismantle(dismantle_id: int, data: DismantleUpdate, db: Session = Depends(get_db)):
    dismantle = db.query(Dismantle).filter(Dismantle.id == dismantle_id).first()
    if not dismantle:
        raise HTTPException(status_code=404, detail="拆解记录不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dismantle, key, value)
    db.commit()
    db.refresh(dismantle)
    return dismantle
