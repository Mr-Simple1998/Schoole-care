from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, Payment, User, UserRole, PLAN_TYPES, Student
from ..models_income import FeeRecord, Invoice
from ..models_campus import CampusTransaction
from ..models_learning import Attendance
from ..security import get_current_platform, hash_password

router = APIRouter()

REMIND_DAYS = 7  # 提前 7 天提醒即将到期

# 交费时间段 -> 有效天数
PAYMENT_PERIOD_DAYS = {
    "半年": 180,
    "一年": 365,
}


def _calc_expire(period: str | None, base: date | None = None) -> date | None:
    """由交费时间段推算到期日期。base 缺省用开户当日（今天）；若传 base 则在 base 基础上顺延。"""
    if not period or period not in PAYMENT_PERIOD_DAYS:
        return None
    base = base or date.today()
    return base + timedelta(days=PAYMENT_PERIOD_DAYS[period])


class OrgCreate(BaseModel):
    """平台开户：创建机构 + 校长账号"""
    org_name: str
    org_code: str | None = None        # 机构编码，缺省自动生成
    contact: str | None = None         # 校长姓名
    phone: str | None = None
    username: str                      # 校长登录账号
    password: str                      # 校长登录密码
    # 开户交费
    plan_type: str | None = None       # 计费方式
    payment_period: str | None = None  # 交费时间段：半年/一年
    fee_amount: float | None = None    # 交费金额


class OrgUpdate(BaseModel):
    name: str | None = None
    contact: str | None = None
    phone: str | None = None
    status: bool | None = None


class PrincipalReset(BaseModel):
    password: str


class RenewData(BaseModel):
    """续费 / 追加流水"""
    plan_type: str | None = None
    payment_period: str | None = None  # 交费时间段：半年/一年
    amount: float | None = None
    remark: str | None = None


def _gen_code(db: Session) -> str:
    n = db.query(Organization).count() + 1
    code = f"ORG{n:03d}"
    while db.query(Organization).filter(Organization.code == code).first():
        n += 1
        code = f"ORG{n:03d}"
    return code


def _expire_status(org: Organization) -> str:
    """到期状态：normal 正常 / expiring 即将到期 / expired 已到期 / none 未设置"""
    if not org.expire_date:
        return "none"
    today = date.today()
    days = (org.expire_date - today).days
    if days < 0:
        return "expired"
    if days <= REMIND_DAYS:
        return "expiring"
    return "normal"


