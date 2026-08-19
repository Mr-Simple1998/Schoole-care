from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_income import CommissionRecord, FeeRecord
from ..security import get_current_user, get_current_principal_or_head, is_head_role, managed_campus_ids
from .students import _check_student_scope

router = APIRouter()

# 四类提成角色的固定比例
ROLE_RATES = {
    "招生": 0.05,    # 首次交费的 5%
    "体验课": 0.03,  # 首次交费的 3%
    "谈单": 0.02,    # 首次交费的 2%
    "续费": 0.05,    # 续费金额的 5%
}

# 按首次交费计提的角色（招生/体验课/谈单）
FIRST_FEE_ROLES = {"招生", "体验课", "谈单"}


def _scope_students_q(db: Session, current_user: User):
    """按角色限定学生范围（教师=自己负责；校区负责人=管辖校区；校长归属校区后=本校区）"""
    q = db.query(Student).filter(Student.org_id == current_user.org_id)
    if current_user.role == UserRole.TEACHER:
        return q.filter(Student.teacher_id == current_user.id)
    if is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        return q.filter(Student.campus_id.in_(managed))
    if current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        return q.filter(Student.campus_id == current_user.campus_id)
    return q


def _get_student(db: Session, current_user: User, student_id: int) -> Student:
    student = db.query(Student).filter(
        Student.id == student_id, Student.org_id == current_user.org_id, Student.deleted == False  # noqa: E712
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _check_student_scope(db, current_user, student)
    return student


def _first_fee_amount(db: Session, student_id: int, org_id: int) -> float | None:
    """第一次交费金额：按缴费日期最早的收费记录（同日取 id 最小）"""
    fee = db.query(FeeRecord).filter(
        FeeRecord.student_id == student_id,
        FeeRecord.org_id == org_id,
    ).order_by(FeeRecord.pay_date.asc(), FeeRecord.id.asc()).first()
    return fee.amount if fee else None


def _last_fee_amount(db: Session, student_id: int, org_id: int) -> float | None:
    """最近一次交费金额（续费提成的默认基数）"""
    fee = db.query(FeeRecord).filter(
        FeeRecord.student_id == student_id,
        FeeRecord.org_id == org_id,
    ).order_by(FeeRecord.pay_date.desc(), FeeRecord.id.desc()).first()
    return fee.amount if fee else None


def _fee_amount_by_id(db: Session, fee_id: int | None, org_id: int) -> float | None:
    if not fee_id:
        return None
    fee = db.query(FeeRecord).filter(FeeRecord.id == fee_id, FeeRecord.org_id == org_id).first()
    return fee.amount if fee else None


class CommissionCreate(BaseModel):
    student_id: int
    role: str                          # 招生 / 体验课 / 谈单 / 续费（分类标签）
    teacher_id: int | None = None
    teacher_name: str | None = None
    base_amount: float | None = None   # 不传时自动取：招生/体验课/谈单=首次交费，续费=最近交费（或 fee_id 对应金额）
    percent: float | None = None       # 提成百分比（手动选择，如 5 表示 5%）；不传时用角色默认比例
    fee_id: int | None = None          # 关联收费记录（续费提成可指定某笔续费）
    remark: str | None = None


class CommissionUpdate(BaseModel):
    teacher_id: int | None = None
    teacher_name: str | None = None
    base_amount: float | None = None
    percent: float | None = None           # 提成百分比（手动选择）；不传保持不变
    commission_amount: float | None = None   # 手动指定提成金额（覆盖自动计算）
    fee_id: int | None = None
    remark: str | None = None


class CommissionOut(BaseModel):
    id: int
    student_id: int
    student_name: str | None = None
    role: str
    teacher_id: int | None = None
    teacher_name: str | None = None
    base_amount: float
    commission_rate: float
    commission_amount: float
    fee_id: int | None = None
    remark: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


def _commission_out(rec: CommissionRecord, student_name: str | None = None) -> CommissionOut:
    out = CommissionOut.model_validate(rec)
    out.student_name = student_name
    return out


@router.get("", response_model=list[CommissionOut])
def list_commissions(
    student_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提成列表；可按学生过滤。教师只看到自己负责学生的提成。"""
    if student_id is not None:
        _get_student(db, current_user, student_id)
    q = db.query(CommissionRecord).filter(CommissionRecord.org_id == current_user.org_id)
    if student_id is not None:
        q = q.filter(CommissionRecord.student_id == student_id)
    else:
        scoped_ids = [s.id for s in _scope_students_q(db, current_user).all()]
        if not scoped_ids:
            return []
        q = q.filter(CommissionRecord.student_id.in_(scoped_ids))
    records = q.order_by(CommissionRecord.created_at.desc(), CommissionRecord.id.desc()).all()

    name_map = {s.id: s.name for s in db.query(Student).filter(Student.id.in_([r.student_id for r in records])).all()}
    return [_commission_out(r, name_map.get(r.student_id)) for r in records]


@router.post("", response_model=CommissionOut, dependencies=[Depends(get_current_principal_or_head)])
def create_commission(data: CommissionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """手动记录一条提成：比例由用户手动选择（percent），未传时用角色默认；基数自动取或手动传。"""
    if data.role not in ROLE_RATES:
        raise HTTPException(status_code=400, detail="提成角色无效，可选：招生/体验课/谈单/续费")
    student = _get_student(db, current_user, data.student_id)

    # 计提基数：显式传入优先；否则按角色规则自动取
    base = data.base_amount
    if base is None:
        if data.role in FIRST_FEE_ROLES:
            base = _first_fee_amount(db, student.id, current_user.org_id)
        else:  # 续费：优先 fee_id 对应金额，否则最近一次交费金额
            base = _fee_amount_by_id(db, data.fee_id, current_user.org_id) or _last_fee_amount(db, student.id, current_user.org_id)
    if base is None:
        base = 0.0
    base = round(float(base), 2)

    # 提成比例：手动选择优先；未传时用角色默认比例
    if data.percent is not None:
        if not (0 < float(data.percent) <= 100):
            raise HTTPException(status_code=400, detail="提成百分比需在 0-100 之间")
        rate = round(float(data.percent) / 100, 4)
    else:
        rate = ROLE_RATES[data.role]
    amount = round(base * rate, 2)

    # 教师信息：teacher_id 优先，否则用传入的 teacher_name
    teacher_name = data.teacher_name
    if data.teacher_id:
        t = db.query(User).filter(User.id == data.teacher_id).first()
        if t:
            teacher_name = t.name

    rec = CommissionRecord(
        org_id=current_user.org_id,
        student_id=student.id,
        role=data.role,
        teacher_id=data.teacher_id,
        teacher_name=teacher_name,
        base_amount=base,
        commission_rate=rate,
        commission_amount=amount,
        fee_id=data.fee_id,
        remark=data.remark,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _commission_out(rec, student.name)


@router.put("/{record_id}", response_model=CommissionOut, dependencies=[Depends(get_current_principal_or_head)])
def update_commission(record_id: int, data: CommissionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(CommissionRecord).filter(
        CommissionRecord.id == record_id, CommissionRecord.org_id == current_user.org_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="提成记录不存在")
    student = db.query(Student).filter(Student.id == rec.student_id).first()
    if student:
        _check_student_scope(db, current_user, student)

    if data.teacher_id is not None:
        rec.teacher_id = data.teacher_id
        t = db.query(User).filter(User.id == data.teacher_id).first()
        rec.teacher_name = t.name if t else None
    if data.teacher_name is not None:
        rec.teacher_name = data.teacher_name
    if data.base_amount is not None:
        rec.base_amount = round(float(data.base_amount), 2)
        rec.commission_amount = round(rec.base_amount * (rec.commission_rate or 0), 2)
    if data.percent is not None:
        if not (0 < float(data.percent) <= 100):
            raise HTTPException(status_code=400, detail="提成百分比需在 0-100 之间")
        rec.commission_rate = round(float(data.percent) / 100, 4)
        rec.commission_amount = round(rec.base_amount * rec.commission_rate, 2)
    if data.commission_amount is not None:
        rec.commission_amount = round(float(data.commission_amount), 2)
    if data.fee_id is not None:
        rec.fee_id = data.fee_id
    if data.remark is not None:
        rec.remark = data.remark
    db.commit()
    db.refresh(rec)
    return _commission_out(rec, student.name if student else None)


@router.delete("/{record_id}", dependencies=[Depends(get_current_principal_or_head)])
def delete_commission(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(CommissionRecord).filter(
        CommissionRecord.id == record_id, CommissionRecord.org_id == current_user.org_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="提成记录不存在")
    student = db.query(Student).filter(Student.id == rec.student_id).first()
    if student:
        _check_student_scope(db, current_user, student)
    db.delete(rec)
    db.commit()
    return {"detail": "已删除"}
