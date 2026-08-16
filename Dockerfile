# =====================================================================
# 机构后台学习管理系统 — 完整系统镜像（PC 前端 + 后端 API 同容器）
#
# 构建：
#   docker build -t tuoguan-system .
#
# 运行（SQLite 数据挂载到 /data 持久化，端口映射为 8000）：
#   docker run -d --name tuoguan \
#     -p 8000:8000 \
#     -v tuoguan-data:/data \
#     -e DATABASE_URL=sqlite:////data/tortoise.db \
#     -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 \
#     tuoguan-system
#
# 访问：
#   PC 管理端 http://localhost:8000
#   API（同源）http://localhost:8000/api/*   接口文档 http://localhost:8000/docs
#
# 说明：
#   - 微信小程序（weapp/）构建产物需通过微信开发者工具上传，不包含在本镜像中；
#     小程序端请求地址改为本服务域名后即可使用。
#   - 后端另有 backend/Dockerfile 供微信云托管「从代码仓库构建」使用（仅后端）。
# =====================================================================

# ---------- 阶段 1：构建 PC 前端（Vue3 + Vite） ----------
FROM node:22-alpine AS frontend-builder
WORKDIR /build

# 先装依赖（有 lockfile 用 npm ci，缺失/不同步时回退 npm install）
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# ---------- 阶段 2：后端运行环境（FastAPI + SQLite） ----------
FROM python:3.14-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 后端依赖（各包均有 cp314 manylinux wheel，无需编译）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 后端应用代码
COPY backend/app ./app

# PC 前端构建产物（由 FastAPI 同端口托管，支持 history 路由）
COPY --from=frontend-builder /build/dist ./frontend_dist

# SQLite 数据目录（挂载卷实现持久化）与头像上传目录
RUN mkdir -p /data /app/app/static/uploads

ENV PORT=8000 \
    FRONTEND_DIST=/app/frontend_dist \
    DATABASE_URL=sqlite:////data/tortoise.db \
    DEBUG=false

EXPOSE 8000

# 健康检查：命中 /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/health'%os.environ.get('PORT','8000'),timeout=3)"

# 启动：先幂等初始化超级管理员与默认学科（seed_admin），再启动 API 服务
CMD ["sh", "-c", "python -m app.seed_admin && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
