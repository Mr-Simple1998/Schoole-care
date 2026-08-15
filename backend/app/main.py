from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine

# 导入所有模型以注册到 Base（models_income/learning/points 已通过 models 传递）
from . import models  # noqa: F401
from . import models_income  # noqa: F401
from . import models_learning  # noqa: F401
from . import models_points  # noqa: F401
from . import models_subject  # noqa: F401

from .routers import auth, students, income, learning, points, dashboard, subjects, profile, platform

# 创建数据表
Base.metadata.create_all(bind=engine)

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


@app.get("/")
def read_root():
    return {"message": f"{settings.app_name} 运行中", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}