def _org_overview(db: Session, org_id: int, month_start: date, today: date) -> dict:
    """机构运营概况（平台超级管理员视角）：资金（本月收支/待缴）+ 教师 + 学生 + 今日打卡"""
    # 学生
    student_count = db.query(Student).filter(Student.org_id == org_id, Student.deleted == False).count()  # noqa: E712
    active_student_count = db.query(Student).filter(
        Student.org_id == org_id, Student.deleted == False, Student.status == "在读"  # noqa: E712
    ).count()
    # 教师（含校区负责人/校区负责人）
    teacher_count = db.query(User).filter(
        User.org_id == org_id,
        User.is_active == True,  # noqa: E712
        User.role.in_([UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
    ).count()
    # 本月资金：学费收入（按缴费日期）+ 手工收支（按登记日期）
    tuition = db.query(func.coalesce(func.sum(FeeRecord.amount), 0)).filter(
        FeeRecord.org_id == org_id,
        FeeRecord.pay_date >= month_start,
    ).scalar() or 0
    manual_income = db.query(func.coalesce(func.sum(CampusTransaction.amount), 0)).filter(
        CampusTransaction.org_id == org_id,
        CampusTransaction.kind == "income",
        CampusTransaction.record_date >= month_start,
    ).scalar() or 0
    manual_expense = db.query(func.coalesce(func.sum(CampusTransaction.amount), 0)).filter(
        CampusTransaction.org_id == org_id,
        CampusTransaction.kind == "expense",
        CampusTransaction.record_date >= month_start,
    ).scalar() or 0
    # 今日打卡
    today_attendance = db.query(Attendance).filter(
        Attendance.date == today, Attendance.org_id == org_id
    ).count()
    # 待缴（应收未收）
    invs = db.query(Invoice).filter(
        Invoice.org_id == org_id,
        Invoice.status.in_(["待缴", "部分缴纳"]),
    ).all()
    unpaid = sum((inv.amount or 0) - (inv.paid_amount or 0) for inv in invs)

    month_income = round(float(tuition) + float(manual_income), 2)
    month_expense = round(float(manual_expense), 2)
    return {
        "student_count": student_count,
        "active_student_count": active_student_count,
        "teacher_count": teacher_count,
        "month_income": month_income,
        "month_expense": month_expense,
        "month_balance": round(month_income - month_expense, 2),
        "today_attendance": today_attendance,
        "unpaid": round(unpaid, 2),
    }


def _org_out(o: Organization, db: Session):
    principal = (
        db.query(User)
        .filter(User.org_id == o.id, User.role == UserRole.PRINCIPAL, User.is_active == True)  # noqa: E712
        .first()
    )
    expire_date = o.expire_date
    today = date.today()
    month_start = today.replace(day=1)
    return {
        "id": o.id,
        "name": o.name,
        "code": o.code,
        "contact": o.contact,
        "phone": o.phone,
        "status": o.status,
        "plan_type": o.plan_type,
        "plan_type_text": PLAN_TYPES.get(o.plan_type, ""),
        "payment_period": o.payment_period,
        "fee_amount": o.fee_amount or 0,
        "total_paid": o.total_paid or 0,
        "expire_date": expire_date.isoformat() if expire_date else None,
        "expire_status": _expire_status(o),
        "days_left": (expire_date - date.today()).days if expire_date else None,
        "last_paid_at": o.last_paid_at.isoformat() if o.last_paid_at else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "principal": {
            "id": principal.id,
            "username": principal.username,
            "name": principal.name,
        } if principal else None,
        # 机构运营概况（资金/教师/学生）
        "overview": _org_overview(db, o.id, month_start, today),
    }


@router.get("/organizations")
def list_organizations(page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：查看全部机构（校长开户情况），含交费与到期状态 + 机构运营概况（资金/教师/学生）"""
    q = db.query(Organization).order_by(Organization.created_at.desc(), Organization.id.desc())
    orgs = (q.offset((page - 1) * page_size).limit(page_size).all()
            if page is not None else q.all())
    return [_org_out(o, db) for o in orgs]


@router.get("/overview")
def platform_overview(current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：全部机构运营汇总（资金/教师/学生/打卡），用于超级管理员工作台"""
    orgs = db.query(Organization).all()
    today = date.today()
    month_start = today.replace(day=1)
    org_ids = [o.id for o in orgs]

    student_count = active_student_count = teacher_count = today_attendance = 0
    month_income = month_expense = unpaid = 0.0
    for o in orgs:
        ov = _org_overview(db, o.id, month_start, today)
        student_count += ov["student_count"]
        active_student_count += ov["active_student_count"]
        teacher_count += ov["teacher_count"]
        today_attendance += ov["today_attendance"]
        month_income += ov["month_income"]
        month_expense += ov["month_expense"]
        unpaid += ov["unpaid"]

    expiring_count = sum(1 for o in orgs if _expire_status(o) == "expiring")
    expired_count = sum(1 for o in orgs if _expire_status(o) == "expired")
    total_paid = sum(o.total_paid or 0 for o in orgs)

    return {
        "org_count": len(orgs),
        "student_count": student_count,
        "active_student_count": active_student_count,
        "teacher_count": teacher_count,
        "month_income": round(month_income, 2),
        "month_expense": round(month_expense, 2),
        "month_balance": round(month_income - month_expense, 2),
        "today_attendance": today_attendance,
        "unpaid": round(unpaid, 2),
        "total_paid": round(total_paid, 2),
        "expiring_count": expiring_count,
        "expired_count": expired_count,
    }


@router.post("/organizations")
def create_organization(data: OrgCreate, current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：为新校长开户（创建机构 + 校长账号，数据归零），可录入交费"""
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="校长账号已存在")

    org = Organization(
        name=data.org_name,
        code=data.org_code or _gen_code(db),
        contact=data.contact,
        phone=data.phone,
        status=True,
        plan_type=data.plan_type,
        payment_period=data.payment_period,
        fee_amount=data.fee_amount or 0,
        total_paid=data.fee_amount or 0,
        expire_date=_calc_expire(data.payment_period),  # 从开户当日推算
        last_paid_at=datetime.utcnow() if (data.fee_amount or data.payment_period) else None,
    )
    db.add(org)
    db.flush()  # 获取 org.id

    principal = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.contact or data.org_name,
        role=UserRole.PRINCIPAL,
        org_id=org.id,
        phone=data.phone,
    )
    db.add(principal)

    # 生成开户流水
    if data.fee_amount is not None or data.payment_period:
        db.add(Payment(
            org_id=org.id,
            amount=data.fee_amount or 0,
            plan_type=data.plan_type,
            payment_period=data.payment_period,
            expire_date=org.expire_date,
            remark="开户缴费",
        ))
    db.commit()
    db.refresh(org)
    return _org_out(org, db)


@router.put("/organizations/{org_id}")
def update_organization(org_id: int, data: OrgUpdate, current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：修改机构信息 / 启停用"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(org, k, v)
    db.commit()
    db.refresh(org)
    return _org_out(org, db)


@router.post("/organizations/{org_id}/payments")
def add_payment(org_id: int, data: RenewData, current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：机构续费 / 追加交费流水，更新到期日期与累计金额"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    amount = data.amount or 0
    if amount < 0:
        raise HTTPException(status_code=400, detail="金额不能为负")
    # 交费时间段：在现有到期日（未过期）基础上顺延，否则从今日起算
    if data.payment_period:
        base = org.expire_date if (org.expire_date and org.expire_date >= date.today()) else date.today()
        org.expire_date = _calc_expire(data.payment_period, base)
        org.payment_period = data.payment_period
    if data.plan_type:
        org.plan_type = data.plan_type
    if amount:
        org.fee_amount = amount
        org.total_paid = (org.total_paid or 0) + amount
        org.last_paid_at = datetime.utcnow()
    db.add(Payment(
        org_id=org.id,
        amount=amount,
        plan_type=data.plan_type or org.plan_type,
        payment_period=data.payment_period or org.payment_period,
        expire_date=org.expire_date,
        remark=data.remark or "续费",
    ))
    db.commit()
    db.refresh(org)
    return _org_out(org, db)


@router.get("/organizations/{org_id}/payments")
def list_org_payments(org_id: int, page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：某机构的开户流水明细"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    q = db.query(Payment).filter(Payment.org_id == org_id).order_by(Payment.id.desc())
    rows = (q.offset((page - 1) * page_size).limit(page_size).all()
            if page is not None else q.all())
    return [{
        "id": p.id,
        "amount": p.amount or 0,
        "plan_type": p.plan_type,
        "plan_type_text": PLAN_TYPES.get(p.plan_type, ""),
        "payment_period": p.payment_period,
        "expire_date": p.expire_date.isoformat() if p.expire_date else None,
        "remark": p.remark,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    } for p in rows]


@router.get("/organizations/{org_id}/principals")
def list_org_principals(org_id: int, page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：查看某机构下的校长账号"""
    q = db.query(User).filter(User.org_id == org_id, User.role == UserRole.PRINCIPAL).order_by(User.id)
    q = q.offset((page - 1) * page_size).limit(page_size) if page is not None else q
    return [
        {"id": u.id, "username": u.username, "name": u.name, "phone": u.phone, "is_active": u.is_active}
        for u in q.all()
    ]


@router.put("/principals/{user_id}/reset-password")
def reset_principal_password(user_id: int, data: PrincipalReset, current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：重置校长账号密码"""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.PRINCIPAL).first()
    if not user:
        raise HTTPException(status_code=404, detail="校长账号不存在")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    user.password_hash = hash_password(data.password)
    db.commit()
    return {"detail": "校长密码已重置"}


@router.get("/payments/statistics")
def payment_statistics(current_user: User = Depends(get_current_platform), db: Session = Depends(get_db)):
    """平台：全部机构开户流水统计（总金额、按机构汇总、按月趋势、待收款/已到期列表）"""
    today = date.today()

    # 总交费金额
    total_amount = db.query(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0

    # 按机构汇总
    orgs = db.query(Organization).all()
    by_org = []
    for o in orgs:
        by_org.append({
            "org_id": o.id,
            "name": o.name,
            "total_paid": o.total_paid or 0,
            "payment_period": o.payment_period,
            "expire_date": o.expire_date.isoformat() if o.expire_date else None,
            "expire_status": _expire_status(o),
        })

    # 按月趋势（按交费时间）
    month_rows = (
        db.query(
            func.strftime("%Y-%m", Payment.created_at).label("month"),
            func.sum(Payment.amount).label("amount"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    by_month = [{"month": m.month, "amount": round(m.amount or 0, 2)} for m in month_rows]

    # 待收款 / 已到期列表（即将到期 + 已到期）
    due_list = []
    for o in orgs:
        st = _expire_status(o)
        if st in ("expiring", "expired"):
            due_list.append({
                "org_id": o.id,
                "name": o.name,
                "payment_period": o.payment_period,
                "expire_date": o.expire_date.isoformat() if o.expire_date else None,
                "days_left": (o.expire_date - today).days if o.expire_date else None,
                "expire_status": st,
                "total_paid": o.total_paid or 0,
            })
    due_list.sort(key=lambda x: (x["days_left"] if x["days_left"] is not None else 9999))

    return {
        "total_amount": round(total_amount, 2),
        "org_count": len(orgs),
        "by_org": by_org,
        "by_month": by_month,
        "due_list": due_list,
    }
