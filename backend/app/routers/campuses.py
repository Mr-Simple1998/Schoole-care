"""校区管理：校区设置、负责人指定、手工收支登记、各校区概况统计

权限模型：
- 总校长（principal）：可设置校区、为校区开校长管理号（负责人）、登记收支、查看全部校区汇总（只读总览）
- 校区负责人（sub_principal / 存量 campus_head）：只能登记/查看自己校区的收支
- 教师（teacher）：不参与收支管理（学生数据权限维持原状）
- 学费收入按“缴费学生所属校区”自动归属；手工收支（非学费收入/支出）登记在 CampusTransaction
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_campus import Campus, CampusTransaction
from ..models_income import FeeRecord, Invoice
from ..models_learning import Attendance
from ..security import get_current_user, hash_password, is_head_role

router = APIRouter()

INCOME_CATEGORIES = ("餐费", "杂费", "其他")
EXPENSE_CATEGORIES = ("房租", "工资", "水电", "其他")


# ---------- 权限辅助 ----------
def _org_campus_ids(db: Session, user: User) -> set[int] | None:
    """总校长返回 None（可见全部校区概况，只读总览）；校区负责人仅可见自己校区"""
    if user.role == UserRole.PRINCIPAL:
        return None
    if user.campus_id:
        return {user.campus_id}
    return set()


def _require_campus(db: Session, user: User, campus_id: int) -> Campus:
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")
    if is_head_role(user.role) and user.campus_id != campus.id:
        raise HTTPException(status_code=403, detail="只能操作自己校区的数据")
    return campus


# ---------- 概况统计 ----------
def _overview(db: Session, org_id: int, campus_id: int | None, month_start: date, today: date) -> dict:
    """单个校区（或未分校区）的本月收支与人员概况"""
    st_q = db.query(Student).filter(Student.org_id == org_id, Student.deleted == False)  # noqa: E712
    if campus_id is None:
        st_q = st_q.filter(Student.campus_id.is_(None))
    else:
        st_q = st_q.filter(Student.campus_id == campus_id)
    student_ids = [s.id for s in st_q.all()]
    student_count = len(student_ids)

    tuition = 0.0
    if student_ids:
        tuition = db.query(func.coalesce(func.sum(FeeRecord.amount), 0)).filter(
            FeeRecord.org_id == org_id,
            FeeRecord.student_id.in_(student_ids),
            FeeRecord.pay_date >= month_start,
        ).scalar() or 0

    manual_income = manual_expense = 0.0
    if campus_id is not None:
        manual_income = db.query(func.coalesce(func.sum(CampusTransaction.amount), 0)).filter(
            CampusTransaction.org_id == org_id,
            CampusTransaction.campus_id == campus_id,
            CampusTransaction.kind == "income",
            CampusTransaction.record_date >= month_start,
        ).scalar() or 0
        manual_expense = db.query(func.coalesce(func.sum(CampusTransaction.amount), 0)).filter(
            CampusTransaction.org_id == org_id,
            CampusTransaction.campus_id == campus_id,
            CampusTransaction.kind == "expense",
            CampusTransaction.record_date >= month_start,
        ).scalar() or 0

    teacher_count = 0
    if campus_id is not None:
        teacher_count = db.query(User).filter(
            User.org_id == org_id,
            User.is_active == True,  # noqa: E712
            User.role.in_([UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
            User.campus_id == campus_id,
        ).count()

    today_attendance = 0
    if student_ids:
        today_attendance = db.query(Attendance).filter(
            Attendance.date == today,
            Attendance.org_id == org_id,
            Attendance.student_id.in_(student_ids),
        ).count()

    unpaid = 0.0
    if student_ids:
        invs = db.query(Invoice).filter(
            Invoice.org_id == org_id,
            Invoice.status.in_(["待缴", "部分缴纳"]),
            Invoice.student_id.in_(student_ids),
        ).all()
        unpaid = sum((inv.amount or 0) - (inv.paid_amount or 0) for inv in invs)

    head = None
    if campus_id is not None:
        h = db.query(User).filter(
            User.org_id == org_id,
            User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
            User.campus_id == campus_id,
            User.is_active == True,  # noqa: E712
        ).first()
        if h:
            head = {"id": h.id, "name": h.name, "username": h.username, "phone": h.phone}

    month_income = round(float(tuition) + float(manual_income), 2)
    month_expense = round(float(manual_expense), 2)
    return {
        "student_count": student_count,
        "teacher_count": teacher_count,
        "month_income": month_income,
        "month_expense": month_expense,
        "month_balance": round(month_income - month_expense, 2),
        "today_attendance": today_attendance,
        "unpaid": round(unpaid, 2),
        "head": head,
    }


def _campus_item(db: Session, org_id: int, campus: Campus | None, month_start: date, today: date) -> dict:
    if campus is None:
        return {
            "id": None,
            "name": "未分校区",
            "address": None,
            "phone": None,
            "remark": None,
            "status": True,
            "can_manage": False,
            **_overview(db, org_id, None, month_start, today),
        }
    return {
        "id": campus.id,
        "name": campus.name,
        "address": campus.address,
        "phone": campus.phone,
        "remark": campus.remark,
        "status": bool(campus.status),
        "can_manage": True,
        **_overview(db, org_id, campus.id, month_start, today),
    }


# ---------- 校区下拉（供学生/教师表单选择） ----------
@router.get("/options")
def campus_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.org_id:
        return []
    rows = db.query(Campus).filter(Campus.org_id == current_user.org_id).order_by(Campus.id).all()
    return [{"id": c.id, "name": c.name, "status": bool(c.status)} for c in rows]


# ---------- 校区列表 + 概况 ----------
@router.get("")
def list_campuses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """各校区概况：总校长看全部（含未分校区与汇总行），校区负责人/教师只见自己校区"""
    org_id = current_user.org_id
    today = date.today()
    month_start = today.replace(day=1)
    can_manage = current_user.role == UserRole.PRINCIPAL

    if not org_id:
        return {"summary": None, "items": [], "uncategorized": None, "can_manage": False, "role": current_user.role}

    visible = _org_campus_ids(db, current_user)
    if visible is None:
        campuses = db.query(Campus).filter(Campus.org_id == org_id).order_by(Campus.id).all()
    else:
        campuses = db.query(Campus).filter(
            Campus.org_id == org_id, Campus.id.in_(visible) if visible else Campus.id.in_([])
        ).order_by(Campus.id).all()

    items = [_campus_item(db, org_id, c, month_start, today) for c in campuses]

    uncategorized = None
    if current_user.role == UserRole.PRINCIPAL:
        uncategorized = _campus_item(db, org_id, None, month_start, today)

    # 汇总行
    summary = None
    if current_user.role == UserRole.PRINCIPAL:
        all_rows = items + ([uncategorized] if uncategorized else [])
        # 教师数按机构整体统计（含未分校区教师）
        teacher_count = db.query(User).filter(
            User.org_id == org_id,
            User.is_active == True,  # noqa: E712
            User.role.in_([UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
        ).count()
        summary = {
            "campus_count": len(campuses),
            "student_count": sum(r["student_count"] for r in all_rows),
            "teacher_count": teacher_count,
            "month_income": round(sum(r["month_income"] for r in all_rows), 2),
            "month_expense": round(sum(r["month_expense"] for r in all_rows), 2),
            "month_balance": round(sum(r["month_income"] for r in all_rows) - sum(r["month_expense"] for r in all_rows), 2),
            "today_attendance": sum(r["today_attendance"] for r in all_rows),
            "unpaid": round(sum(r["unpaid"] for r in all_rows), 2),
            "head": None,
        }
    elif is_head_role(current_user.role) and items:
        it = items[0]
        summary = {
            "campus_count": 1,
            "student_count": it["student_count"],
            "teacher_count": it["teacher_count"],
            "month_income": it["month_income"],
            "month_expense": it["month_expense"],
            "month_balance": it["month_balance"],
            "today_attendance": it["today_attendance"],
            "unpaid": it["unpaid"],
            "head": it["head"],
        }

    return {
        "summary": summary,
        "items": items,
        "uncategorized": uncategorized,
        "can_manage": can_manage,
        "role": current_user.role,
    }


# ---------- 校区设置（仅总校长） ----------
class CampusCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    remark: str | None = None
    status: bool = True


class CampusUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    remark: str | None = None
    status: bool | None = None


@router.post("")
def create_campus(data: CampusCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅总校长可设置校区")
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="校区名称不能为空")
    campus = Campus(**data.model_dump(), org_id=current_user.org_id)
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return _campus_item(db, current_user.org_id, campus, date.today().replace(day=1), date.today())


@router.put("/{campus_id}")
def update_campus(campus_id: int, data: CampusUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅总校长可设置校区")
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == current_user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(campus, k, v)
    db.commit()
    db.refresh(campus)
    return _campus_item(db, current_user.org_id, campus, date.today().replace(day=1), date.today())


@router.delete("/{campus_id}")
def delete_campus(campus_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅总校长可设置校区")
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == current_user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")
    students = db.query(Student).filter(Student.campus_id == campus_id).count()
    users = db.query(User).filter(User.campus_id == campus_id).count()
    txns = db.query(CampusTransaction).filter(CampusTransaction.campus_id == campus_id).count()
    if students or users or txns:
        raise HTTPException(
            status_code=400,
            detail=f"该校区已有 {students} 名学生、{users} 名教师、{txns} 条收支记录，请先转移数据或停用校区",
        )
    db.delete(campus)
    db.commit()
    return {"detail": "已删除"}


# ---------- 指定校区负责人（仅总校长；可新建账号或指定已有教师） ----------
class HeadAssign(BaseModel):
    user_id: int | None = None       # 指定已有教师账号（与新建账号二选一）
    username: str | None = None      # 新建负责人账号：登录账号
    password: str | None = None      # 新建负责人账号：密码
    name: str | None = None          # 新建负责人账号：姓名
    phone: str | None = None         # 新建负责人账号：电话（可选）


@router.post("/{campus_id}/head")
def assign_campus_head(campus_id: int, data: HeadAssign, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """总校长设置校区负责人（校长管理号）：可手动新建负责人账号，或指定本机构已有教师；都不传则取消负责人。"""
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅总校长可指定负责人")
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == current_user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")

    # 原负责人降级为教师（保留校区归属）
    db.query(User).filter(
        User.org_id == current_user.org_id,
        User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
        User.campus_id == campus_id,
    ).update({"role": UserRole.TEACHER}, synchronize_session=False)

    has_user = data.user_id is not None
    has_new = bool(data.username or data.password or data.name)
    if has_user and has_new:
        raise HTTPException(status_code=400, detail="请选择一种方式：指定已有账号或新建账号")

    head = None
    if has_user:
        user = db.query(User).filter(User.id == data.user_id, User.org_id == current_user.org_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="账号不存在")
        if user.role not in (UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD):
            raise HTTPException(status_code=400, detail="只能指定教师账号为校区负责人")
        user.role = UserRole.SUB_PRINCIPAL
        user.campus_id = campus.id
        head = user
    elif has_new:
        if not data.username or not data.password or not data.name:
            raise HTTPException(status_code=400, detail="新建负责人需填写姓名、登录账号、密码")
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="密码至少 6 位")
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="登录账号已存在")
        head = User(
            username=data.username.strip(),
            password_hash=hash_password(data.password),
            name=data.name.strip(),
            role=UserRole.SUB_PRINCIPAL,
            campus_id=campus.id,
            phone=data.phone,
            org_id=current_user.org_id,
        )
        db.add(head)

    db.commit()
    if head:
        db.refresh(head)
    return {
        "detail": "负责人已设置",
        "campus_id": campus.id,
        "head": {"id": head.id, "name": head.name, "username": head.username} if head else None,
    }


# ---------- 手工收支登记 ----------
class TransactionCreate(BaseModel):
    campus_id: int
    kind: str  # income / expense
    category: str
    amount: float
    record_date: date
    remark: str | None = None


class TransactionOut(BaseModel):
    id: int
    campus_id: int
    campus_name: str | None = None
    kind: str
    category: str
    amount: float
    record_date: date
    remark: str | None
    created_by_name: str | None = None
    created_at: datetime | None

    class Config:
        from_attributes = True


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(data: TransactionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL and not is_head_role(current_user.role):
        raise HTTPException(status_code=403, detail="无收支登记权限")
    campus = _require_campus(db, current_user, data.campus_id)
    if data.kind not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="类型必须为 income 或 expense")
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于 0")
    allowed = INCOME_CATEGORIES if data.kind == "income" else EXPENSE_CATEGORIES
    if data.category not in allowed:
        raise HTTPException(status_code=400, detail=f"分类不合法，可选：{'、'.join(allowed)}")
    txn = CampusTransaction(
        org_id=current_user.org_id,
        campus_id=campus.id,
        kind=data.kind,
        category=data.category,
        amount=data.amount,
        record_date=data.record_date,
        remark=data.remark,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    out = TransactionOut.model_validate(txn)
    out.campus_name = campus.name
    out.created_by_name = current_user.name
    return out


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    campus_id: int | None = None,
    kind: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.PRINCIPAL and not is_head_role(current_user.role):
        raise HTTPException(status_code=403, detail="无权限查看收支明细")
    q = db.query(CampusTransaction).filter(CampusTransaction.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        q = q.filter(CampusTransaction.campus_id == current_user.campus_id)
    if campus_id:
        if is_head_role(current_user.role) and campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能查看自己校区的收支")
        q = q.filter(CampusTransaction.campus_id == campus_id)
    if kind:
        q = q.filter(CampusTransaction.kind == kind)
    rows = q.order_by(CampusTransaction.record_date.desc(), CampusTransaction.id.desc()).all()
    campus_map = {c.id: c.name for c in db.query(Campus).filter(Campus.org_id == current_user.org_id).all()}
    user_map = {u.id: u.name for u in db.query(User).filter(User.org_id == current_user.org_id).all()}
    result = []
    for t in rows:
        out = TransactionOut.model_validate(t)
        out.campus_name = campus_map.get(t.campus_id)
        out.created_by_name = user_map.get(t.created_by)
        result.append(out)
    return result


@router.delete("/transactions/{txn_id}")
def delete_transaction(txn_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL and not is_head_role(current_user.role):
        raise HTTPException(status_code=403, detail="无权限删除收支记录")
    txn = db.query(CampusTransaction).filter(CampusTransaction.id == txn_id, CampusTransaction.org_id == current_user.org_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="收支记录不存在")
    if is_head_role(current_user.role):
        if txn.campus_id != current_user.campus_id:
            raise HTTPException(status_code=403, detail="只能删除自己校区的收支记录")
        if txn.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只能删除自己登记的收支记录")
    db.delete(txn)
    db.commit()
    return {"detail": "已删除"}
