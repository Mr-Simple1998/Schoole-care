from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserRole, Student
from ..models_subject import Subject, teacher_subjects
from ..security import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_principal, get_current_principal_or_head, is_head_role,
    managed_campus_ids,
)

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "teacher"  # 仅教师（校长由平台开户创建；校区负责人由校长在校区管理页开号）
    email: str | None = None
    phone: str | None = None
    campus_id: int | None = None  # 所属校区（可选）
    subject_ids: list[int] | None = None  # 教师所属学科（可多选）


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    campus_id: int | None = None  # 所属校区（可选）
    subject_ids: list[int] | None = None  # 教师所属学科


class SubjectOut(BaseModel):
    id: int
    name: str
    category: str

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None
    phone: str | None
    avatar: str | None = None
    is_active: bool
    resigned: bool = False
    campus_id: int | None = None
    campus_name: str | None = None
    work_start_time: str | None = None
    work_end_time: str | None = None
    subjects: list[SubjectOut] = []  # 所属学科

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(user) -> UserOut:
    out = UserOut.model_validate(user)
    if user.campus:
        out.campus_name = user.campus.name
    return out


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录：使用账号密码，返回 JWT"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=_user_out(user))


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)


def _set_teacher_subjects(db: Session, user: User, subject_ids: list[int] | None):
    """更新教师所属学科；subject_ids 为 None 表示不修改"""
    if subject_ids is None:
        return
    if len(subject_ids) != len(set(subject_ids)):
        raise HTTPException(status_code=400, detail="学科不能重复")
    subs = db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
    if len(subs) != len(subject_ids):
        raise HTTPException(status_code=400, detail="存在无效学科")
    user.subjects = subs


@router.post("/register", response_model=UserOut)
def register_teacher(data: UserCreate, current_user: User = Depends(get_current_principal_or_head), db: Session = Depends(get_db)):
    """校长/校区负责人创建教师账号（新增教师固定为教师角色；校长由平台开户创建，校区负责人由校长在校区管理页开号）"""
    if data.role != "teacher":
        raise HTTPException(status_code=400, detail="只能创建教师账号")
    # 校区负责人/归属了校区的校长：新建教师默认归属同一校区；多校区负责人可在其管辖校区中选择
    if is_head_role(current_user.role) or (current_user.role == UserRole.PRINCIPAL and current_user.campus_id):
        if current_user.role == UserRole.PRINCIPAL:
            # 校长管辖全部校区：保留所选校区（由下方校验是否属于本机构）；未指定时默认其归属校区，
            # 避免新建教师无校区归属导致其新增学生在校长/校长端不可见
            if data.campus_id is None:
                data.campus_id = current_user.campus_id
        else:
            managed = managed_campus_ids(db, current_user) or set()
            if data.campus_id in managed:
                pass  # 使用所选校区
            else:
                data.campus_id = current_user.campus_id if current_user.campus_id in managed else (next(iter(managed), None))
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if data.campus_id is not None:
        from ..models_campus import Campus
        if not db.query(Campus).filter(Campus.id == data.campus_id, Campus.org_id == current_user.org_id).first():
            raise HTTPException(status_code=400, detail="校区不存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        role=UserRole.TEACHER,
        email=data.email,
        phone=data.phone,
        campus_id=data.campus_id,
        org_id=current_user.org_id,
    )
    _set_teacher_subjects(db, user, data.subject_ids)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.get("/teachers", response_model=list[UserOut])
def list_teachers(
    campus_id: int | None = None,
    current_user: User = Depends(get_current_principal_or_head),
    db: Session = Depends(get_db),
):
    """校长查看本机构全部账号（校长/校区负责人/教师，可按校区筛选）；校区负责人仅见本校区（可多校区）教师。
    含校长本人：校长/校区负责人也可以拥有自己的学生，可作为学生的负责教师被选择。"""
    q = db.query(User).filter(
        User.role.in_([UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD, UserRole.PRINCIPAL]),
        User.org_id == current_user.org_id,
    )
    if current_user.role == UserRole.PRINCIPAL:
        # 校长：可见机构全部账号（含各校区负责人及其所属校区的教师），可按校区筛选
        if campus_id is not None:
            q = q.filter(User.campus_id == campus_id)
    elif is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed))
    return [_user_out(u) for u in q.order_by(User.id).all()]


@router.get("/users", response_model=list[UserOut])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """账号列表（校长见机构全部；校区负责人见本校区全部（可多校区）；教师仅见自己）"""
    if current_user.role == UserRole.PRINCIPAL:
        return [_user_out(u) for u in db.query(User).filter(User.org_id == current_user.org_id).all()]
    if is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        return [_user_out(u) for u in db.query(User).filter(
            User.org_id == current_user.org_id, User.campus_id.in_(managed)).all()]
    return [_user_out(current_user)]


