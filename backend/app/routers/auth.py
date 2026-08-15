from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserRole, Student
from ..models_subject import Subject, teacher_subjects
from ..security import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_principal,
)

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "teacher"  # principal / teacher
    email: str | None = None
    phone: str | None = None
    subject_ids: list[int] | None = None  # 教师所属学科（可多选）


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
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
    subjects: list[SubjectOut] = []  # 所属学科

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录：使用账号密码，返回 JWT"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


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
def register_teacher(data: UserCreate, current_user: User = Depends(get_current_principal), db: Session = Depends(get_db)):
    """仅校长可创建账号（教师或校长），账号归属当前机构"""
    if data.role not in ("teacher", "principal"):
        raise HTTPException(status_code=400, detail="角色不合法")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        role=UserRole(data.role),
        email=data.email,
        phone=data.phone,
        org_id=current_user.org_id,
    )
    _set_teacher_subjects(db, user, data.subject_ids)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/teachers", response_model=list[UserOut])
def list_teachers(current_user: User = Depends(get_current_principal), db: Session = Depends(get_db)):
    """校长：查看本机构教师账号列表"""
    return db.query(User).filter(User.role == UserRole.TEACHER, User.org_id == current_user.org_id).all()


@router.get("/users", response_model=list[UserOut])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """当前用户列表（校长可见本机构全部，教师仅见自己）"""
    if current_user.role == UserRole.PRINCIPAL:
        return db.query(User).filter(User.org_id == current_user.org_id).all()
    return [current_user]


@router.delete("/users/{user_id}", response_model=UserOut)
def delete_user(user_id: int, current_user: User = Depends(get_current_principal), db: Session = Depends(get_db)):
    """校长：停用本机构账号"""
    user = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.delete("/teachers/{user_id}")
def delete_teacher(user_id: int, current_user: User = Depends(get_current_principal), db: Session = Depends(get_db)):
    """校长：删除本机构教师账号。该教师名下有在读学生时禁止删除。"""
    user = db.query(User).filter(
        User.id == user_id,
        User.org_id == current_user.org_id,
        User.role == UserRole.TEACHER,
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="教师账号不存在")
    student_count = db.query(Student).filter(
        Student.teacher_id == user.id,
        Student.deleted == False,  # noqa: E712
    ).count()
    if student_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该教师名下有 {student_count} 名在读学生，请先转移或删除这些学生后再删除教师账号",
        )
    # 先清理教师-学科关联，再删除账号
    db.execute(teacher_subjects.delete().where(teacher_subjects.c.teacher_id == user.id))
    db.delete(user)
    db.commit()
    return {"detail": "已删除"}


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, current_user: User = Depends(get_current_principal), db: Session = Depends(get_db)):
    """校长：编辑本机构教师账号信息及其所属学科"""
    user = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    for k, v in data.model_dump(exclude_unset=True, exclude={"subject_ids"}).items():
        setattr(user, k, v)
    if "subject_ids" in data.model_dump(exclude_unset=True):
        _set_teacher_subjects(db, user, data.subject_ids)
    db.commit()
    db.refresh(user)
    return user


class ResetPassword(BaseModel):
    password: str = Query(..., min_length=6, description="新密码")


@router.put("/users/{user_id}/reset-password")
def reset_teacher_password(
    user_id: int,
    data: ResetPassword,
    current_user: User = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """校长：重置本机构教师密码（教师忘记密码时使用）"""
    user = db.query(User).filter(User.id == user_id, User.org_id == current_user.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    user.password_hash = hash_password(data.password)
    db.commit()
    return {"detail": "密码已重置"}


# ========== 微信小程序登录（本地开发模式） ==========

class WxLogin(BaseModel):
    """微信登录：code 为 wx.login 返回的临时凭证。
    本地开发未配置真实 AppID/Secret 时，code 由前端生成本地 openid 模拟，
    后端直接把它当作 openid 使用，保证本地可完整跑通登录绑定流程。
    """
    code: str = Field(..., min_length=1, max_length=128)


class WxBind(BaseModel):
    """微信绑定：使用账号密码绑定当前微信 openid"""
    username: str
    password: str
    wx_openid: str = Field(..., min_length=1, max_length=128)


def _wx_openid(code: str) -> str:
    """将 wx.login 的临时 code 换取微信 openid。
    未配置 WX_APPID/WX_SECRET 时退化为本地开发模拟：直接把 code 作为 openid。
    """
    from ..config import settings
    if not settings.wx_appid or not settings.wx_secret:
        return code
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
    openid = _wx_openid(data.code)
    user = db.query(User).filter(User.wx_openid == openid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_BOUND")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/wx-bind", response_model=Token)
def wx_bind(data: WxBind, db: Session = Depends(get_db)):
    """小程序绑定登录：校验账号密码，绑定当前微信 openid，返回 JWT"""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    user.wx_openid = data.wx_openid
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))