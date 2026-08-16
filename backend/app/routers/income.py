from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_income import FeeRecord, Invoice, RefundAdjustment, Installment, InstallmentRecord
from ..security import (
    get_current_user, get_current_principal_or_head, is_head_role, managed_campus_ids,
)

router = APIRouter()


def _scope_income_students(q, db: Session, current_user: User):
    """按角色限定学生数据范围（教师=自己负责；校区负责人=管辖校区（可多校区）；总校长归属校区后=本校区）"""
    if current_user.role == UserRole.TEACHER:
        return q.join(Student).filter(Student.teacher_id == current_user.id)
    if is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        return q.join(Student).filter(Student.campus_id.in_(managed))
    if current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        return q.join(Student).filter(Student.campus_id == current_user.campus_id)
    return q


def _check_student_scope(db: Session, current_user: User, student: Student):
    """校验学生是否在当前用户数据范围内"""
    if current_user.role == UserRole.TEACHER:
        if student.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="只能操作自己负责的学生")
    elif is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        if student.campus_id not in managed:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        if student.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能操作本校区学生")

# 缴费时间段 -> 有效天数
PERIOD_DAYS = {
    "一月": 30,
    "半学期": 60,
    "一年": 365,
}


# ---------- 收费流水 ----------
class FeeCreate(BaseModel):
    student_id: int
    fee_type: str
    amount: float
    pay_date: date
    payment_method: str = "现金"
    payment_period: str | None = None   # 缴费时间段：一月/半学期/一年
    total_sessions: int | None = None   # 课程总次数（按次核销）
    remark: str | None = None


class FeeOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    student_deleted: bool = False
    fee_type: str
    amount: float
    pay_date: date
    payment_method: str
    payment_period: str | None = None
    expire_date: date | None = None
    total_sessions: int | None = None
    used_sessions: int = 0
    remaining_sessions: int | None = None
    remark: str | None

    class Config:
        from_attributes = True