@router.delete("/users/{user_id}", response_model=UserOut)
def delete_user(user_id: int, current_user: User = Depends(get_current_principal_or_head), db: Session = Depends(get_db)):
    """校长/校区负责人：停用本机构（本校区）账号"""
    q = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        # 校区负责人只能停用本校区教师账号
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.delete("/teachers/{user_id}")
def delete_teacher(user_id: int, current_user: User = Depends(get_current_principal_or_head), db: Session = Depends(get_db)):
    """校长/校区负责人：删除本机构（本校区）教师账号。该账号名下有在读学生时禁止删除（请先办理离职，学生将自动暂存校区）。"""
    q = db.query(User).filter(
        User.id == user_id,
        User.org_id == current_user.org_id,
        User.role.in_([UserRole.TEACHER, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
    )
    if is_head_role(current_user.role):
        # 校区负责人只能删除本校区教师账号（不可删除校区负责人）
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="教师账号不存在")
    student_count = db.query(Student).filter(
        Student.teacher_id == user.id,
        Student.deleted == False,  # noqa: E712
    ).count()
    if student_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该教师名下有 {student_count} 名在读学生，请先办理离职（学生自动暂存校区）或转移学生后再删除教师账号",
        )
    # 先清理教师-学科关联、校区负责人关联，再删除账号
    db.execute(teacher_subjects.delete().where(teacher_subjects.c.teacher_id == user.id))
    from ..models_campus import CampusHead
    db.query(CampusHead).filter(CampusHead.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return {"detail": "已删除"}


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, current_user: User = Depends(get_current_principal_or_head), db: Session = Depends(get_db)):
    """校长/校区负责人：编辑本机构（本校区）教师账号信息及其所属学科；重新启用离职账号时清除离职标记"""
    q = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        # 校区负责人只能编辑本校区教师账号（不可编辑校区负责人）
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    payload = data.model_dump(exclude_unset=True, exclude={"subject_ids"})
    if is_head_role(current_user.role):
        # 校区负责人可把教师调整到其管辖的任一校区（多校区时不再强制主校区）
        managed = managed_campus_ids(db, current_user) or set()
        if "campus_id" in payload and payload["campus_id"] not in managed:
            raise HTTPException(status_code=400, detail="只能设置教师到您管辖的校区")
    for k, v in payload.items():
        setattr(user, k, v)
    # 重新启用：清除离职标记（离职数据仍保留在原校区）
    if payload.get("is_active") is True:
        user.resigned = False
        user.resigned_at = None
    if "subject_ids" in data.model_dump(exclude_unset=True):
        _set_teacher_subjects(db, user, data.subject_ids)
    db.commit()
    db.refresh(user)
    return _user_out(user)


class ResetPassword(BaseModel):
    password: str = Query(..., min_length=6, description="新密码")


class WorkTimeUpdate(BaseModel):
    """设置教师上下班打卡时间（HH:MM）"""
    work_start_time: str | None = None
    work_end_time: str | None = None


@router.put("/users/{user_id}/work-time", response_model=UserOut)
def update_teacher_work_time(
    user_id: int,
    data: WorkTimeUpdate,
    current_user: User = Depends(get_current_principal_or_head),
    db: Session = Depends(get_db),
):
    """校长/校区负责人：设置教师的上下班打卡时间，用于教师工作台打卡与月度考勤汇总标记"""
    q = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        # 校区负责人只能设置本校区教师
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="教师账号不存在")
    if data.work_start_time is not None:
        user.work_start_time = data.work_start_time.strip() or None
    if data.work_end_time is not None:
        user.work_end_time = data.work_end_time.strip() or None
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.put("/users/{user_id}/reset-password")
def reset_teacher_password(
    user_id: int,
    data: ResetPassword,
    current_user: User = Depends(get_current_principal_or_head),
    db: Session = Depends(get_db),
):
    """校长/校区负责人：重置本机构（本校区）教师密码（教师忘记密码时使用）"""
    q = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        # 校区负责人只能重置本校区教师密码（不可重置校区负责人）
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    user.password_hash = hash_password(data.password)
    db.commit()
    return {"detail": "密码已重置"}


# ========== 离职处理（教师 / 校区负责人） ==========

