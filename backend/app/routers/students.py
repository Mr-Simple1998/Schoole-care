from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_points import PointRecord
from ..models_subject import Subject, StudentSubject
from ..security import get_current_user, is_head_role

router = APIRouter()


def _scope_student_query(q, current_user: User):
    """按角色限定学生数据范围：
    - 教师：只看自己负责的学生
    - 校区负责人（sub_principal / campus_head）：只看本校区全部学生
    - 总校长（principal）：归属校区后只看本校区；未归属校区（存量）看全机构
    """
    if current_user.role == UserRole.TEACHER:
        return q.filter(Student.teacher_id == current_user.id)
    if is_head_role(current_user.role):
        return q.filter(Student.campus_id == current_user.campus_id)
    if current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        return q.filter(Student.campus_id == current_user.campus_id)
    return q


def _check_student_scope(db: Session, current_user: User, student: Student):
    """校验单个学生是否在当前用户数据范围内"""
    if current_user.role == UserRole.TEACHER:
        if student.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能操作自己负责的学生")
    elif is_head_role(current_user.role):
        if student.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        if student.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")


class SubjectSessionIn(BaseModel):
    """新增/编辑学生时传入的学科课时配置"""
    subject_id: int
    total_sessions: int | None = None  # None = 不按课时核销，按到期时间
    duration_value: int | None = None  # 时长数值（不按课时核销时使用）
    duration_unit: str | None = None   # 时长单位：天/月/年
    expire_date: date | None = None    # 到期时间（保留字段，实际由首次打卡计算）


class StudentCreate(BaseModel):
    name: str
    gender: str | None = None
    school: str | None = None        # 学校信息
    grade: str | None = None
    class_name: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    teacher_id: int | None = None
    campus_id: int | None = None     # 所属校区（可选）
    enrollment_date: date | None = None
    notes: str | None = None
    subject_ids: list[int] | None = None       # 所属学科（可多选）
    subject_sessions: list[SubjectSessionIn] | None = None  # 学科课时配置


class StudentUpdate(BaseModel):
    name: str | None = None
    gender: str | None = None
    school: str | None = None
    grade: str | None = None
    class_name: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    teacher_id: int | None = None
    campus_id: int | None = None     # 所属校区（可选）
    enrollment_date: date | None = None
    status: str | None = None
    notes: str | None = None
    subject_ids: list[int] | None = None
    subject_sessions: list[SubjectSessionIn] | None = None


class SubjectOut(BaseModel):
    id: int
    name: str
    category: str

    class Config:
        from_attributes = True


class SubjectSessionOut(BaseModel):
    subject_id: int
    subject_name: str
    total_sessions: int | None = None    # None = 不按课时
    used_sessions: int = 0
    remaining: int | None = None         # None = 不按课时
    duration_value: int | None = None    # 时长数值
    duration_unit: str | None = None     # 时长单位：天/月/年
    expire_date: date | None = None      # 到期时间（首次打卡计算）


class StudentOut(BaseModel):
    id: int
    name: str
    student_no: str
    gender: str | None
    school: str | None = None
    grade: str | None
    class_name: str | None
    guardian_name: str | None
    guardian_phone: str | None
    teacher_id: int | None
    teacher_name: str | None = None
    campus_id: int | None = None
    campus_name: str | None = None
    enrollment_date: date | None
    status: str
    points: int
    notes: str | None
    subjects: list[SubjectOut] = []
    subject_sessions: list[SubjectSessionOut] = []

    class Config:
        from_attributes = True


def _student_out(student) -> StudentOut:
    out = StudentOut.model_validate(student)
    out.teacher_name = student.teacher.name if student.teacher else None
    out.campus_name = student.campus.name if student.campus else None
    # 学科课时信息
    out.subject_sessions = []
    for link in student.subject_links:
        total = link.total_sessions
        used = link.used_sessions or 0
        out.subject_sessions.append(SubjectSessionOut(
            subject_id=link.subject_id,
            subject_name=link.subject.name if link.subject else "",
            total_sessions=total,
            used_sessions=used,
            remaining=(total - used) if total is not None else None,
            duration_value=link.duration_value,
            duration_unit=link.duration_unit,
            expire_date=link.expire_date,
        ))
    return out


