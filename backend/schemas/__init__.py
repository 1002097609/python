"""
数据校验模式模块初始化文件（schemas/__init__.py）。

该模块统一导出所有 Pydantic Schema 类，供路由层（routes）使用。
Schema 用于请求参数的自动校验、响应数据的序列化以及 OpenAPI 文档的自动生成。

当前导出的 Schema 包括：
  - MaterialCreate / MaterialUpdate / MaterialResponse     : 素材相关
  - DismantleCreate / DismantleUpdate / DismantleResponse  : 拆解相关
  - SkeletonCreate / SkeletonUpdate / SkeletonResponse     : 骨架相关
"""

from .material import MaterialCreate, MaterialUpdate, MaterialResponse
from .dismantle import DismantleCreate, DismantleUpdate, DismantleResponse
from .skeleton import SkeletonCreate, SkeletonUpdate, SkeletonResponse

__all__ = [
    "MaterialCreate", "MaterialUpdate", "MaterialResponse",
    "DismantleCreate", "DismantleUpdate", "DismantleResponse",
    "SkeletonCreate", "SkeletonUpdate", "SkeletonResponse",
]
