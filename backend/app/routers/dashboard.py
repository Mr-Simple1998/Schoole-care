from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, Student, User, UserRole
from ..models_income import FeeRecord, Invoice
from ..models_learning import Score, Attendance
from ..models_subject import StudentSubject, Subject
from ..models_points import PointRecord
from ..security import get_current_user

router = APIRouter()

REMIND_DAYS = 7  # 提前 7 天提醒机构即将到期
FEE_REMIND_DAYS = 5  # 提前 5 天提醒学生费用即将到期


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
    if current_user.role == UserRole.TEACHER:
        student_q = student_q.filter(Student.teacher_id == current_user.id)

    total_students = student_q.count()
    today = datetime.utcnow().date()

    # 本月收入（教师不可见机构收入，置 0）
    month_start = today.replace(day=1)
    if current_user.role == UserRole.TEACHER:
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
    if current_user.role == UserRole.TEACHER:
        today_att_q = today_att_q.join(Student).filter(Student.teacher_id == current_user.id)
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
    """返回费用到期提醒列表。校长看全部学生，教师只看自己负责的学生。"""
    student_q = db.query(Student).filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
    if current_user.role == UserRole.TEACHER:
        student_q = student_q.filter(Student.teacher_id == current_user.id)
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


@router.get("/recent-income")
def recent_income(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """近14天每日收入"""
    end = datetime.utcnow().date()
    start = end - timedelta(days=13)
    q = db.query(FeeRecord).filter(FeeRecord.pay_date >= start, FeeRecord.org_id == current_user.org_id)
    if current_user.role == UserRole.TEACHER:
        q = q.join(Student).filter(Student.teacher_id == current_user.id)
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