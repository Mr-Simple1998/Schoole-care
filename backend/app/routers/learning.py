import csv
import io
from datetime import date as DateType, datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_learning import Score, Attendance, Homework, ClassPerformance
from ..models_income import FeeRecord
from ..models_subject import StudentSubject, Subject
from ..security import get_current_user, is_head_role

router = APIRouter()


def _filter_teacher(db, query, current_user, student_id_field=None):
    """教师角色：只允许查询自己负责的学生；校区负责人：本校区全部学生"""
    if current_user.role == UserRole.TEACHER:
        query = query.join(Student).filter(Student.teacher_id == current_user.id)
    elif is_head_role(current_user.role):
        query = query.join(Student).filter(Student.campus_id == current_user.campus_id)
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        query = query.join(Student).filter(Student.campus_id == current_user.campus_id)
    return query


def _check_student_teacher(db, student_id, current_user):
    """教师角色：校验学生是否归自己负责；校区负责人：校验学生是否在本校区"""
    if current_user.role == UserRole.TEACHER:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or student.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能操作自己负责的学生")
    elif is_head_role(current_user.role):
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or student.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or student.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")
    return


# ---------- 成绩 ----------
class ScoreCreate(BaseModel):
    student_id: int
    subject: str
    exam_type: str = "平时考"
    score: float
    full_score: float = 100
    exam_date: DateType | None = None
    remark: str | None = None


class ScoreOut(BaseModel):
    id: int
    student_id: int
    subject: str
    exam_type: str
    score: float
    full_score: float
    exam_date: DateType | None
    remark: str | None

    class Config:
        from_attributes = True


