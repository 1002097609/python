from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.material import Material
from ..schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse

router = APIRouter()


@router.post("/", response_model=MaterialResponse, status_code=201)
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    material = Material(**data.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("/", response_model=list[MaterialResponse])
def list_materials(
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Material)
    if platform:
        query = query.filter(Material.platform == platform)
    if category:
        query = query.filter(Material.category == category)
    if status is not None:
        query = query.filter(Material.status == status)
    items = query.order_by(Material.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(material_id: int, data: MaterialUpdate, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(material, key, value)
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=204)
def delete_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")
    db.delete(material)
    db.commit()
