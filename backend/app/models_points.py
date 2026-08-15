from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from .models_learning import *  # noqa: F401,F403
from .models import Base, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date, Text


class PointRecord(Base):
    """积分加扣记录"""
    __tablename__ = "point_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    change = Column(Integer, nullable=False)         # 积分变动，正为加负为扣
    reason = Column(String(255), nullable=True)      # 原因
    category = Column(String(30), default="表现")     # 表现/作业/成绩/纪律/兑换/其他
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=None, nullable=True)

    student = relationship("Student", back_populates="point_records")


class PointSetting(Base):
    """积分规则配置"""
    __tablename__ = "point_settings"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    name = Column(String(100), nullable=False)       # 规则名
    category = Column(String(30), default="表现")
    change = Column(Integer, nullable=False)         # 默认积分值
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)


class Prize(Base):
    """积分可兑换奖品"""
    __tablename__ = "prizes"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    cost_points = Column(Integer, nullable=False)    # 所需积分
    stock = Column(Integer, default=0)               # 库存，-1 表示不限
    image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=True)


class Redemption(Base):
    """积分兑换记录"""
    __tablename__ = "redemptions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    prize_id = Column(Integer, ForeignKey("prizes.id"), nullable=False)
    cost_points = Column(Integer, nullable=False)
    status = Column(String(20), default="已兑换")     # 已兑换/已领取/已取消
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student")
    prize = relationship("Prize")