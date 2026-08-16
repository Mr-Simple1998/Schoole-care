from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, UserRole

# 生产环境请通过环境变量覆盖 SECRET_KEY
SECRET_KEY = "change_this_in_production_secret_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 小时

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录已过期或无权限，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    """依赖：校验当前用户角色"""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行此操作")
        return current_user
    return checker


def get_current_principal(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.PRINCIPAL:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅校长可执行此操作")
    return current_user


def is_head_role(role) -> bool:
    """是否为校区负责人类角色（新 sub_principal 或存量 campus_head）"""
    return role in (UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD)


def managed_campus_ids(db, user) -> set | None:
    """当前用户可管辖的校区 id 集合。

    - 校长（principal）：返回 None（可管全部校区）
    - 校区负责人/其他角色：返回 {user.campus_id} ∪ campus_heads 关联表中的校区
    """
    if user.role == UserRole.PRINCIPAL:
        return None
    from .models_campus import CampusHead
    ids: set = set()
    if getattr(user, "campus_id", None):
        ids.add(user.campus_id)
    for ch in db.query(CampusHead).filter(CampusHead.user_id == user.id).all():
        ids.add(ch.campus_id)
    return ids


def get_current_principal_or_head(current_user: User = Depends(get_current_user)) -> User:
    """校长或校区负责人可访问（校区负责人只能操作本校区数据）"""
    if current_user.role not in (UserRole.PRINCIPAL, UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅校长或校区负责人可执行此操作")
    return current_user


def get_current_platform(current_user: User = Depends(get_current_user)) -> User:
    """仅平台超级管理员可访问"""
    if current_user.role != UserRole.PLATFORM:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅平台管理员可执行此操作")
    return current_user