from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, Student, User, UserRole
from ..models_income import FeeRecord, Invoice
from ..models_learning import Score, Attendance, TeacherAttendance
from ..models_subject import StudentSubject, Subject
from ..models_points import PointRecord
from ..security import get_current_user, is_head_role, managed_campus_ids

router = APIRouter()

REMIND_DAYS = 7  # 提前 7 天提醒机构即将到期
FEE_REMIND_DAYS = 5  # 提前 5 天提醒学生费用即将到期


def _scope_students(q, db: Session, current_user: User):
    """按角色限定学生数据范围（教师=自己负责；校区负责人=管辖校区（可多校区）；总校长归属校区后=本校区）"""
    if current_user.role == UserRole.TEACHER:
        return q.filter(Student.teacher_id == current_user.id)
    if is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        return q.filter(Student.campus_id.in_(managed))
    if current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        return q.filter(Student.campus_id == current_user.campus_id)
    return q


def _is_finance_visible(current_user: User) -> bool:
    """是否可查看收入数据：教师不可见（收入置 0），校区负责人/总校长可见"""
    return current_user.role != UserRole.TEACHER


def _org_expire_info(db: Session, org_id: int):
    """返回机构到期信息，供校长端提醒"""
    if not org_id:
        return None
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None
    today = date.today()
    days = (org.expire_date - today).days if org.expire_date else None
    status = "none"
    if org.expire_date:
        if days < 0:
            status = "expired"
        elif days <= REMIND_DAYS:
            status = "expiring"
        else:
            status = "normal"
    return {
        "name": org.name,
        "expire_date": org.expire_date.isoformat() if org.expire_date else None,
        "days_left": days,
        "status": status,
        "plan_type": org.plan_type,
        "fee_amount": org.fee_amount or 0,
    }


@router.get("/overview")
def dashboard_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """工作台总览统计"""
    student_q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
    student_q = _scope_students(student_q, db, current_user)

    total_students = student_q.count()
    today = datetime.utcnow().date()

    # 本月收入（教师不可见机构收入，置 0）
    month_start = today.replace(day=1)
    if not _is_finance_visible(current_user):
        month_income = 0
    else:
        month_income = db.query(func.coalesce(func.sum(FeeRecord.amount), 0)).filter(
            FeeRecord.pay_date >= month_start, FeeRecord.org_id == current_user.org_id
        ).scalar() or 0

    # 总欠费
    overdue = db.query(Invoice).filter(Invoice.status.in_(["待缴", "部分缴纳"]), Invoice.org_id == current_user.org_id).all()
    total_unpaid = 0
    for inv in overdue:
        total_unpaid += (inv.amount - inv.paid_amount)

    # 今日考勤
    today_att_q = db.query(Attendance).filter(Attendance.date == today, Attendance.org_id == current_user.org_id)
    today_att_q = _scope_students(today_att_q, db, current_user)
    today_attendance = today_att_q.count()

    # 待缴账单数
    pending_invoices = len(overdue)

    # 积分总记录数
    point_records = db.query(PointRecord).filter(PointRecord.org_id == current_user.org_id).count()

    # 费用到期提醒（每个学生取最近一条收费记录，到期/即将到期即提醒）
    fee_reminders = _fee_expire_reminders(db, current_user, today)

    return {
        "total_students": total_students,
        "month_income": round(month_income, 2),
        "total_unpaid": round(total_unpaid, 2),
        "today_attendance": today_attendance,
        "pending_invoices": pending_invoices,
        "point_records": point_records,
        "role": current_user.role,
        "org_expire": _org_expire_info(db, current_user.org_id),
        "fee_expire_reminders": fee_reminders,
    }


