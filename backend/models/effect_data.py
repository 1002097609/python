"""
效果数据模型模块

定义 EffectData（效果数据）ORM 模型，对应数据库中的 effect_data 表。
用于存储素材在广告投放后的实际效果指标，形成"投放 -> 效果回写 -> 骨架优化"闭环。

主要字段：
  id: 自增主键
  material_id: 关联的原始素材 ID
  fission_id: 关联的裂变素材 ID（如果是裂变产出的话）
  platform: 投放平台
  impressions: 展示量，clicks: 点击量
  ctr: 点击率（%），conversions: 转化量，cvr: 转化率（%）
  cost: 花费（元），revenue: 收入（元）
  roi: 投资回报率，cpa: 单次转化成本
  stat_date: 数据统计日期
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index, DECIMAL
from sqlalchemy.sql import func
from backend.database import Base


class EffectData(Base):
    """
    效果数据表（effect_data）

    记录素材在各投放平台上的实际广告效果指标。
    每行记录对应某一天的投放汇总数据（按 stat_date 区分）。

    效果闭环：
      素材投放 -> 平台导出每日数据 -> 写入 effect_data ->
      -> 自动计算 ROI/CTR/CVR 等指标 ->
      -> 更新 fission.actual_ctr/actual_roi ->
      -> 更新 skeleton.avg_roi/avg_ctr ->
      -> 下次裂变时优先推荐高效果骨架

    关联关系：
      - material_id -> material.id （原始素材，可选）
      - fission_id -> fission.id （裂变素材，可选，至少关联一个）
    """

    __tablename__ = "effect_data"

    # 自增主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联的原始素材 ID（如果是直接投放原始素材而非裂变产出）
    material_id = Column(Integer, ForeignKey("material.id", ondelete="CASCADE"), comment="关联素材 ID")

    # 关联的裂变素材 ID（如果是裂变产出素材的投放数据）
    fission_id = Column(Integer, ForeignKey("fission.id", ondelete="CASCADE"), comment="关联裂变素材 ID")

    # 投放平台标识（如"抖音"、"小红书"等）
    platform = Column(String(50), comment="投放平台")

    # 广告展示量（曝光次数）
    impressions = Column(Integer, comment="展示量")

    # 广告点击量
    clicks = Column(Integer, comment="点击量")

    # 点击率（百分比），计算公式：CTR = clicks / impressions * 100
    ctr = Column(DECIMAL(5, 2), comment="点击率%")

    # 转化量（下单/留资等转化行为次数）
    conversions = Column(Integer, comment="转化量")

    # 转化率（百分比），计算公式：CVR = conversions / clicks * 100
    cvr = Column(DECIMAL(5, 2), comment="转化率%")

    # 广告花费（元），精确到分
    cost = Column(DECIMAL(10, 2), comment="花费（元）")

    # 投放带来的收入（元），精确到分
    revenue = Column(DECIMAL(10, 2), comment="收入（元）")

    # 投资回报率，计算公式：ROI = revenue / cost
    roi = Column(DECIMAL(5, 2), comment="ROI")

    # 单次转化成本（元），计算公式：CPA = cost / conversions
    cpa = Column(DECIMAL(10, 2), comment="单次转化成本")

    # 数据统计日期，用于区分同一素材不同日期的投放效果
    stat_date = Column(Date, comment="数据日期")

    # 创建时间，自动设置为当前时间
    created_at = Column(DateTime, server_default=func.now())

    # 索引：按素材 ID、裂变 ID、统计日期加速查询
    __table_args__ = (
        Index("idx_effect_material", "material_id"),  # 查询某原始素材的所有效果数据
        Index("idx_effect_fission", "fission_id"),    # 查询某裂变素材的所有效果数据
        Index("idx_effect_date", "stat_date"),         # 按日期范围查询（如近7天数据）
    )
