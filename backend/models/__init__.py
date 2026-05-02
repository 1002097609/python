"""
模型包初始化模块

本模块统一导入并导出所有 SQLAlchemy ORM 模型类，
方便其他模块通过 `from backend.models import Material` 的方式引用，
避免逐个文件导入的繁琐。

包含的模型类：
  - Material: 素材表，存储原始营销素材
  - Dismantle: 拆解表，存储素材的 L1-L5 五层拆解数据
  - Skeleton: 骨架表，存储可复用的内容骨架
  - Fission: 裂变表，存储裂变配置和产出内容
  - EffectData: 效果数据表，回写投放数据
  - Tag / MaterialTag: 标签表及素材标签关联表
  - Option: 选项配置表，管理平台/品类/风格等枚举选项
"""

from .material import Material
from .dismantle import Dismantle
from .skeleton import Skeleton
from .fission import Fission
from .effect_data import EffectData
from .tag import Tag, MaterialTag
from .option import Option
from .operation_log import OperationLog

# __all__ 控制 `from backend.models import *` 时导出的符号
__all__ = ["Material", "Dismantle", "Skeleton", "Fission", "EffectData", "Tag", "MaterialTag", "Option", "OperationLog"]
