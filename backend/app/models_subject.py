from datetime import datetime

from datetime import date

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Table
from sqlalchemy.orm import relationship

from .models import Base, Student, User


# 教师-学科 多对多关联表（教师所属学科）
teacher_subjects = Table(
    "teacher_subjects",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id"), primary_key=True),
)


class Subject(Base):
    """学科分类：学科类（语文/数学/英语/托管）与非学科类（魔方/书法/画画/轮滑）"""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)  # 所属机构
    name = Column(String(30), nullable=False)
    category = Column(String(20), default="学科")   # 学科 / 非学科
    sort = Column(Integer, default=0)                # 排序
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_links = relationship("StudentSubject", back_populates="subject")


class StudentSubject(Base):
    """学生-学科关联（含课时配置）"""
    __tablename__ = "student_subjects"

    student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), primary_key=True)
    total_sessions = Column(Integer, nullable=True)   # 总课时（NULL=不按课时核销，按到期时间）
    used_sessions = Column(Integer, default=0)        # 已核销课时
    duration_value = Column(Integer, nullable=True)   # 时长数值（不按课时核销时使用）
    duration_unit = Column(String(10), nullable=True) # 时长单位：天/月/年
    expire_date = Column(Date, nullable=True)          # 到期时间（首次打卡时按 时长 计算）

    student = relationship("Student", back_populates="subject_links")
    subject = relationship("Subject", back_populates="student_links")


# 在学生模型上挂载关系（跨模块，避免 models.py 依赖本模块）
Student.subjects = relationship(
    "Subject",
    secondary="student_subjects",
    backref="students",
    viewonly=True,
)
Student.subject_links = relationship("StudentSubject", back_populates="student")

# 在教师(用户)模型上挂载多对多关系：教师所属学科
User.subjects = relationship(
    "Subject",
    secondary=teacher_subjects,
    backref="teachers",
)