@router.post("/users/{user_id}/resign")
def resign_user(user_id: int, current_user: User = Depends(get_current_principal_or_head), db: Session = Depends(get_db)):
    """办理离职：停用账号并标记离职；其名下所有学生数据全部保留，暂存至学生所属校区（teacher_id 置空），
    由校长/校区负责人后续分配给其他教师或新账号。

    - 校区负责人离职：校区全部数据（学生/教师/收支/收费记录）原样保留，校长可重新建号后自动接管
    - 教师离职：名下学生暂存至校区负责人处（校区可见、可再分配）
    """
    q = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id)
    if is_head_role(current_user.role):
        # 校区负责人只能办理本校区教师离职（负责人离职由校长在“校区管理-负责人”中办理）
        managed = managed_campus_ids(db, current_user) or set()
        q = q.filter(User.campus_id.in_(managed), User.role == UserRole.TEACHER)
    user = q.first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.role == UserRole.PRINCIPAL:
        raise HTTPException(status_code=400, detail="校长为机构所有者，不可办理离职")
    if user.role == UserRole.PLATFORM:
        raise HTTPException(status_code=400, detail="平台管理员不可办理离职")

    org_id = current_user.org_id
    # 1. 停用账号并标记离职
    user.is_active = False
    user.resigned = True
    user.resigned_at = datetime.utcnow()
    # 2. 若是校区负责人：移除其所有校区负责人关联（校区数据保留），不再担任负责人时降级为教师
    from ..models_campus import CampusHead
    head_rows = db.query(CampusHead).filter(
        CampusHead.org_id == org_id, CampusHead.user_id == user.id
    ).delete(synchronize_session=False)
    if head_rows and is_head_role(user.role):
        user.role = UserRole.TEACHER
    # 3. 名下学生暂存至其所属校区（数据保留，教师置空）
    students = db.query(Student).filter(
        Student.org_id == org_id, Student.teacher_id == user.id, Student.deleted == False  # noqa: E712
    ).all()
    for s in students:
        s.teacher_id = None
        if s.campus_id is None and user.campus_id:
            s.campus_id = user.campus_id  # 未归属校区的学生暂存到教师所属校区
    db.commit()
    return {
        "detail": "离职办理完成",
        "user_id": user.id,
        "name": user.name,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "students_transferred": len(students),
        "head_links_removed": head_rows,
        "tip": "所有学生数据已保留并暂存至所在校区（负责人可见），可分配给其他教师或新建账号后分配。",
    }


# ========== 微信小程序登录（本地开发模式） ==========

class WxLogin(BaseModel):
    """微信登录：code 为 wx.login 返回的临时凭证。
    本地开发未配置真实 AppID/Secret 时，code 由前端生成本地 openid 模拟，
    后端直接把它当作 openid 使用，保证本地可完整跑通登录绑定流程。
    """
    code: str = Field(..., min_length=1, max_length=128)
    device_id: str | None = None


class WxBind(BaseModel):
    """微信绑定：使用账号密码绑定当前微信 openid"""
    username: str
    password: str
    wx_openid: str = Field(..., min_length=1, max_length=128)
    device_id: str | None = None


def _wx_openid(code: str, device_id: str | None = None) -> str:
    """将 wx.login 的临时 code 换取微信 openid。
    未配置 WX_APPID/WX_SECRET 时退化为本地开发模拟：直接把 code 作为 openid。
    """
    from ..config import settings
    if not settings.wx_appid or not settings.wx_secret:
        return device_id or code
    import urllib.parse
    import urllib.request
    import json
    params = urllib.parse.urlencode({
        "appid": settings.wx_appid,
        "secret": settings.wx_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    })
    url = "https://api.weixin.qq.com/sns/jscode2session?" + params
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="微信登录服务调用失败")
    if data.get("errcode"):
        # 微信返回错误码时，回退到模拟模式（便于本地无网络/凭证联调）
        if data.get("errcode") in (40013, 40125, 40029):
            return code
        raise HTTPException(status_code=400, detail="微信登录失败: " + str(data.get("errmsg")))
    return data.get("openid") or code


@router.post("/wx-login", response_model=Token)
def wx_login(data: WxLogin, db: Session = Depends(get_db)):
    """小程序静默登录：用微信 openid 查找已绑定账号，命中则返回 JWT"""
    openid = _wx_openid(data.code, data.device_id)
    user = db.query(User).filter(User.wx_openid == openid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_BOUND")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=_user_out(user))


@router.post("/wx-bind", response_model=Token)
def wx_bind(data: WxBind, db: Session = Depends(get_db)):
    """小程序绑定登录：校验账号密码，绑定当前微信 openid，返回 JWT"""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    # 用 code 换取真实 openid 再绑定，避免存入一次性临时 code 导致后续静默登录匹配不上
    user.wx_openid = _wx_openid(data.wx_openid, data.device_id)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=_user_out(user))
