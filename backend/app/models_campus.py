"""校区模型：校区（分校区）与手工收支登记"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship

from .models import Base


class Campus(Base):
    """校区（校长名下机构的分支）"""
    __tablename__ = "campuses"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    name = Column(String(100), nullable=False)          # 校区名称
    address = Column(String(200), nullable=True)        # 地址
    phone = Column(String(20), nullable=True)           # 联系电话
    remark = Column(String(255), nullable=True)         # 备注
    status = Column(Boolean, default=True)              # 启用/停用
    created_at = Column(DateTime, default=datetime.utcnow)

    heads = relationship("CampusHead", back_populates="campus", cascade="all, delete-orphan")


class CampusHead(Base):
    """校区负责人关联表：一个校区可有多名负责人（可多选，选项含校长）"""
    __tablename__ = "campus_heads"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    campus = relationship("Campus", back_populates="heads")
    user = relationship("User")


class CampusTransaction(Base):
    """校区手工收支登记（学费收入按学生校区自动归属，这里登记非学费收入与支出）"""
    __tablename__ = "campus_transactions"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False, index=True)   # 所属校区
    kind = Column(String(10), nullable=False)           # income 收入 / expense 支出
    category = Column(String(50), nullable=False)       # 分类：餐费/杂费/其他（收入）；房租/工资/水电/其他（支出）
    amount = Column(Float, nullable=False)              # 金额
    record_date = Column(Date, nullable=False)          # 发生日期
    remark = Column(String(255), nullable=True)         # 备注
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 登记人
    created_at = Column(DateTime, nullable=True)

    campus = relationship("Campus")
