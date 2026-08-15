from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from .models import Base
from .models import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date, Text


class FeeRecord(Base):
    """收费记录 / 流水"""
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_type = Column(String(50), nullable=False)   # 学费/餐费/杂费/其他
    amount = Column(Float, nullable=False)          # 金额
    pay_date = Column(Date, nullable=False)         # 缴费日期
    payment_method = Column(String(30), default="现金")  # 现金/转账/微信/支付宝
    payment_period = Column(String(20), nullable=True)   # 缴费时间段：一月/半学期/一年
    expire_date = Column(Date, nullable=True)            # 到期日期（由缴费日期+时间段推算）
    total_sessions = Column(Integer, nullable=True)      # 课程总次数（按次核销时使用）
    used_sessions = Column(Integer, default=0)           # 已核销次数
    remark = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="fee_records")


class Invoice(Base):
    """账单（应收款）"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    item = Column(String(100), nullable=False)      # 账单项目
    amount = Column(Float, nullable=False)          # 应收金额
    due_date = Column(Date, nullable=True)          # 应缴日期
    status = Column(String(20), default="待缴")     # 待缴/部分缴纳/已缴清/已减免
    paid_amount = Column(Float, default=0)          # 已缴金额
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="invoices")


class RefundAdjustment(Base):
    """退费/减免记录"""
    __tablename__ = "refund_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    kind = Column(String(20), default="减免")       # 减免/退费
    amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student")


class Installment(Base):
    """学费分期计划"""
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    title = Column(String(100), nullable=False)      # 分期名称，如：暑期学费分期
    total_amount = Column(Float, nullable=False)     # 总金额
    periods = Column(Integer, default=1)             # 期数
    paid_periods = Column(Integer, default=0)        # 已还期数
    status = Column(String(20), default="进行中")    # 进行中/已完成
    start_date = Column(Date, nullable=True)
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student")


class InstallmentRecord(Base):
    """分期还款记录"""
    __tablename__ = "installment_records"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    installment_id = Column(Integer, ForeignKey("installments.id"), nullable=False)
    period_no = Column(Integer, nullable=False)      # 第几期
    amount = Column(Float, nullable=False)           # 本期金额
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    status = Column(String(20), default="待缴")      # 待缴/已缴
    remark = Column(String(255), nullable=True)

    installment = relationship("Installment")