def _fee_expire_reminders(db: Session, current_user: User, today: date):
    """返回费用到期提醒列表。总校长看全部（归属校区后看本校区），校区负责人看本校区，教师只看自己负责的学生。"""
    student_q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
    student_q = _scope_students(student_q, db, current_user)
    students = student_q.all()
    if not students:
        return []

    student_ids = [s.id for s in students]
    student_map = {s.id: s for s in students}
    teacher_ids = {s.teacher_id for s in students if s.teacher_id}
    teachers = {u.id: u for u in db.query(User).filter(User.id.in_(teacher_ids)).all()} if teacher_ids else {}

    reminders = []

    # 1. 收费记录到期提醒
    for sid in student_ids:
        last_fee = db.query(FeeRecord).filter(
            FeeRecord.student_id == sid,
            FeeRecord.org_id == current_user.org_id,
        ).order_by(FeeRecord.pay_date.desc(), FeeRecord.id.desc()).first()
        if not last_fee or not last_fee.expire_date:
            continue
        days_left = (last_fee.expire_date - today).days
        if days_left <= FEE_REMIND_DAYS:
            st = student_map.get(sid)
            t = teachers.get(st.teacher_id) if st else None
            reminders.append({
                "student_id": sid,
                "student_name": st.name if st else "",
                "teacher_name": t.name if t else "",
                "teacher_phone": t.phone if t else "",
                "fee_type": last_fee.fee_type,
                "amount": last_fee.amount,
                "expire_date": last_fee.expire_date.isoformat(),
                "days_left": days_left,
                "remind_type": "fee",
            })

    # 2. 学科课时到期提醒（不按课时核销的学科，有到期时间则提醒）
    expire_links = db.query(StudentSubject, Subject).join(
        Subject, StudentSubject.subject_id == Subject.id
    ).filter(
        StudentSubject.student_id.in_(student_ids),
        StudentSubject.total_sessions == None,  # noqa: E711
        StudentSubject.expire_date != None,  # noqa: E711
        StudentSubject.expire_date <= today + timedelta(days=FEE_REMIND_DAYS),
    ).all()

    for link, sub in expire_links:
        st = student_map.get(link.student_id)
        if not st:
            continue
        days_left = (link.expire_date - today).days
        t = teachers.get(st.teacher_id) if st else None
        reminders.append({
            "student_id": link.student_id,
            "student_name": st.name,
            "teacher_name": t.name if t else "",
            "teacher_phone": t.phone if t else "",
            "fee_type": f"{sub.name}到期",
            "amount": 0,
            "expire_date": link.expire_date.isoformat(),
            "days_left": days_left,
            "remind_type": "subject",
        })

    reminders.sort(key=lambda x: x["days_left"])
    return reminders


