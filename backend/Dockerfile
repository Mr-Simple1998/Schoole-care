# 微信云托管部署用镜像（从 GitHub 仓库代码构建时自动识别本 Dockerfile）
FROM python:3.14-slim

WORKDIR /app

# 安装依赖（各包均有 cp314 manylinux wheel，无需编译）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app ./app

# 静态资源目录（头像上传）
RUN mkdir -p /app/app/static/uploads

# 云托管默认监听 80 端口（在云托管服务配置中保持一致）
ENV PORT=80
EXPOSE 80

# SQLite 数据目录：云托管实例磁盘是临时的，请在云托管服务中挂载
# CFS 文件存储到 /data 以实现数据持久化（否则重启实例数据会丢失）
RUN mkdir -p /data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
