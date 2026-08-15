import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..security import get_current_user, hash_password, verify_password

router = APIRouter()

# 头像上传存储目录（相对 backend 运行目录）
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class ProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    avatar: str | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.get("")
def get_profile(current_user: User = Depends(get_current_user)):
    """当前登录用户个人资料"""
    return _profile_out(current_user)


def _profile_out(u: User):
    return {
        "id": u.id,
        "username": u.username,
        "name": u.name,
        "role": u.role,
        "email": u.email,
        "phone": u.phone,
        "avatar": u.avatar,
        "org_id": u.org_id,
    }


@router.put("")
def update_profile(data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """修改自己的账号资料（姓名/电话/邮箱/头像）"""
    upd = data.model_dump(exclude_unset=True)
    for k, v in upd.items():
        setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return _profile_out(current_user)


@router.put("/password")
def change_password(data: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """修改自己的密码（需验证原密码）"""
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"detail": "密码修改成功，请重新登录"}


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """上传头像，返回可访问的 URL"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="仅支持 png/jpg/jpeg/gif/webp 图片")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")

    fname = f"u{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
    dest = UPLOAD_DIR / fname
    content = await file.read()
    dest.write_bytes(content)
    url = f"/static/uploads/{fname}"
    return {"url": url}