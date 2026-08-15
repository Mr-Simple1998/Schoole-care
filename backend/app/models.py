from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from .database import Base


# 计费方式
PLAN_TYPES = {
    "annual": "按年",
    "stage": "按次/阶段",
    "custom": "自定义",
}


class UserRole(str, Enum):
    PLATFORM = "platform"      # 平台超级管理员（开户）
    PRINCIPAL = "principal"    # 总校长（机构创始人，平台开户创建；操作限自己校区，可看全校只读总览）
    SUB_PRINCIPAL = "sub_principal"  # 校区负责人（校长管理号，总校长在校区管理页开号；仅看本校区）
    TEACHER = "teacher"        # 教师
    CAMPUS_HEAD = "campus_head"  # 校区负责人（旧角色，与新 sub_principal 同一套权限逻辑，存量兼容）


class Organization(Base):
    """机构（每个校长对应一个机构，数据相互隔离）"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)          # 机构名称
    code = Column(String(50), unique=True, index=True, nullable=False)  # 机构编码
    contact = Column(String(50), nullable=True)          # 联系人
    phone = Column(String(20), nullable=True)
    status = Column(Boolean, default=True)               # 启用/停用
    # --- 交费与到期 ---
    plan_type = Column(String(20), nullable=True)        # 计费方式：annual/stage/custom
    payment_period = Column(String(20), nullable=True)   # 交费时间段：半年/一年
    fee_amount = Column(Float, default=0)                # 当前期交费金额
    total_paid = Column(Float, default=0)                # 累计交费金额（开户流水合计）
    expire_date = Column(Date, nullable=True)            # 账号到期日期（由交费时间段自动推算）
    last_paid_at = Column(DateTime, nullable=True)       # 最近一次交费时间
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    payments = relationship("Payment", back_populates="organization", order_by="Payment.id.desc()")


class Payment(Base):
    """机构开户/续费流水"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True, nullable=False)  # 所属机构
    amount = Column(Float, default=0)                    # 本次流水金额
    plan_type = Column(String(20), nullable=True)        # 计费方式
    payment_period = Column(String(20), nullable=True)   # 交费时间段：半年/一年
    expire_date = Column(Date, nullable=True)            # 本次到期日期
    remark = Column(String(200), nullable=True)          # 备注
    created_at = Column(DateTime, default=datetime.utcnow)  # 交费时间

    organization = relationship("Organization", back_populates="payments")


class User(Base):
    """平台管理员、校长和教师账号"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # 密码哈希
    name = Column(String(50), nullable=False)            # 显示姓名
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.TEACHER)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 所属机构
    avatar = Column(String(255), nullable=True)          # 头像图片路径
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    wx_openid = Column(String(64), nullable=True, index=True)  # 微信小程序 openid（本地开发模式存模拟值）
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=True, index=True)  # 所属校区（教师/校区负责人）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    campus = relationship("Campus")
    students = relationship("Student", back_populates="teacher")


class Student(Base):
    """学生信息"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    student_no = Column(String(30), unique=True, index=True, nullable=False)  # 学号
    gender = Column(String(10), nullable=True)
    school = Column(String(100), nullable=True)         # 学校信息
    grade = Column(String(20), nullable=True)          # 年级
    class_name = Column(String(50), nullable=True)     # 班级/托管班
    guardian_name = Column(String(50), nullable=True)  # 监护人
    guardian_phone = Column(String(20), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 负责教师
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=True, index=True)  # 所属校区（可选）
    enrollment_date = Column(Date, nullable=True)      # 入学日期
    status = Column(String(20), default="在读")        # 在读/休学/退学
    points = Column(Integer, default=0)                # 积分余额
    deleted = Column(Boolean, default=False)           # 软删除标记（保留收费管理历史数据）
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User", back_populates="students")
    campus = relationship("Campus")
    fee_records = relationship("FeeRecord", back_populates="student")
    invoices = relationship("Invoice", back_populates="student")
    scores = relationship("Score", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    homework = relationship("Homework", back_populates="student")
    class_performances = relationship("ClassPerformance", back_populates="student")
    point_records = relationship("PointRecord", back_populates="student")


# 确保校区模型注册（避免循环导入；models_campus 从本模块导入 Base）
from . import models_campus  # noqa: E402,F401