from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine, SessionLocal

# 导入所有模型以注册到 Base（models_income/learning/points 已通过 models 传递）
from . import models  # noqa: F401
from . import models_income  # noqa: F401
from . import models_learning  # noqa: F401
from . import models_points  # noqa: F401
from . import models_subject  # noqa: F401
from . import models_campus  # noqa: F401

from .routers import auth, students, income, learning, points, dashboard, subjects, profile, platform, campuses, commissions

# 创建数据表
Base.metadata.create_all(bind=engine)


def _ensure_schema():
    """轻量自动迁移（SQLite）：为存量库补充新增字段，并把存量单负责人回填到 campus_heads 关联表。

    create_all 只会新建缺失的表，不会给既有表加列；这里做幂等的 ALTER/回填，
    保证老数据库升级后功能可用（正式迁移可继续使用 migrate.py）。
    """
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if engine.dialect.name != "sqlite" or "users" not in insp.get_table_names():
        return
    try:
        cols = {c["name"] for c in insp.get_columns("users")}
        with engine.begin() as conn:
            if "resigned" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN resigned BOOLEAN DEFAULT 0"))
            cols = {c["name"] for c in inspect(engine).get_columns("users")}
            if "resigned_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN resigned_at DATETIME"))
            cols = {c["name"] for c in inspect(engine).get_columns("users")}
            if "work_start_time" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN work_start_time VARCHAR(10)"))
            if "work_end_time" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN work_end_time VARCHAR(10)"))
            if "attendances" in insp.get_table_names():
                cols = {c["name"] for c in inspect(engine).get_columns("attendances")}
                if "is_cancelled" not in cols:
                    conn.execute(text("ALTER TABLE attendances ADD COLUMN is_cancelled BOOLEAN DEFAULT 0"))
                if "cancelled_at" not in cols:
                    conn.execute(text("ALTER TABLE attendances ADD COLUMN cancelled_at DATETIME"))
                if "cancelled_by" not in cols:
                    conn.execute(text("ALTER TABLE attendances ADD COLUMN cancelled_by INTEGER"))
                if "fee_record_id" not in cols:
                    conn.execute(text("ALTER TABLE attendances ADD COLUMN fee_record_id INTEGER"))
            if "campus_heads" not in insp.get_table_names():
                conn.execute(text("""
                    CREATE TABLE campus_heads (
                        id INTEGER NOT NULL PRIMARY KEY,
                        org_id INTEGER,
                        campus_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        assigned_at DATETIME
                    )
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_campus_heads_campus_id ON campus_heads (campus_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_campus_heads_user_id ON campus_heads (user_id)"))
        # 回填：存量校区负责人（sub_principal / campus_head 且已归属校区）写入关联表
        from sqlalchemy.orm import Session
        from .models import User, UserRole
        from .models_campus import CampusHead

        db: Session = SessionLocal()
        try:
            legacy = db.query(User).filter(
                User.role.in_([UserRole.SUB_PRINCIPAL, UserRole.CAMPUS_HEAD]),
                User.campus_id.isnot(None),
            ).all()
            for u in legacy:
                exists = db.query(CampusHead).filter(
                    CampusHead.campus_id == u.campus_id, CampusHead.user_id == u.id
                ).first()
                if not exists:
                    db.add(CampusHead(org_id=u.org_id, campus_id=u.campus_id, user_id=u.id))
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # 迁移失败不阻断启动（新库本身无需迁移）
        print("自动迁移跳过：", exc)


_ensure_schema()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

# 允许前端跨域访问（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源（头像上传等）
_static_dir = Path(__file__).resolve().parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(students.router, prefix="/api/students", tags=["学生"])
app.include_router(income.router, prefix="/api/income", tags=["收费"])
app.include_router(learning.router, prefix="/api/learning", tags=["学习"])
app.include_router(points.router, prefix="/api/points", tags=["积分"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["工作台"])
app.include_router(subjects.router, prefix="/api/subjects", tags=["学科"])
app.include_router(profile.router, prefix="/api/profile", tags=["个人资料"])
app.include_router(platform.router, prefix="/api/platform", tags=["平台管理"])
app.include_router(campuses.router, prefix="/api/campuses", tags=["校区管理"])
app.include_router(commissions.router, prefix="/api/commissions", tags=["提成"])


@app.get("/")
def read_root():
    return {"message": f"{settings.app_name} 运行中", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- 生产环境：托管 PC 前端构建产物（同一端口提供 /api + 静态页面） ----------
# 配置环境变量 FRONTEND_DIST=<前端 dist 目录> 后生效：/assets 静态资源 + 其余路径兜底返回
# index.html（支持 Vue Router history 模式；/api、/static、/docs 等已有路由优先匹配）
if settings.frontend_dist:
    _fe_dir = Path(settings.frontend_dist).resolve()
    if (_fe_dir / "index.html").exists():
        _fe_assets = _fe_dir / "assets"
        if _fe_assets.is_dir():
            app.mount("/assets", StaticFiles(directory=_fe_assets), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def _spa_fallback(full_path: str):
            """前端 history 路由兜底：非 API 路径一律返回 index.html"""
            return FileResponse(_fe_dir / "index.html")