@router.post("/scores", response_model=ScoreOut)
def create_score(data: ScoreCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_student_teacher(db, data.student_id, current_user)
    s = Score(**data.model_dump(), created_by=current_user.id, org_id=current_user.org_id, created_at=datetime.utcnow())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/scores", response_model=list[ScoreOut])
def list_scores(student_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Score).filter(Score.org_id == current_user.org_id)
    q = _filter_teacher(db, q, current_user)
    if student_id:
        q = q.filter(Score.student_id == student_id)
    return q.order_by(Score.exam_date.desc()).all()


@router.get("/scores/trend/{student_id}")
def score_trend(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """某学生各科成绩趋势"""
    _check_student_teacher(db, student_id, current_user)
    scores = db.query(Score).filter(Score.org_id == current_user.org_id, Score.student_id == student_id).order_by(Score.exam_date).all()
    result = {}
    for s in scores:
        result.setdefault(s.subject, []).append({
            "exam_type": s.exam_type,
            "score": s.score,
            "date": s.exam_date.isoformat() if s.exam_date else None,
        })
    return result


# ---------- 考勤 ----------
class AttendCreate(BaseModel):
    student_id: int
    subject_id: int | None = None   # 打卡学科（按学科核销课时）
    date: DateType
    status: str = "正常"
    time_in: str | None = None
    time_out: str | None = None
    remark: str | None = None


class AttendOut(BaseModel):
    id: int
    student_id: int
    subject_id: int | None = None
    subject_name: str | None = None
    date: DateType
    status: str
    time_in: str | None
    time_out: str | None
    remark: str | None

    class Config:
        from_attributes = True


def _add_duration(start: DateType, value: int, unit: str) -> DateType:
    """按 天/月/年 给日期加时长，返回结果日期"""
    if unit == "天":
        return start + timedelta(days=value)
    if unit == "年":
        value *= 12
    # 月（含由年换算的月）
    y = start.year + (start.month - 1 + value) // 12
    m = (start.month - 1 + value) % 12 + 1
    day = min(start.day, [31, 29 if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return DateType(y, m, day)


def _apply_duration_expire(link, first_date):
    """非核销课时学科：按首次打卡日期 + 时长 计算并写入到期时间"""
    start = first_date if isinstance(first_date, DateType) else DateType.fromisoformat(str(first_date))
    link.expire_date = _add_duration(start, int(link.duration_value), link.duration_unit)


@router.post("/attendance", response_model=AttendOut)
def create_attendance(data: AttendCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_student_teacher(db, data.student_id, current_user)
    # 检查当天是否已打卡（同一学生+同一天+同一学科 唯一）
    existing = db.query(Attendance).filter(
        Attendance.org_id == current_user.org_id,
        Attendance.student_id == data.student_id,
        Attendance.date == data.date,
        Attendance.subject_id == data.subject_id,
    ).first()
    if existing:
        detail = "该学生今天已打卡，一天只能打卡一次"
        if data.subject_id:
            sub = db.query(Subject).filter(Subject.id == data.subject_id).first()
            detail = f"该学生今天已在「{sub.name if sub else '未知'}」学科打卡，同一天同一学科只能打卡一次"
        raise HTTPException(status_code=400, detail=detail)
    a = Attendance(**data.model_dump(), created_by=current_user.id, org_id=current_user.org_id)
    db.add(a)
    db.commit()
    db.refresh(a)

    # 打卡成功后自动核销课时
    session_msg = ""
    if data.subject_id:
        # 按学科核销课时
        link = db.query(StudentSubject).filter(
            StudentSubject.student_id == data.student_id,
            StudentSubject.subject_id == data.subject_id,
        ).first()
        if link and link.total_sessions is not None:
            if link.total_sessions > (link.used_sessions or 0):
                link.used_sessions = (link.used_sessions or 0) + 1
                db.commit()
                remaining = link.total_sessions - link.used_sessions
                sub = db.query(Subject).filter(Subject.id == data.subject_id).first()
                session_msg = f"，已核销「{sub.name if sub else '未知'}」1次课时（剩余 {remaining} 次）"
            else:
                session_msg = "，该学科课时已用完"
        else:
            # 该学科未设置课时，按到期时间判断（使用 FeeRecord）
            # 首次打卡：若配置了时长且未计算到期日，则按 打卡日期 + 时长 计算到期时间
            if link and link.duration_value and link.duration_unit and not link.expire_date:
                _apply_duration_expire(link, data.date)
                db.commit()
            fee = db.query(FeeRecord).filter(
                FeeRecord.student_id == data.student_id,
                FeeRecord.org_id == current_user.org_id,
                FeeRecord.total_sessions.isnot(None),
            ).filter(FeeRecord.total_sessions > FeeRecord.used_sessions).order_by(FeeRecord.pay_date.asc()).first()
            if fee:
                fee.used_sessions = (fee.used_sessions or 0) + 1
                db.commit()
                remaining = fee.total_sessions - fee.used_sessions
                session_msg = f"，已核销1次课程（剩余 {remaining} 次）"
    else:
        # 未选择学科，使用旧的 FeeRecord 核销逻辑（向后兼容）
        fee = db.query(FeeRecord).filter(
            FeeRecord.student_id == data.student_id,
            FeeRecord.org_id == current_user.org_id,
            FeeRecord.total_sessions.isnot(None),
        ).filter(FeeRecord.total_sessions > FeeRecord.used_sessions).order_by(FeeRecord.pay_date.asc()).first()
        if fee:
            fee.used_sessions = (fee.used_sessions or 0) + 1
            db.commit()
            remaining = fee.total_sessions - fee.used_sessions
            session_msg = f"，已核销1次课程（剩余 {remaining} 次）"

    # 把学科名称回填到返回结果
    result = AttendOut.model_validate(a)
    if a.subject_id:
        sub = db.query(Subject).filter(Subject.id == a.subject_id).first()
        result.subject_name = sub.name if sub else None
    return result


@router.get("/attendance", response_model=list[AttendOut])
def list_attendance(student_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Attendance).filter(Attendance.org_id == current_user.org_id)
    q = _filter_teacher(db, q, current_user)
    if student_id:
        q = q.filter(Attendance.student_id == student_id)
    return q.order_by(Attendance.date.desc()).all()


# ---------- 作业 ----------
class HomeworkCreate(BaseModel):
    student_id: int
    subject: str
    content: str | None = None
    assign_date: DateType | None = None
    complete_status: str = "未完成"
    score: int | None = None
    remark: str | None = None


class HomeworkOut(BaseModel):
    id: int
    student_id: int
    subject: str
    content: str | None
    assign_date: DateType | None
    complete_status: str
    score: int | None
    remark: str | None

    class Config:
        from_attributes = True


@router.post("/homework", response_model=HomeworkOut)
def create_homework(data: HomeworkCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_student_teacher(db, data.student_id, current_user)
    h = Homework(**data.model_dump(), created_by=current_user.id, org_id=current_user.org_id, created_at=datetime.utcnow())
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


@router.get("/homework", response_model=list[HomeworkOut])
def list_homework(student_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Homework).filter(Homework.org_id == current_user.org_id)
    q = _filter_teacher(db, q, current_user)
    if student_id:
        q = q.filter(Homework.student_id == student_id)
    return q.order_by(Homework.assign_date.desc()).all()


# ---------- 课堂表现 ----------
class PerfCreate(BaseModel):
    student_id: int
    date: DateType | None = None
    performance_type: str = "纪律"
    rating: int = 3
    comment: str | None = None


class PerfOut(BaseModel):
    id: int
    student_id: int
    date: DateType | None
    performance_type: str
    rating: int
    comment: str | None

    class Config:
        from_attributes = True


@router.post("/performances", response_model=PerfOut)
def create_performance(data: PerfCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_student_teacher(db, data.student_id, current_user)
    p = ClassPerformance(**data.model_dump(), created_by=current_user.id, org_id=current_user.org_id, created_at=datetime.utcnow())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/performances", response_model=list[PerfOut])
def list_performances(student_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(ClassPerformance).filter(ClassPerformance.org_id == current_user.org_id)
    q = _filter_teacher(db, q, current_user)
    if student_id:
        q = q.filter(ClassPerformance.student_id == student_id)
    return q.order_by(ClassPerformance.created_at.desc()).all()


# ---------- 成绩单导出（CSV） ----------
@router.get("/transcript/{student_id}/export")
def export_transcript(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """导出某学生成绩单为 CSV（UTF-8 BOM，Excel 可直接打开）"""
    _check_student_teacher(db, student_id, current_user)
    student = db.query(Student).filter(Student.id == student_id, Student.deleted == False).first()  # noqa: E712
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    scores = db.query(Score).filter(Score.org_id == current_user.org_id, Score.student_id == student_id)\
        .order_by(Score.exam_date, Score.subject).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["姓名", "学号", "年级", "班级", "科目", "考试类型", "得分", "满分", "考试日期", "备注"])
    for s in scores:
        writer.writerow([
            student.name, student.student_no, student.grade or "", student.class_name or "",
            s.subject, s.exam_type, s.score, s.full_score,
            s.exam_date.isoformat() if s.exam_date else "", s.remark or "",
        ])
    filename = f"{student.name}_成绩单.csv"
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


# ---------- 考勤统计报表 ----------
@router.get("/attendance/stats")
def attendance_stats(
    student_id: int | None = None,
    start_date: DateType | None = None,
    end_date: DateType | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """考勤统计报表：状态占比 + 按学生汇总 + 每日明细"""
    q = db.query(Attendance).filter(Attendance.org_id == current_user.org_id)
    q = _filter_teacher(db, q, current_user)
    if student_id:
        q = q.filter(Attendance.student_id == student_id)
    if start_date:
        q = q.filter(Attendance.date >= start_date)
    if end_date:
        q = q.filter(Attendance.date <= end_date)
    records = q.order_by(Attendance.date).all()

    # 状态统计
    status_counts = {}
    for r in records:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    total = len(records)
    normal = status_counts.get("正常", 0)
    attendance_rate = round(normal / total * 100, 1) if total else 0.0

    # 每日明细
    by_date = []
    for r in records:
        st = db.query(Student).filter(Student.id == r.student_id).first()
        by_date.append({
            "date": r.date.isoformat(),
            "student_id": r.student_id,
            "student_name": st.name if st else "",
            "status": r.status,
            "time_in": r.time_in,
            "time_out": r.time_out,
            "remark": r.remark,
        })

    # 按学生汇总（未指定学生时）
    by_student = {}
    if not student_id:
        for r in records:
            bucket = by_student.setdefault(r.student_id, {"normal": 0, "late": 0, "absent": 0, "leave": 0, "early": 0, "total": 0})
            bucket[r.status] = bucket.get(r.status, 0) + 1
            bucket["total"] += 1
    by_student = [{
        "student_id": sid,
        "student_name": (db.query(Student).filter(Student.id == sid).first().name if db.query(Student).filter(Student.id == sid).first() else ""),
        **stats,
    } for sid, stats in by_student.items()]

    return {
        "total": total,
        "status_counts": status_counts,
        "attendance_rate": attendance_rate,
        "by_date": by_date,
        "by_student": by_student,
    }