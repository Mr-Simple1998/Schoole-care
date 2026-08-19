"""校区管理：校区设置、负责人指定、手工收支登记、各校区概况统计

权限模型：
- 校长（principal）：可设置校区、为校区开校区负责人（负责人）、登记收支、查看全部校区汇总（只读总览）
- 校区负责人（sub_principal / 存量 campus_head）：只能登记/查看自己校区的收支
- 教师（teacher）：不参与收支管理（学生数据权限维持原状）
- 学费收入按“缴费学生所属校区”自动归属；手工收支（非学费收入/支出）登记在 CampusTransaction
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_campus import Campus, CampusHead, CampusTransaction
from ..models_income import FeeRecord, Invoice
from ..models_learning import Attendance
from ..security import get_current_user, hash_password, is_head_role, managed_campus_ids

router = APIRouter()

INCOME_CATEGORIES = ("餐费", "杂费", "其他")
EXPENSE_CATEGORIES = ("房租", "工资", "水电", "其他")


# ---------- 权限辅助 ----------
def _org_campus_ids(db: Session, user: User) -> set[int] | None:
    """校长返回 None（可见全部校区概况，只读总览）；校区负责人可见自己管辖的校区（支持多校区）"""
    return managed_campus_ids(db, user)


def _require_campus(db: Session, user: User, campus_id: int) -> Campus:
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")
    if is_head_role(user.role):
        managed = managed_campus_ids(db, user) or set()
        if campus.id not in managed:
            raise HTTPException(status_code=403, detail="只能操作自己管辖校区的数据")
    return campus


def _campus_heads(db: Session, org_id: int, campus_id: int) -> list[dict]:
    """校区负责人列表（关联表 + 存量兼容：campus_id 归属的负责人），按关联时间排序"""
    rows = db.query(CampusHead).filter(
        CampusHead.org_id == org_id, CampusHead.campus_id == campus_id
    ).order_by(CampusHead.id).all()
    heads = []
    seen = set()
    for ch in rows:
        u = ch.user
        if not u or u.id in seen:
            continue
        seen.add(u.id)
        heads.append({"id": u.id, "name": u.name, "username": u.username, "phone": u.phone,
                      "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                      "is_active": bool(u.is_active), "resigned": bool(u.resigned)})
    # 存量兼容：老数据中负责人仅通过 users.campus_id 关联（未写入关联表）
    legacy = db.query(User).filter(
        User.org_id == org_id,
        User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
        User.campus_id == campus_id,
    ).order_by(User.id).all()
    for u in legacy:
        if u.id not in seen:
            heads.append({"id": u.id, "name": u.name, "username": u.username, "phone": u.phone,
                          "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                          "is_active": bool(u.is_active), "resigned": bool(u.resigned)})
    return heads


def _active_head_names(db: Session, org_id: int, campus_id: int) -> list[dict]:
    return [h for h in _campus_heads(db, org_id, campus_id) if h["is_active"] and not h["resigned"]]


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
            User.resigned == False,  # noqa: E712
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

    # 负责人：支持多名（含校长），离职负责人单独标注
    heads = []
    head = None
    if campus_id is not None:
        heads = _campus_heads(db, org_id, campus_id)
        active = [h for h in heads if h["is_active"] and not h["resigned"]]
        head = active[0] if active else None

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
        "heads": heads,
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
def campus_options(page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.org_id:
        return []
    q = db.query(Campus).filter(Campus.org_id == current_user.org_id).order_by(Campus.id)
    rows = (q.offset((page - 1) * page_size).limit(page_size).all()
            if page is not None else q.all())
    return [{"id": c.id, "name": c.name, "status": bool(c.status)} for c in rows]


# ---------- 负责人候选（校长设置校区负责人时的多选项；可包含校长本人，校长也可兼任某校区负责人） ----------
@router.get("/head-candidates")
def head_candidates(page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅校长可查看负责人候选")
    q = db.query(User).filter(User.org_id == current_user.org_id).order_by(User.id)
    users = (q.offset((page - 1) * page_size).limit(page_size).all()
             if page is not None else q.all())
    campus_map = {c.id: c.name for c in db.query(Campus).filter(Campus.org_id == current_user.org_id).all()}
    return [
        {
            "id": u.id,
            "name": u.name,
            "username": u.username,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "campus_id": u.campus_id,
            "campus_name": campus_map.get(u.campus_id),
            "is_active": bool(u.is_active),
            "resigned": bool(u.resigned),
        }
        for u in users if u.role != UserRole.PLATFORM
    ]


# ---------- 校区列表 + 概况 ----------
@router.get("")
def list_campuses(page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """各校区概况：校长看全部（含未分校区与汇总行），校区负责人/教师只见自己校区"""
    org_id = current_user.org_id
    today = date.today()
    month_start = today.replace(day=1)
    can_manage = current_user.role == UserRole.PRINCIPAL

    if not org_id:
        return {"summary": None, "items": [], "uncategorized": None, "can_manage": False, "role": current_user.role}

    visible = _org_campus_ids(db, current_user)
    if visible is None:
        q = db.query(Campus).filter(Campus.org_id == org_id).order_by(Campus.id)
    else:
        q = db.query(Campus).filter(
            Campus.org_id == org_id, Campus.id.in_(visible) if visible else Campus.id.in_([])
        ).order_by(Campus.id)
    campuses = (q.offset((page - 1) * page_size).limit(page_size).all()
                if page is not None else q.all())

    items = [_campus_item(db, org_id, c, month_start, today) for c in campuses]

    uncategorized = None
    if current_user.role == UserRole.PRINCIPAL:
        uncategorized = _campus_item(db, org_id, None, month_start, today)

    # 汇总行
    summary = None
    if current_user.role == UserRole.PRINCIPAL:
        all_rows = items + ([uncategorized] if uncategorized else [])
        # 教师数按机构整体统计（含未分校区教师，不含离职）
        teacher_count = db.query(User).filter(
            User.org_id == org_id,
            User.is_active == True,  # noqa: E712
            User.resigned == False,  # noqa: E712
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


# ---------- 校区设置（仅校长） ----------
class CampusCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    remark: str | None = None
    status: bool = True
    head_user_ids: list[int] | None = None  # 可选：创建校区时直接指定负责人（可含校长本人）


class CampusUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    remark: str | None = None
    status: bool | None = None


@router.post("")
def create_campus(data: CampusCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅校长可设置校区")
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="校区名称不能为空")
    campus = Campus(**data.model_dump(exclude={"head_user_ids"}), org_id=current_user.org_id)
    db.add(campus)
    db.flush()  # 获取 campus.id
    # 创建校区时直接指定负责人（可多选，含校长本人）
    if data.head_user_ids:
        selected = set(data.head_user_ids)
        users = db.query(User).filter(User.id.in_(selected), User.org_id == current_user.org_id).all()
        if len(users) != len(selected):
            raise HTTPException(status_code=400, detail="存在无效账号")
        for u in users:
            if u.role == UserRole.PLATFORM:
                raise HTTPException(status_code=400, detail="平台管理员不能设为校区负责人")
        for uid in selected:
            db.add(CampusHead(org_id=current_user.org_id, campus_id=campus.id, user_id=uid))
        _sync_campus_head_roles(db, current_user.org_id, campus.id, selected, set())
    db.commit()
    db.refresh(campus)
    return _campus_item(db, current_user.org_id, campus, date.today().replace(day=1), date.today())


@router.put("/{campus_id}")
def update_campus(campus_id: int, data: CampusUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅校长可设置校区")
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
        raise HTTPException(status_code=403, detail="仅校长可设置校区")
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


# ---------- 指定校区负责人（仅校长；可多选，选项含校长；可新建账号） ----------
class HeadAssign(BaseModel):
    user_ids: list[int] | None = None  # 多选：现有账号 id（含校长/教师/其他校区负责人）
    user_id: int | None = None         # 兼容旧单选项
    username: str | None = None        # 新建负责人账号：登录账号（填写则新建并添加）
    password: str | None = None        # 新建负责人账号：密码
    name: str | None = None            # 新建负责人账号：姓名
    phone: str | None = None           # 新建负责人账号：电话（可选）


def _sync_campus_head_roles(db: Session, org_id: int, campus_id: int, keep_ids: set[int], removed_ids: set[int]):
    """同步负责人角色：
    - 保留/新增的负责人：教师类角色升级为 sub_principal（校长不动），并归属该校区
    - 被移除的负责人：若不再管辖任何校区，则降级为教师（离职账号保持停用状态不动）
    """
    for uid in keep_ids:
        u = db.query(User).filter(User.id == uid, User.org_id == org_id).first()
        if not u or u.role == UserRole.PRINCIPAL or u.role == UserRole.PLATFORM:
            continue
        if u.role not in (UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD):
            u.role = UserRole.SUB_PRINCIPAL
        u.campus_id = campus_id
        u.resigned = False
        u.is_active = True  # 重新指定为负责人时恢复启用
    for uid in removed_ids:
        u = db.query(User).filter(User.id == uid, User.org_id == org_id).first()
        if not u or u.role == UserRole.PRINCIPAL:
            continue
        # 仍管辖其他校区则保留负责人角色，并把主校区指到剩余校区
        remaining = db.query(CampusHead).filter(
            CampusHead.user_id == uid, CampusHead.campus_id != campus_id
        ).order_by(CampusHead.id).all()
        if len(remaining) == 0 and is_head_role(u.role) and not u.resigned:
            u.role = UserRole.TEACHER
            u.campus_id = campus_id  # 降级为教师，保留校区归属
        elif remaining and u.campus_id == campus_id:
            u.campus_id = remaining[0].campus_id


@router.post("/{campus_id}/head")
def assign_campus_head(campus_id: int, data: HeadAssign, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """校长设置校区负责人：可多选（选项含校长/教师/其他校区负责人），也可新建账号并添加。

    - 传入 user_ids：以该集合替换校区现有负责人（不包含在集合中的将被移除）
    - 同时填写 username/password/name：新建负责人账号并加入最终负责人集合
    - 数据（学生/收支等）始终归属校区，更换负责人自动完成“数据交接”
    """
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅校长可指定负责人")
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == current_user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")

    org_id = current_user.org_id

    # 现有负责人集合（关联表；存量负责人已在启动迁移时回填）
    existing = {ch.user_id for ch in db.query(CampusHead).filter(
        CampusHead.org_id == org_id, CampusHead.campus_id == campus_id).all()}
    # 存量兼容：极老数据中未写入关联表的负责人（防止误移除）
    legacy_ids = {u.id for u in db.query(User).filter(
        User.org_id == org_id,
        User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
        User.campus_id == campus_id,
    ).all()}

    selected = list(data.user_ids or [])
    if data.user_id is not None and data.user_id not in selected:
        selected.append(data.user_id)

    # 校验所选账号均为本机构有效账号且角色合法（含校长）
    final_ids: set[int] = set()
    if selected:
        users = db.query(User).filter(User.id.in_(selected), User.org_id == org_id).all()
        if len(users) != len(set(selected)):
            raise HTTPException(status_code=400, detail="存在无效账号")
        for u in users:
            if u.role == UserRole.PLATFORM:
                raise HTTPException(status_code=400, detail="平台管理员不能设为校区负责人")
            if u.resigned and u.id not in existing:
                raise HTTPException(status_code=400, detail=f"「{u.name}」已离职，请先重新启用或另选他人")
        final_ids = {u.id for u in users}
    # 未传任何选择且未新建账号：视为取消全部负责人（兼容旧“清空取消”语义）
    if not selected and not (data.username or data.password or data.name):
        final_ids = set()
    # 仅新建账号（未多选现有账号）：保留现有负责人并追加新账号
    elif not selected:
        final_ids |= existing | legacy_ids

    # 新建负责人账号（可选）
    new_head = None
    if data.username or data.password or data.name:
        if not data.username or not data.password or not data.name:
            raise HTTPException(status_code=400, detail="新建负责人需填写姓名、登录账号、密码")
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="密码至少 6 位")
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="登录账号已存在")
        new_head = User(
            username=data.username.strip(),
            password_hash=hash_password(data.password),
            name=data.name.strip(),
            role=UserRole.SUB_PRINCIPAL,
            campus_id=campus.id,
            phone=data.phone,
            org_id=org_id,
        )
        db.add(new_head)
        db.flush()
        final_ids.add(new_head.id)

    removed = existing - final_ids

    # 同步关联表
    for uid in final_ids:
        if uid not in existing:
            db.add(CampusHead(org_id=org_id, campus_id=campus_id, user_id=uid))
    if removed:
        db.query(CampusHead).filter(
            CampusHead.org_id == org_id,
            CampusHead.campus_id == campus_id,
            CampusHead.user_id.in_(removed),
        ).delete(synchronize_session=False)

    _sync_campus_head_roles(db, org_id, campus_id, final_ids, removed)
    db.commit()

    heads = _campus_heads(db, org_id, campus_id)
    return {
        "detail": "负责人已设置",
        "campus_id": campus.id,
        "heads": heads,
        "head": next((h for h in heads if h["is_active"] and not h["resigned"]), None),
        "new_head": {"id": new_head.id, "name": new_head.name, "username": new_head.username} if new_head else None,
    }


# ---------- 校区负责人离职（仅校长）：账号停用、校区数据全部保留，供新负责人接管 ----------
class HeadResign(BaseModel):
    user_id: int


@router.post("/{campus_id}/head/resign")
def resign_campus_head(campus_id: int, data: HeadResign, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """校区负责人离职处理：
    - 负责人账号停用并标记离职（不可再登录）
    - 校区全部数据（学生/教师/收支/收费记录）原样保留
    - 该负责人名下直接负责的学生暂存至校区（teacher_id 置空），由校长/新负责人后续分配
    - 校长可在“负责人”中重新建号，新负责人即自动接管该校区全部数据
    """
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=403, detail="仅校长可办理负责人离职")
    campus = db.query(Campus).filter(Campus.id == campus_id, Campus.org_id == current_user.org_id).first()
    if not campus:
        raise HTTPException(status_code=404, detail="校区不存在")
    user = db.query(User).filter(User.id == data.user_id, User.org_id == current_user.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.role == UserRole.PRINCIPAL:
        raise HTTPException(status_code=400, detail="校长为机构所有者，不可办理离职")
    if user.role not in (UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD):
        raise HTTPException(status_code=400, detail="该账号不是校区负责人")

    is_head = db.query(CampusHead).filter(
        CampusHead.org_id == current_user.org_id,
        CampusHead.campus_id == campus_id,
        CampusHead.user_id == user.id,
    ).first() is not None
    legacy_head = user.campus_id == campus_id
    if not is_head and not legacy_head:
        raise HTTPException(status_code=400, detail="该账号不是该校区负责人")

    org_id = current_user.org_id
    # 1. 停用账号并标记离职
    user.is_active = False
    user.resigned = True
    user.resigned_at = datetime.utcnow()
    # 2. 从该校区负责人关联表中移除
    db.query(CampusHead).filter(
        CampusHead.org_id == org_id,
        CampusHead.campus_id == campus_id,
        CampusHead.user_id == user.id,
    ).delete(synchronize_session=False)
    # 若不再担任任何校区负责人，则降级为教师（账号仍停用，历史保留）；
    # 仍管辖其他校区时把主校区指到剩余校区
    remaining = db.query(CampusHead).filter(
        CampusHead.org_id == org_id, CampusHead.user_id == user.id
    ).order_by(CampusHead.id).all()
    if not remaining and is_head_role(user.role):
        user.role = UserRole.TEACHER
    elif remaining and user.campus_id == campus_id:
        user.campus_id = remaining[0].campus_id
    # 3. 名下学生暂存至校区（数据保留，教师置空，由校区负责人统一再分配）
    students = db.query(Student).filter(
        Student.org_id == org_id, Student.teacher_id == user.id, Student.deleted == False  # noqa: E712
    ).all()
    for s in students:
        s.teacher_id = None
        if s.campus_id is None:
            s.campus_id = campus_id  # 未归属校区的学生暂存到该校区
    db.commit()
    return {
        "detail": "负责人已办理离职",
        "user_id": user.id,
        "name": user.name,
        "campus_id": campus.id,
        "campus_student_kept": db.query(Student).filter(
            Student.org_id == org_id, Student.campus_id == campus.id, Student.deleted == False  # noqa: E712
        ).count(),
        "students_transferred": len(students),
        "tip": "校区数据已全部保留。请在“负责人”中新建账号，新负责人将自动接管本校区全部数据。",
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
    page: int | None = Query(default=None, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    campus_id: int | None = None,
    kind: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.PRINCIPAL and not is_head_role(current_user.role):
        raise HTTPException(status_code=403, detail="无权限查看收支明细")
    q = db.query(CampusTransaction).filter(CampusTransaction.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(CampusTransaction.campus_id.in_(managed))
    if campus_id:
        if is_head_role(current_user.role) and campus_id not in (managed_campus_ids(db, current_user) or set()):
            raise HTTPException(status_code=403, detail="只能查看自己校区的收支")
        q = q.filter(CampusTransaction.campus_id == campus_id)
    if kind:
        q = q.filter(CampusTransaction.kind == kind)
    q = q.order_by(CampusTransaction.record_date.desc(), CampusTransaction.id.desc())
    rows = (q.offset((page - 1) * page_size).limit(page_size).all()
            if page is not None else q.all())
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
        if txn.campus_id not in (managed_campus_ids(db, current_user) or set()):
            raise HTTPException(status_code=403, detail="只能删除自己校区的收支记录")
        if txn.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="只能删除自己登记的收支记录")
    db.delete(txn)
    db.commit()
    return {"detail": "已删除"}
