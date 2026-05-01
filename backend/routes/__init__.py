from fastapi import APIRouter
from .material import router as material_router
from .dismantle import router as dismantle_router
from .skeleton import router as skeleton_router
from .fission import router as fission_router
from .effect import router as effect_router
from .options import router as options_router

api_router = APIRouter(prefix="/api")
api_router.include_router(material_router, prefix="/material", tags=["素材管理"])
api_router.include_router(dismantle_router, prefix="/dismantle", tags=["拆解引擎"])
api_router.include_router(skeleton_router, prefix="/skeleton", tags=["骨架库"])
api_router.include_router(fission_router, prefix="/fission", tags=["裂变引擎"])
api_router.include_router(effect_router, tags=["效果数据"])
api_router.include_router(options_router, prefix="/options", tags=["选项数据"])
