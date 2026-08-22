from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from .models_income import *  # noqa: F401,F403
from .models import Base, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Date, Text


class Score(Base):
    """学生成绩"""
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String(30), nullable=False)     # 科目：语文/数学/英语...
    exam_type = Column(String(30), default="平时考")  # 平时考/期中/期末
    score = Column(Float, nullable=False)
    full_score = Column(Float, default=100)
    exam_date = Column(Date, nullable=True)
    remark = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    fee_record_id = Column(Integer, ForeignKey("fee_records.id"), nullable=True)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="scores")


class Attendance(Base):
    """考勤打卡"""
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)  # 打卡学科（按学科核销课时）
    date = Column(Date, nullable=False)
    status = Column(String(20), default="正常")      # 正常/迟到/早退/请假/缺勤
    time_in = Column(String(10), nullable=True)      # 到校时间 HH:MM
    time_out = Column(String(10), nullable=True)     # 离校时间
    remark = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    student = relationship("Student", back_populates="attendances")


class TeacherAttendance(Base):
    """教师上下班打卡记录（校区负责人设置上下班时间后，教师在工作台打卡）"""
    __tablename__ = "teacher_attendances"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 教师账号
    date = Column(Date, nullable=False)
    time_in = Column(String(10), nullable=True)      # 上班打卡时间 HH:MM
    time_out = Column(String(10), nullable=True)     # 下班打卡时间 HH:MM
    status = Column(String(20), default="正常")      # 正常/迟到/早退/缺勤（汇总时整体标记）
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True)

    user = relationship("User")


class Homework(Base):
    """作业管理"""
    __tablename__ = "homework"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String(30), nullable=False)
    content = Column(Text, nullable=True)            # 作业内容
    assign_date = Column(Date, nullable=True)        # 布置日期
    complete_status = Column(String(20), default="未完成")  # 未完成/已完成/优秀
    score = Column(Integer, nullable=True)           # 评分
    remark = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="homework")


class ClassPerformance(Base):
    """课堂表现"""
    __tablename__ = "class_performances"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=True)
    performance_type = Column(String(30), default="纪律")  # 纪律/参与度/积极性/态度
    rating = Column(Integer, default=3)              # 1-5 星
    comment = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="class_performances")