@router.post("/fees", response_model=FeeOut)
def create_fee(data: FeeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    payload = data.model_dump()
    period = data.payment_period
    if period and period in PERIOD_DAYS:
        payload["expire_date"] = data.pay_date + timedelta(days=PERIOD_DAYS[period])
    else:
        payload.pop("expire_date", None)
    fee = FeeRecord(**payload, org_id=current_user.org_id, created_by=current_user.id, created_at=datetime.utcnow())
    db.add(fee)
    # 若有对应账单，更新已缴金额与状态
    inv = db.query(Invoice).filter(
        Invoice.student_id == data.student_id,
        Invoice.status == "待缴",
        Invoice.org_id == current_user.org_id,
    ).first()
    if inv:
        inv.paid_amount += data.amount
        if inv.paid_amount >= inv.amount:
            inv.paid_amount = inv.amount
            inv.status = "已缴清"
        else:
            inv.status = "部分缴纳"
    db.commit()
    db.refresh(fee)
    return _fee_with_name(fee, student)


def _fee_with_name(fee, student=None):
    out = FeeOut.model_validate(fee)
    if fee.total_sessions:
        out.remaining_sessions = fee.total_sessions - (fee.used_sessions or 0)
    if student is not None:
        out.student_name = student.name
        out.student_deleted = bool(student.deleted)
    return out


@router.get("/fees", response_model=list[FeeOut])
def list_fees(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(FeeRecord).filter(FeeRecord.org_id == current_user.org_id)
    q = _scope_income_students(q, db, current_user)
    fees = q.order_by(FeeRecord.pay_date.desc()).all()
    result = []
    for f in fees:
        item = FeeOut.model_validate(f)
        if f.total_sessions:
            item.remaining_sessions = f.total_sessions - (f.used_sessions or 0)
        st = db.query(Student).filter(Student.id == f.student_id).first()
        item.student_name = st.name if st else None
        item.student_deleted = st.deleted if st else False
        result.append(item)
    return result


# ---------- 学生课程次数查询 ----------
@router.get("/students/{student_id}/sessions")
def get_student_sessions(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """查询学生课程剩余次数（含学科课时明细）"""
    from ..models_subject import StudentSubject, Subject
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    # FeeRecord 级别（旧）
    fees = db.query(FeeRecord).filter(
        FeeRecord.student_id == student_id,
        FeeRecord.org_id == current_user.org_id,
        FeeRecord.total_sessions.isnot(None)
    ).all()
    fee_details = []
    for f in fees:
        fee_details.append({
            "id": f.id,
            "fee_type": f.fee_type,
            "total_sessions": f.total_sessions,
            "used_sessions": f.used_sessions or 0,
            "remaining_sessions": (f.total_sessions or 0) - (f.used_sessions or 0),
            "pay_date": f.pay_date.isoformat() if f.pay_date else None,
            "expire_date": f.expire_date.isoformat() if f.expire_date else None,
            "payment_period": f.payment_period,
        })
    # 学科课时明细（新）
    links = db.query(StudentSubject).filter(StudentSubject.student_id == student_id).all()
    subject_details = []
    for link in links:
        sub = db.query(Subject).filter(Subject.id == link.subject_id).first()
        subject_details.append({
            "subject_id": link.subject_id,
            "subject_name": sub.name if sub else "",
            "total_sessions": link.total_sessions,
            "used_sessions": link.used_sessions or 0,
            "remaining": (link.total_sessions - (link.used_sessions or 0)) if link.total_sessions is not None else None,
        })
    return {
        "student_id": student_id,
        "student_name": student.name,
        "total_remaining": sum(d["remaining_sessions"] for d in fee_details),
        "details": fee_details,
        "subject_sessions": subject_details,
    }


@router.post("/students/{student_id}/deduct-session")
def deduct_session(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """手动核销一次课程"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    fee = db.query(FeeRecord).filter(
        FeeRecord.student_id == student_id,
        FeeRecord.org_id == current_user.org_id,
        FeeRecord.total_sessions.isnot(None),
    ).filter(FeeRecord.total_sessions > FeeRecord.used_sessions).order_by(FeeRecord.pay_date.asc()).first()
    if not fee:
        raise HTTPException(status_code=400, detail="该学生没有剩余课程次数")
    fee.used_sessions = (fee.used_sessions or 0) + 1
    db.commit()
    remaining = fee.total_sessions - fee.used_sessions
    return {"detail": "已核销一次", "remaining_sessions": remaining, "fee_id": fee.id}


# ---------- 账单 ----------
class InvoiceCreate(BaseModel):
    student_id: int
    item: str
    amount: float
    due_date: date | None = None


class InvoiceOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    student_deleted: bool = False
    item: str
    amount: float
    due_date: date | None
    status: str
    paid_amount: float

    class Config:
        from_attributes = True


@router.post("/invoices", response_model=InvoiceOut, dependencies=[Depends(get_current_principal_or_head)])
def create_invoice(data: InvoiceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    inv = Invoice(**data.model_dump(), org_id=current_user.org_id, created_at=datetime.utcnow())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Invoice).filter(Invoice.org_id == current_user.org_id)
    q = _scope_income_students(q, db, current_user)
    invoices = q.order_by(Invoice.created_at.desc()).all()
    result = []
    for inv in invoices:
        item = InvoiceOut.model_validate(inv)
        st = db.query(Student).filter(Student.id == inv.student_id).first()
        item.student_name = st.name if st else None
        item.student_deleted = st.deleted if st else False
        result.append(item)
    return result


@router.get("/overdue")
def list_overdue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """欠费/未缴提醒：返回待缴账单及学生信息"""
    q = db.query(Invoice).filter(Invoice.status.in_(["待缴", "部分缴纳"]), Invoice.org_id == current_user.org_id)
    q = _scope_income_students(q, db, current_user)
    invoices = q.all()
    result = []
    for inv in invoices:
        st = db.query(Student).filter(Student.id == inv.student_id).first()
        result.append({
            "invoice_id": inv.id,
            "student_id": inv.student_id,
            "student_name": st.name if st else "",
            "student_deleted": st.deleted if st else False,
            "item": inv.item,
            "amount": inv.amount,
            "paid_amount": inv.paid_amount,
            "unpaid": round(inv.amount - inv.paid_amount, 2),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "status": inv.status,
        })
    return result


# ---------- 退费/减免 ----------
class RefundCreate(BaseModel):
    student_id: int
    invoice_id: int | None = None
    kind: str = "减免"  # 减免/退费
    amount: float
    reason: str | None = None


class RefundOut(BaseModel):
    id: int
    student_id: int
    invoice_id: int | None
    student_name: str | None = None
    student_deleted: bool = False
    kind: str
    amount: float
    reason: str | None
    created_at: datetime | None

    class Config:
        from_attributes = True


@router.post("/refunds", response_model=RefundOut, dependencies=[Depends(get_current_principal_or_head)])
def create_refund(data: RefundCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    refund = RefundAdjustment(**data.model_dump(), org_id=current_user.org_id, created_by=current_user.id, created_at=datetime.utcnow())
    db.add(refund)
    # 若关联账单，更新减免后状态
    if data.invoice_id:
        inv = db.query(Invoice).filter(Invoice.id == data.invoice_id, Invoice.org_id == current_user.org_id).first()
        if inv:
            inv.amount = max(0, inv.amount - data.amount)
            if inv.amount <= inv.paid_amount:
                inv.status = "已减免"
    db.commit()
    db.refresh(refund)
    return refund


@router.get("/refunds", response_model=list[RefundOut])
def list_refunds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(RefundAdjustment).filter(RefundAdjustment.org_id == current_user.org_id)
    q = _scope_income_students(q, db, current_user)
    result = []
    for r in q.order_by(RefundAdjustment.created_at.desc()).all():
        item = RefundOut.model_validate(r)
        st = db.query(Student).filter(Student.id == r.student_id).first()
        item.student_name = st.name if st else None
        item.student_deleted = st.deleted if st else False
        result.append(item)
    return result


# ---------- 学费分期 ----------
class InstallmentCreate(BaseModel):
    student_id: int
    title: str
    total_amount: float
    periods: int = 1
    start_date: date | None = None
    remark: str | None = None


class InstallmentOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    student_deleted: bool = False
    title: str
    total_amount: float
    periods: int
    paid_periods: int
    status: str
    start_date: date | None
    remark: str | None

    class Config:
        from_attributes = True


@router.post("/installments", response_model=InstallmentOut, dependencies=[Depends(get_current_principal_or_head)])
def create_installment(data: InstallmentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """总校长/校区负责人：为学费创建分期计划"""
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    if data.periods < 1:
        raise HTTPException(status_code=400, detail="期数至少为1")
    inst = Installment(
        student_id=data.student_id, title=data.title, total_amount=data.total_amount,
        periods=data.periods, start_date=data.start_date, remark=data.remark,
        status="进行中", org_id=current_user.org_id, created_at=datetime.utcnow(),
    )
    db.add(inst)
    db.flush()
    # 生成各期还款记录
    per_amount = round(data.total_amount / data.periods, 2)
    for i in range(1, data.periods + 1):
        db.add(InstallmentRecord(
            installment_id=inst.id, period_no=i, amount=per_amount,
            due_date=data.start_date, status="待缴", org_id=current_user.org_id,
        ))
    db.commit()
    db.refresh(inst)
    return _installment_with_name(inst, student)


@router.get("/installments", response_model=list[InstallmentOut])
def list_installments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Installment).filter(Installment.org_id == current_user.org_id)
    q = _scope_income_students(q, db, current_user)
    insts = q.order_by(Installment.created_at.desc()).all()
    result = []
    for i in insts:
        st = db.query(Student).filter(Student.id == i.student_id).first()
        result.append(_installment_with_name(i, st))
    return result


def _installment_with_name(inst, student):
    out = InstallmentOut.model_validate(inst)
    out.student_name = student.name if student else None
    out.student_deleted = student.deleted if student else False
    return out


@router.get("/installments/{installment_id}")
def get_installment_detail(installment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """查看分期详情及各期还款记录"""
    inst = db.query(Installment).filter(Installment.id == installment_id, Installment.org_id == current_user.org_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="分期不存在")
    st = db.query(Student).filter(Student.id == inst.student_id).first()
    if st:
        _check_student_scope(db, current_user, st)
    records = db.query(InstallmentRecord).filter(
        InstallmentRecord.installment_id == installment_id,
        InstallmentRecord.org_id == current_user.org_id,
    ).order_by(InstallmentRecord.period_no).all()
    return {
        "id": inst.id,
        "student_id": inst.student_id,
        "student_name": st.name if st else "",
        "title": inst.title,
        "total_amount": inst.total_amount,
        "paid_amount": round(sum(r.amount for r in records if r.status == "已缴"), 2),
        "periods": inst.periods,
        "paid_periods": inst.paid_periods,
        "status": inst.status,
        "records": [{
            "id": r.id, "period_no": r.period_no, "amount": r.amount,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "paid_date": r.paid_date.isoformat() if r.paid_date else None,
            "status": r.status,
        } for r in records],
    }


@router.post("/installments/{installment_id}/pay")
def pay_installment(installment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """缴纳下一期（教师可操作）"""
    inst = db.query(Installment).filter(Installment.id == installment_id, Installment.org_id == current_user.org_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="分期不存在")
    st = db.query(Student).filter(Student.id == inst.student_id).first()
    if st:
        _check_student_scope(db, current_user, st)
    if inst.status == "已完成":
        raise HTTPException(status_code=400, detail="分期已完成")
    next_record = db.query(InstallmentRecord).filter(
        InstallmentRecord.installment_id == installment_id,
        InstallmentRecord.status == "待缴",
        InstallmentRecord.org_id == current_user.org_id,
    ).order_by(InstallmentRecord.period_no).first()
    if not next_record:
        inst.status = "已完成"
        inst.paid_periods = inst.periods
        db.commit()
        return {"detail": "分期已完成", "status": "已完成"}
    next_record.status = "已缴"
    next_record.paid_date = date.today()
    inst.paid_periods += 1
    if inst.paid_periods >= inst.periods:
        inst.status = "已完成"
    db.commit()
    return {"detail": f"第{next_record.period_no}期已缴纳", "paid_periods": inst.paid_periods, "status": inst.status}