"""初始化数据库：创建默认超级管理员账号。
用法：在 backend 目录下执行 .venv 下的 python -m app.seed_admin
"""
import os

from sqlalchemy.orm import Session

from app.database import SessionLocal, Base, engine
from app.models import User, UserRole
from app.security import hash_password


def init_db():
    # 导入所有模型并建表
    from app import models, models_income, models_learning, models_points, models_subject  # noqa: F401
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    default_admin = os.environ.get("ADMIN_USERNAME", "admin")
    default_password = os.environ.get("ADMIN_PASSWORD", "admin123")

    exists = db.query(User).filter(User.username == default_admin).first()
    if exists:
        print(f"超级管理员账号 {default_admin} 已存在，跳过创建")
    else:
        admin = User(
            username=default_admin,
            password_hash=hash_password(default_password),
            name="超级管理员",
            role=UserRole.PLATFORM,
        )
        db.add(admin)
        db.commit()
        print(f"已创建默认超级管理员账号：{default_admin} / {default_password}")

    # 初始化默认学科分类
    from app.models_subject import Subject
    default_subjects = [
        ("语文", "学科", 1), ("数学", "学科", 2), ("英语", "学科", 3), ("托管", "学科", 4),
        ("魔方", "非学科", 1), ("书法", "非学科", 2), ("画画", "非学科", 3), ("轮滑", "非学科", 4),
    ]
    existing_names = {s.name for s in db.query(Subject).all()}
    added = 0
    for name, category, sort in default_subjects:
        if name not in existing_names:
            db.add(Subject(name=name, category=category, sort=sort))
            added += 1
    if added:
        db.commit()
        print(f"已初始化 {added} 个默认学科")
    else:
        print("学科数据已存在，跳过初始化")
    db.close()


if __name__ == "__main__":
    init_db()