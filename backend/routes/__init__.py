"""
路由模块初始化文件（routes/__init__.py）。

该模块负责创建统一的路由入口 api_router，并将各业务子路由注册到对应路径前缀下。
包含以下子路由模块：
  - material:    素材管理（/api/material）
  - dismantle:   拆解引擎（/api/dismantle）
  - skeleton:    骨架库（/api/skeleton）
  - fission:     裂变引擎（/api/fission）
  - effect:      效果数据（/api/effect）
  - options:     选项数据（旧版，/api/options）
  - option:      选项数据（新版，/api/option）

所有子路由统一挂载在 /api 前缀下，由 FastAPI 主应用在启动时引用本模块的 api_router。
"""

from fastapi import APIRouter
from .material import router as material_router
from .dismantle import router as dismantle_router
from .skeleton import router as skeleton_router
from .fission import router as fission_router
from .effect import router as effect_router
from .options import router as options_router
from .option import router as option_router
from .tag import router as tag_router

# 创建统一的 API 路由器，所有子路由统一使用 /api 前缀
api_router = APIRouter(prefix="/api")

# 注册素材管理路由：处理素材的增删改查
api_router.include_router(material_router, prefix="/material", tags=["素材管理"])

# 注册拆解引擎路由：处理素材的 L1-L5 拆解操作
api_router.include_router(dismantle_router, prefix="/dismantle", tags=["拆解引擎"])

# 注册骨架库路由：管理从拆解结果中提取的可复用骨架
api_router.include_router(skeleton_router, prefix="/skeleton", tags=["骨架库"])

# 注册裂变引擎路由：基于骨架+新内容组合批量产出新素材
api_router.include_router(fission_router, prefix="/fission", tags=["裂变引擎"])

# 注册效果数据路由：录入和查询投放效果数据（CTR、ROI 等）
api_router.include_router(effect_router, tags=["效果数据"])

# 注册选项数据路由（旧版兼容）：按分组返回下拉框选项
api_router.include_router(options_router, prefix="/options", tags=["选项数据(旧)"])

# 注册选项数据路由（新版）：提供更完整的 CRUD 操作
api_router.include_router(option_router, prefix="/option", tags=["选项数据"])

# 注册标签管理路由：标签 CRUD + 素材标签关联
api_router.include_router(tag_router, prefix="/tag", tags=["标签管理"])