@router.get("/org-expire")
def org_expire(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """当前校长/教师所属机构的到期提醒信息"""
    return _org_expire_info(db, current_user.org_id)


@router.get("/attendance-summary")
def attendance_summary(
    month: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """月度考勤汇总：
    - 教师：汇总自己名下全部学生的考勤（含每日明细供日历展示）+ 自己的上下班打卡
    - 校区负责人：只汇总本校区全部教师上下班打卡（上班未按时打卡整体标记「迟到」，不再展示全部学生）
    - 总校长：不展示学生/教师打卡信息
    """
    today = date.today()
    if month and len(month) == 7:
        try:
            y, m = int(month[:4]), int(month[5:7])
        except ValueError:
            y, m = today.year, today.month
    else:
        y, m = today.year, today.month
    start = date(y, m, 1)
    end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    is_current_month = (y == today.year and m == today.month)

    # 总校长不需要展示学生/教师打卡信息（本校区教师考勤由校区负责人负责查看）
    if current_user.role == UserRole.PRINCIPAL:
        return {
            "month": f"{y:04d}-{m:02d}",
            "students": [],
            "teachers": [],
            "summary": {
                "student_count": 0,
                "student_attendance_count": 0,
                "teacher_count": 0,
                "teacher_late_count": 0,
                "teacher_absent_count": 0,
            },
        }

    # ---- 学生考勤汇总（仅教师可见；校区负责人不再展示本校区全部学生）----
    students = []
    student_summary = []
    att_records = []
    if not is_head_role(current_user.role):
        student_q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
        student_q = _scope_students(student_q, db, current_user)
        students = student_q.all()
        student_ids = [s.id for s in students]
        if student_ids:
            att_records = db.query(Attendance).filter(
                Attendance.org_id == current_user.org_id,
                Attendance.student_id.in_(student_ids),
                Attendance.date >= start,
                Attendance.date < end,
            ).order_by(Attendance.date, Attendance.id).all()
        name_map = {s.id: s.name for s in students}
        by_student: dict[int, dict] = {}
        for r in att_records:
            b = by_student.setdefault(r.student_id, {"normal": 0, "late": 0, "absent": 0, "leave": 0, "early": 0, "total": 0, "records": []})
            key = {"正常": "normal", "迟到": "late", "缺勤": "absent", "请假": "leave", "早退": "early"}.get(r.status, "normal")
            b[key] += 1
            b["total"] += 1
            b["records"].append({"date": r.date.isoformat(), "status": r.status})
        student_summary = [
            {"student_id": sid, "student_name": name_map.get(sid, ""), **counts}
            for sid, counts in by_student.items()
        ]

    # ---- 教师上下班考勤汇总（整体标记）----
    if current_user.role == UserRole.TEACHER:
        teacher_list = [current_user]
    elif is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        teacher_list = db.query(User).filter(
            User.org_id == current_user.org_id,
            User.campus_id.in_(managed),
            User.role == UserRole.TEACHER,
            User.resigned == False,  # noqa: E712
        ).all()
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        teacher_list = db.query(User).filter(
            User.org_id == current_user.org_id,
            User.campus_id == current_user.campus_id,
            User.role == UserRole.TEACHER,
            User.resigned == False,  # noqa: E712
        ).all()
    else:
        teacher_list = db.query(User).filter(
            User.org_id == current_user.org_id,
            User.role == UserRole.TEACHER,
            User.resigned == False,  # noqa: E712
        ).all()

    def _day_status(r, ws, we):
        if r.time_in and ws and r.time_in > ws:
            return "迟到"
        if r.time_out and we and r.time_out < we:
            return "早退"
        return "正常"

    teacher_summary = []
    for t in teacher_list:
        recs = db.query(TeacherAttendance).filter(
            TeacherAttendance.org_id == current_user.org_id,
            TeacherAttendance.user_id == t.id,
            TeacherAttendance.date >= start,
            TeacherAttendance.date < end,
        ).all()
        rec_map = {r.date: r for r in recs}
        normal = late = early = absent = 0
        records = []
        if t.work_start_time:
            # 有排班：按工作日（周一~周五）计算应打卡天数，未打卡标记「缺勤」
            weekdays = set()
            d = start
            last = today if is_current_month else (end - timedelta(days=1))
            while d <= last:
                if d.weekday() < 5:
                    weekdays.add(d)
                d += timedelta(days=1)
            processed = set()
            for d in sorted(weekdays):
                r = rec_map.get(d)
                if not r or not r.time_in:
                    absent += 1
                    records.append({"date": d.isoformat(), "status": "缺勤", "time_in": r.time_in if r else None, "time_out": r.time_out if r else None})
                else:
                    st = _day_status(r, t.work_start_time, t.work_end_time)
                    if st == "迟到":
                        late += 1
                    elif st == "早退":
                        early += 1
                    else:
                        normal += 1
                    records.append({"date": d.isoformat(), "status": st, "time_in": r.time_in, "time_out": r.time_out})
                processed.add(d)
            # 非工作日（如周末）若有实际打卡，也展示（不计缺勤）
            for r in recs:
                if r.date not in processed:
                    st = _day_status(r, t.work_start_time, t.work_end_time)
                    if st == "迟到":
                        late += 1
                    elif st == "早退":
                        early += 1
                    else:
                        normal += 1
                    records.append({"date": r.date.isoformat(), "status": st, "time_in": r.time_in, "time_out": r.time_out})
            records.sort(key=lambda x: x["date"])
        else:
            # 无排班：仅按实际打卡记录汇总
            for r in sorted(recs, key=lambda x: x.date):
                st = _day_status(r, t.work_start_time, t.work_end_time)
                if st == "迟到":
                    late += 1
                elif st == "早退":
                    early += 1
                else:
                    normal += 1
                records.append({"date": r.date.isoformat(), "status": st, "time_in": r.time_in, "time_out": r.time_out})
        teacher_summary.append({
            "user_id": t.id,
            "teacher_name": t.name,
            "username": t.username,
            "work_start": t.work_start_time,
            "work_end": t.work_end_time,
            "normal": normal,
            "late": late,
            "early": early,
            "absent": absent,
            "total": len(records),
            "records": records,
        })

    return {
        "month": f"{y:04d}-{m:02d}",
        "students": student_summary,
        "teachers": teacher_summary,
        "summary": {
            "student_count": len(students),
            "student_attendance_count": len(att_records),
            "teacher_count": len(teacher_list),
            "teacher_late_count": sum(t["late"] for t in teacher_summary),
            "teacher_absent_count": sum(t["absent"] for t in teacher_summary),
        },
    }


@router.get("/recent-income")
def recent_income(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """近14天每日收入"""
    end = datetime.utcnow().date()
    start = end - timedelta(days=13)
    q = db.query(FeeRecord).filter(FeeRecord.pay_date >= start, FeeRecord.org_id == current_user.org_id)
    if current_user.role == UserRole.TEACHER:
        q = q.join(Student).filter(Student.teacher_id == current_user.id)
    elif is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        q = q.join(Student).filter(Student.campus_id.in_(managed))
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        q = q.join(Student).filter(Student.campus_id == current_user.campus_id)
    records = q.all()
    buckets = {}
    for i in range(14):
        d = start + timedelta(days=i)
        buckets[d.isoformat()] = 0
    for r in records:
        key = r.pay_date.isoformat()
        if key in buckets:
            buckets[key] += r.amount
    return [{"date": d, "amount": a} for d, a in buckets.items()]