def _set_subjects(db: Session, student: Student, subject_ids: list[int] | None, subject_sessions: list | None = None):
    """更新学生学科关联及课时配置；subject_ids 为 None 表示不修改"""
    if subject_ids is None:
        return
    if len(subject_ids) != len(set(subject_ids)):
        raise HTTPException(status_code=400, detail="学科不能重复")
    subs = db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
    if len(subs) != len(subject_ids):
        raise HTTPException(status_code=400, detail="存在无效学科")

    # 构建课时配置映射
    session_map = {}
    duration_value_map = {}
    duration_unit_map = {}
    expire_map = {}
    if subject_sessions:
        for ss in subject_sessions:
            if hasattr(ss, 'subject_id'):
                session_map[ss.subject_id] = ss.total_sessions
                duration_value_map[ss.subject_id] = getattr(ss, 'duration_value', None)
                duration_unit_map[ss.subject_id] = getattr(ss, 'duration_unit', None)
                expire_map[ss.subject_id] = getattr(ss, 'expire_date', None)
            else:
                session_map[ss.get("subject_id")] = ss.get("total_sessions")
                duration_value_map[ss.get("subject_id")] = ss.get("duration_value")
                duration_unit_map[ss.get("subject_id")] = ss.get("duration_unit")
                expire_map[ss.get("subject_id")] = ss.get("expire_date")

    # 清除旧关联
    db.query(StudentSubject).filter(StudentSubject.student_id == student.id).delete()
    # 创建新关联
    for sub in subs:
        total = session_map.get(sub.id)
        exp = expire_map.get(sub.id)
        link = StudentSubject(
            student_id=student.id,
            subject_id=sub.id,
            total_sessions=total,
            used_sessions=0,
            duration_value=duration_value_map.get(sub.id),
            duration_unit=duration_unit_map.get(sub.id),
            expire_date=exp,
        )
        db.add(link)


def _next_student_no(db: Session) -> str:
    last = db.query(Student).order_by(Student.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f"S{num:05d}"


@router.get("", response_model=list[StudentOut])
def list_students(
    subject_id: int | None = None,
    campus_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """教师仅见自己负责的学生；校区负责人见本校区全部学生；总校长归属校区后见本校区，未归属见全部。
    可按 subject_id / campus_id 筛选（campus_id=0 表示未分校区）"""
    q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
    q = _scope_student_query(q, current_user)
    # 仅未归属校区的总校长可跨校区筛选；其余角色数据范围已由 _scope_student_query 限定
    scoped = current_user.role == UserRole.TEACHER or is_head_role(current_user.role) or (
        current_user.role == UserRole.PRINCIPAL and current_user.campus_id
    )
    if campus_id is not None and not scoped:
        if campus_id == 0:
            q = q.filter(Student.campus_id.is_(None))
        else:
            q = q.filter(Student.campus_id == campus_id)
    if subject_id:
        q = q.join(StudentSubject, StudentSubject.student_id == Student.id).filter(
            StudentSubject.subject_id == subject_id
        )
    return [_student_out(s) for s in q.all()]


@router.get("/deleted")
def list_deleted_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """已删除学生列表：仅总校长可查看（归属校区后仅本校区）"""
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅总校长可查看已删除学生")
    q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == True)  # noqa: E712
    if current_user.campus_id:
        q = q.filter(Student.campus_id == current_user.campus_id)
    return [_student_out(s) for s in q.order_by(Student.id.desc()).all()]


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id, Student.org_id == current_user.org_id, Student.deleted == False).first()  # noqa: E712
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    return _student_out(student)


@router.post("", response_model=StudentOut)
def create_student(data: StudentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = data.model_dump(exclude={"subject_ids", "subject_sessions"})
    # 教师添加的学生自动归属到该教师名下并默认归属其校区；校区负责人添加的学生默认归属其校区
    if current_user.role == UserRole.TEACHER:
        payload["teacher_id"] = current_user.id
        if payload.get("campus_id") is None:
            payload["campus_id"] = current_user.campus_id
    elif is_head_role(current_user.role):
        payload["campus_id"] = current_user.campus_id
        if payload.get("teacher_id") is not None:
            # 校区负责人只能指定本校区教师
            t = db.query(User).filter(User.id == payload["teacher_id"], User.org_id == current_user.org_id).first()
            if not t or t.campus_id != current_user.campus_id:
                raise HTTPException(status_code=400, detail="只能指定本校区教师")
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        payload["campus_id"] = current_user.campus_id
    student = Student(**payload, student_no=_next_student_no(db), status="在读", org_id=current_user.org_id)
    db.add(student)
    db.flush()  # 获取 student.id 以创建关联
    _set_subjects(db, student, data.subject_ids, data.subject_sessions)
    db.commit()
    db.refresh(student)
    return _student_out(student)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id, Student.org_id == current_user.org_id, Student.deleted == False).first()  # noqa: E712
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    for k, v in data.model_dump(exclude_unset=True, exclude={"subject_ids", "subject_sessions"}).items():
        setattr(student, k, v)
    if "subject_ids" in data.model_dump(exclude_unset=True):
        _set_subjects(db, student, data.subject_ids, data.subject_sessions)
    db.commit()
    db.refresh(student)
    return _student_out(student)


@router.delete("/{student_id}")
def delete_student(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """软删除学生：两端同步隐藏该学生，清除其积分数据；保留收费管理（流水/账单/分期）历史记录。"""
    student = db.query(Student).filter(Student.id == student_id, Student.org_id == current_user.org_id).first()
    if not student or student.deleted:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    # 清除积分数据（积分记录 + 余额）
    db.query(PointRecord).filter(
        PointRecord.student_id == student.id, PointRecord.org_id == current_user.org_id
    ).delete(synchronize_session=False)
    student.points = 0
    student.deleted = True
    db.commit()
    return {"detail": "已删除"}