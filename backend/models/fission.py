"""
裂变模型模块

定义 Fission（裂变）ORM 模型，对应数据库中的 fission 表。
裂变是将骨架与新内容组合，产出新素材的过程。支持三种裂变模式：
  - replace_leaf: 换叶子（替换 L1+L5），最可靠，效果保留约 85%
  - replace_branch: 换枝杈（替换 L3+L4），效果保留约 65%
  - replace_style: 换表达（替换 L2+L5），效果保留约 70%

主要字段：
  id: 自增主键
  skeleton_id: 使用的骨架 ID
  source_material_id: 母体素材 ID（可选）
  fission_mode: 裂变模式（三种之一）
  new_topic / new_category / new_platform / new_style: 新内容参数
  replacement_json: 替换内容映射（详细的替换规则）
  output_title / output_content: 裂变产出的素材标题和内容
  output_status: 产出素材状态（草稿/待审核/已采用/已投放）
  predicted_ctr / predicted_roi: 基于骨架历史数据的预测值
  actual_ctr / actual_roi: 投放后的实际效果数据
  created_by: 创建人
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, JSON, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class Fission(Base):
    """
    裂变表（fission）

    记录一次裂变操作的完整信息：使用了哪个骨架、采用了哪种裂变模式、
    产出了什么内容、预测效果和实际效果如何。

    裂变流程：
      1. 选择骨架（skeleton_id）
      2. 选择裂变模式（fission_mode）
      3. 输入新主题/品类/风格等参数
      4. 引擎根据骨架模板 + 替换内容生成新素材
      5. output_status 跟踪素材从草稿到投放的状态流转
      6. 投放后回写 actual_ctr / actual_roi 形成效果闭环

    关联关系：
      - skeleton_id -> skeleton.id （使用的骨架）
      - source_material_id -> material.id （可选，母体素材）
      - 投放后可关联 effect_data 表的记录
    """

    __tablename__ = "fission"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 使用的骨架 ID，非空，指定本次裂变基于哪个内容骨架
    skeleton_id = Column(Integer, ForeignKey("skeleton.id", ondelete="CASCADE"), nullable=False, comment="使用的骨架 ID")

    # 母体素材 ID（可选），指明本次裂变是在哪个现有素材基础上进行的
    source_material_id = Column(Integer, ForeignKey("material.id", ondelete="SET NULL"), comment="母体素材 ID")

    # 裂变模式：
    # replace_leaf = 换叶子（替换主题+表达，骨架不变，效果保留约 85%）
    # replace_branch = 换枝杈（替换结构+元素，主题不变，效果保留约 65%）
    # replace_style = 换表达（替换策略+表达，骨架不变，效果保留约 70%）
    fission_mode = Column(String(50), comment="裂变模式：replace_leaf/replace_branch/replace_style")

    # 新主题的 L1 描述内容，用于替换原骨架的主题层
    new_topic = Column(String(200), comment="新主题")

    # 新品类标识，用于替换原素材的品类标签
    new_category = Column(String(50), comment="新品类")

    # 新投放平台，用于跨平台迁移
    new_platform = Column(String(50), comment="新平台")

    # 新风格标签，用于调整内容风格
    new_style = Column(String(50), comment="新风格")

    # 替换内容映射（JSON），详细描述需要替换的模块和新内容
    # 示例：{"l5_expressions":{"golden_sentences":["新金句1","新金句2"]},"l1_topic":"新主题描述"}
    replacement_json = Column(JSON, comment="替换内容映射")

    # 裂变产出的素材标题
    output_title = Column(String(200), comment="产出素材标题")

    # 裂变产出的完整素材内容（脚本/文案等）
    output_content = Column(Text, comment="产出素材内容")

    # 产出素材的状态流转：
    # 0 = 草稿（刚生成，待人工确认）
    # 1 = 待审核（已提交，等待审核）
    # 2 = 已采用（审核通过，准备投放）
    # 3 = 已投放（正在投放中，可回写效果数据）
    output_status = Column(Integer, default=0, comment="0=草稿 1=待审核 2=已采用 3=已投放")

    # 预测点击率范围，基于骨架历史 avg_ctr 计算
    predicted_ctr = Column(String(20), comment="预测 CTR 范围")

    # 预测 ROI 范围，基于骨架历史 avg_roi 计算
    predicted_roi = Column(String(20), comment="预测 ROI 范围")

    # 投放后的实际点击率（可选，投放结束后由 effect_data 回写）
    actual_ctr = Column(DECIMAL(5, 2), comment="实际 CTR%")

    # 投放后的实际 ROI（可选，投放结束后由 effect_data 回写）
    actual_roi = Column(DECIMAL(5, 2), comment="实际 ROI")

    # 创建人标识
    created_by = Column(String(50))

    # 创建时间，自动设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 索引：按骨架 ID、产出状态、母体素材加速查询
    __table_args__ = (
        Index("idx_fission_skeleton", "skeleton_id"),          # 查找某个骨架的所有裂变记录
        Index("idx_fission_status", "output_status"),          # 按产出状态筛选
        Index("idx_fission_source_material", "source_material_id"),  # 按母体素材查找
    )
