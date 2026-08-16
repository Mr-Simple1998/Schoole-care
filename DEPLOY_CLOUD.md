# 微信云托管部署指南（后端 FastAPI + 小程序）

> 目标：把本地 FastAPI 后端部署到微信云托管（CloudBase Run），小程序改为调用云托管域名，实现手机端真实可用。

## 前提

- 小程序使用**真实注册 AppID**（测试号无法使用云服务）
- 微信开发者工具已登录，且已开通云开发环境
- GitHub 仓库 `Mr-Simple1998/tuoguan-system` 已推送最新代码（含 `backend/Dockerfile`）

## 一、后端部署到微信云托管

1. 用真实 AppID 打开小程序项目（`weapp/dist/build/mp-weixin`），进入「云开发」控制台，**开通环境**（如 `tuoguan-prod`）。
2. 打开「云托管」→「新建服务」：
   - 服务名：`tuoguan-api`
   - 构建方式：**从代码仓库构建**（关联 GitHub 仓库 `Mr-Simple1998/tuoguan-system`）
   - 构建目录：`backend`（自动识别 `backend/Dockerfile`）
   - 分支：`main`
3. 服务配置：
   - **端口**：`80`
   - **健康检查路径**：`/health`
   - CPU/内存：1核/2G 起步，按量计费
   - 实例数：最小 0 ~ 最大 2（冷启动自动拉起）
4. 点击「部署」，等待构建成功（首次拉取 python:3.14-slim 镜像较慢）。
5. 部署成功后，在服务详情页拿到**默认域名**，形如：
   `https://tuoguan-api-xxxxxxxx.ap-shanghai.run.tcloudbase.com`（以控制台实际为准）。

### 数据库持久化（重要）

- 云托管实例磁盘是**临时**的，重启会丢数据。请在服务配置中**挂载 CFS 文件存储**到 `/data`，
  并把环境变量 `DATABASE_URL` 设为 `sqlite:////data/tortoise.db`（Dockerfile 已默认该路径，挂载后即持久化）。
- 首次启动后需初始化管理员账号：进入容器终端执行
  `python -m app.seed_admin`（或在部署前把种子逻辑放入启动脚本）。

### 微信登录凭证

在云托管服务「环境变量」中配置（对应 `backend/app/config.py`）：
- `WX_APPID` = 你的真实小程序 AppID
- `WX_SECRET` = 小程序密钥
- `DEBUG` = `false`

不配置时后端退化为本地模拟模式（code 当 openid），真实手机端无法正常登录。

## 二、小程序端对接

1. 修改 `weapp/src/utils/request.js`：
   ```js
   const BASE_URL = 'https://你的云托管域名/api';
   ```
2. 修改 `weapp/src/manifest.json`：`mp-weixin.appid` 改为真实 AppID。
3. 重新构建：
   ```powershell
   cd weapp
   npm run build:mp-weixin
   ```
4. 上传体验版：
   ```powershell
   & "E:\微信小程序开发工具\微信web开发者工具\cli.bat" upload --project "C:\Users\DZY\Desktop\后台管理系统\weapp\dist\build\mp-weixin" -v 1.0.0 -d "云托管部署版"
   ```
5. 在微信后台「版本管理」把体验版设为可用，手机扫码体验。

## 三、PC 端对接

- `frontend/src/utils/request.js` 的 BASE_URL 同样改为云托管域名（可选，PC 端也可继续用本地后端）。

## 四、完整系统镜像（PC 前端 + 后端，根目录 Dockerfile）

仓库根目录的 `Dockerfile` 提供**一体化镜像**：多阶段构建 PC 前端（Vue3+Vite），再与 FastAPI 后端打进同一容器，由后端同端口托管（`/api/*` 接口 + `/assets` 静态资源 + history 路由兜底返回 `index.html`）。

```powershell
# 构建
docker build -t tuoguan-system .

# 运行（SQLite 数据挂载到 /data 持久化；端口映射 8000）
docker run -d --name tuoguan `
  -p 8000:8000 `
  -v tuoguan-data:/data `
  -e DATABASE_URL=sqlite:////data/tortoise.db `
  -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=admin123 `
  tuoguan-system
```

- 启动时自动执行幂等的 `python -m app.seed_admin`（不存在才创建 admin / 默认学科）。
- 访问 `http://localhost:8000` 即 PC 管理端；接口文档 `http://localhost:8000/docs`。
- 可选环境变量：`PORT`（默认 8000）、`WX_APPID`/`WX_SECRET`（真实小程序登录）、`DEBUG`（默认 false）。
- 微信小程序（weapp/）产物需用微信开发者工具上传，不包含在本镜像内；将 `weapp/src/utils/request.js` 的 BASE_URL 指向本服务域名即可对接。
- 后端单独的云托管镜像见 `backend/Dockerfile`（微信云托管「从代码仓库构建」时识别）。

## 注意事项

- 云托管是**按量付费**服务（0 实例时不计费，有请求才拉起），个人小程序也可用。
- 微信要求正式环境请求走 **HTTPS + 已备案域名**；体验版可临时用默认域名（https 已具备）。
- 头像等静态文件会上传到容器临时磁盘，重启丢失；如需持久化请改用云存储。
