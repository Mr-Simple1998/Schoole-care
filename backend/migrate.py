"""多租户数据迁移：为现有数据库补充 org_id/avatar 字段，建立默认机构与平台管理员账号"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text
from datetime import datetime

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app import models_income  # noqa: F401
from app import models_learning  # noqa: F401
from app import models_points  # noqa: F401
from app import models_subject  # noqa: F401
from app import models_campus  # noqa: F401
from app.models import Organization, User, UserRole
from app.security import hash_password


def add_column_if_missing(conn, table, column, ddl):
    cols = {r[1] for r in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
    if column not in cols:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
        print(f"  + {table}.{column}")
    else:
        print(f"  = {table}.{column} 已存在")


def main():
    # 1. 创建新表（organizations）
    Base.metadata.create_all(bind=engine)
    print("create_all 完成（organizations 表已创建）")

    conn = engine.connect()
    trans = conn.begin()
    try:
        # 2. 为既有表补充字段
        print("补充字段：")
        add_column_if_missing(conn, "users", "org_id", "INTEGER")
        add_column_if_missing(conn, "users", "avatar", "VARCHAR(255)")
        add_column_if_missing(conn, "users", "resigned", "BOOLEAN DEFAULT 0")
        add_column_if_missing(conn, "users", "resigned_at", "DATETIME")
        add_column_if_missing(conn, "users", "work_start_time", "VARCHAR(10)")
        add_column_if_missing(conn, "users", "work_end_time", "VARCHAR(10)")
        # 校区（2026：校区管理功能）
        add_column_if_missing(conn, "students", "campus_id", "INTEGER")
        add_column_if_missing(conn, "users", "campus_id", "INTEGER")
        for t in ["students", "subjects", "fee_records", "invoices", "refund_adjustments",
                  "installments", "installment_records", "scores", "attendances", "homework",
                  "class_performances", "point_records", "point_settings", "prizes", "redemptions"]:
            add_column_if_missing(conn, t, "org_id", "INTEGER")

        trans.commit()
    except Exception as e:
        trans.rollback()
        print("补充字段失败，回滚：", e)
        raise
    conn.close()

    # 3. 种子数据：默认机构 + 平台管理员 + 数据归并
    db = SessionLocal()
    try:
        # 默认机构
        org = db.query(Organization).filter(Organization.code == "DEFAULT").first()
        if not org:
            org = Organization(name="默认机构", code="DEFAULT", contact="系统管理员")
            db.add(org)
            db.flush()
            print("已创建默认机构 id=", org.id)

        # 平台管理员
        if not db.query(User).filter(User.username == "platform").first():
            db.add(User(
                username="platform",
                password_hash=hash_password("admin123"),
                name="平台管理员",
                role=UserRole.PLATFORM,
                org_id=None,
            ))
            print("已创建平台管理员：platform / admin123")

        # 现有普通用户（校长/教师）归属默认机构
        orphan_users = db.query(User).filter(User.role.in_([UserRole.PRINCIPAL, UserRole.TEACHER]), User.org_id.is_(None)).all()
        for u in orphan_users:
            u.org_id = org.id
        print(f"已为 {len(orphan_users)} 个校长/教师账号设置机构")

        # 存量校区负责人回填到 campus_heads 关联表（多负责人功能）
        from app.models_campus import CampusHead
        legacy_heads = db.query(User).filter(
            User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
            User.campus_id.isnot(None),
        ).all()
        backfilled = 0
        for u in legacy_heads:
            if not db.query(CampusHead).filter(
                CampusHead.campus_id == u.campus_id, CampusHead.user_id == u.id
            ).first():
                db.add(CampusHead(org_id=u.org_id, campus_id=u.campus_id, user_id=u.id))
                backfilled += 1
        if backfilled:
            print(f"campus_heads: {backfilled} 条负责人关联已回填")

        # 现有业务数据归属默认机构
        for t in ["students", "subjects", "fee_records", "invoices", "refund_adjustments",
                  "installments", "installment_records", "scores", "attendances", "homework",
                  "class_performances", "point_records", "point_settings", "prizes", "redemptions"]:
            n = db.execute(text(f"UPDATE {t} SET org_id = {org.id} WHERE org_id IS NULL")).rowcount
            if n:
                print(f"  {t}: {n} 条数据归入默认机构")

        db.commit()
        print("迁移完成 ✓")
    finally:
        db.close()


if __name__ == "__main__":
    main()