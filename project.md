# 机构后台学习管理系统 — 项目说明（v3 · 2026-08-16 更新）

> 后端托管的机构后台管理系统，含平台开户、总校长/校长管理号/教师多端、学生档案、收费核销、积分、考勤、校区管理等功能。
> 本文档用于快速了解项目架构、开发约定、踩坑记录，避免下次更新时重新扫描全项目或重踩环境问题。

---

## 0. 项目现状（本次会话后）

| 项 | 值 |
|----|----|
| 仓库 | `git@github.com:Mr-Simple1998/tuoguan-system.git`（私有，SSH 认证） |
| 本地位置 | `C:\Users\DZY\Desktop\后台管理系统`（克隆于 2026-08-15） |
| 分支 | `main`（跟踪 origin/main） |
| 角色体系 | **已梳理**（总校长 principal / 校长管理号 sub_principal / 教师 teacher / 平台 platform，详见 §4） |
| 三端 | PC 端 + 小程序均支持新角色与校区数据隔离（详见 §8） |
| 后端 | FastAPI，端口 8000（运行中），SQLite `backend/tortoise.db` 已初始化 |
| 前端 | Vue3 + Vite，端口 5173（运行中） |
| 小程序 | 已 `build:mp-weixin` 构建，产物 `weapp/dist/build/mp-weixin`，已导入微信开发者工具 |
| 本次新增 | 教师上下班打卡 · 全体学生考勤日历 · 学生打卡权限分离（详见 §8） |

---

## 1. 技术栈

| 端 | 技术 |
|----|------|
| 后端 | Python 3.14 + FastAPI 0.141 + SQLAlchemy 2.0 + Pydantic 2 + SQLite |
| 前端 | Vue 3.5 + Vite 8 + Element Plus 2.14 + Pinia + Vue Router 4 + ECharts |
| 小程序 | uni-app（Vue3 + Vite 5 + Pinia），微信小程序 mp-weixin |
| 认证 | JWT（python-jose）+ bcrypt 密码哈希 |

依赖清单：后端 `backend/requirements.txt`，前端 `frontend/package.json`，小程序 `weapp/package.json`。

---

## 2. 目录结构

```
C:\Users\DZY\Desktop\后台管理系统\
├─ backend\
│  ├─ app\
│  │  ├─ main.py            # FastAPI 入口，注册全部路由、CORS、静态目录
│  │  ├─ config.py          # 配置（app_name / database_url / debug / wx_*）
│  │  ├─ database.py        # 引擎 / SessionLocal / get_db
│  │  ├─ security.py        # JWT、密码哈希、get_current_user / get_current_principal
│  │  ├─ seed_admin.py      # 初始化默认管理员 + 默认学科
│  │  ├─ models.py          # Organization / Payment / User / Student（UserRole 含 principal/sub_principal/teacher/platform/campus_head）
│  │  ├─ models_income.py   # FeeRecord / Invoice（收费）
│  │  ├─ models_learning.py # Score / Attendance / Homework / ClassPerformance
│  │  ├─ models_points.py   # PointRecord（积分）
│  │  ├─ models_subject.py  # Subject / StudentSubject（学科+课时）
│  │  ├─ models_campus.py   # Campus / CampusTransaction（校区 + 手工收支）
│  │  └─ routers\           # auth/students/income/learning/points/dashboard/subjects/profile/platform/campuses
│  └─ tortoise.db           # SQLite 数据库（已初始化）
├─ frontend\                # PC 管理端（Vue3 + Element Plus + ECharts）
│  └─ src\
│     ├─ views\             # 12 个页面（均已 UI 优化）
│     ├─ layouts\MainLayout.vue
│     ├─ stores\user.js / router\index.js / utils\request.js
│     └─ style.css          # 全局样式 + 数据直观化工具类（见 §12）
├─ weapp\                   # 微信小程序（uni-app）
│  └─ src\
│     ├─ pages\             # 14 个页面（均已 UI 优化）
│     ├─ App.vue            # 全局样式（统计卡/标签/进度条/横幅等工具类）
│     ├─ uni.scss           # 主题变量（teal #10b981）
│     ├─ manifest.json / pages.json
│     └─ utils\request.js   # BASE_URL 默认 http://127.0.0.1:8000
├─ .ssh\                    # 本地 SSH 密钥（已被 .git/info/exclude 排除，不入库）
├─ .tmp\UI_GUIDE.md         # 三端 UI 设计规范（也已被排除，不入库）
├─ Dockerfile               # 完整系统镜像（PC 前端 + 后端同容器，多阶段构建）
├─ .dockerignore
├─ start.bat                # 一键启动脚本
└─ project.md / README.md / .gitignore
```

---

## 3. 启动方式

### 后端（端口 8000）
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- 首次建表由 `main.py` 的 `Base.metadata.create_all` 自动完成；初始化管理员/学科：
  ```powershell
  .\.venv\Scripts\python.exe -m app.seed_admin
  ```

### 前端（端口 5173）
```powershell
cd frontend
npm run dev    # 或 npm.cmd run dev（若 npm 不在 PATH）
```

### 微信小程序（uni-app）
```powershell
cd weapp
npm run build:mp-weixin    # 产物在 weapp/dist/build/mp-weixin
```
然后微信开发者工具「导入项目」打开该目录（或见 §10 CLI 方式）。本地联调勾选「不校验合法域名」。

### ⚠️ 沙箱/特殊环境下的启动注意事项（agent 会话用）
- 系统 schannel TLS 在此环境失效 → **PowerShell/curl/winget 无法 HTTPS**；Node.js 与 Python（OpenSSL）正常。
- `pip install` 会被沙箱拦截写临时目录 → 需 `danger-full-access` 权限，或用系统 pip 直装 venv：
  ```powershell
  python -m pip --python .venv\Scripts\python.exe install -r requirements.txt
  ```
- Vite / uni 构建需要 spawn 子进程 → 同样需完整权限启动。
- git 的 SSH 必须用系统原生 ssh（见 §11-④）。

---

## 4. 账号与角色

| 角色 | 说明 | 默认账号 |
|------|------|----------|
| `platform` | 平台超级管理员（机构开户） | `admin / admin123` |
| `principal` | **总校长**（机构创始人）：平台开户时创建；操作范围=自己所在校区，可看全校各校区运营**只读总览**（资金/人员/学生等） | 由平台「机构开户」创建 |
| `sub_principal` | **校区负责人（校长管理号）**：由总校长在「校区管理」页开号；只能查看/操作本校区全部数据（学生/教师/收支/收入等） | 由总校长在校区管理页开号 |
| `campus_head` | 校区负责人（**旧角色**，与新 `sub_principal` 同一套权限逻辑，存量账号兼容，不迁移） | 存量数据 |
| `teacher`  | 教师（仅自己负责的学生） | 由总校长/校区负责人在「教师管理」创建 |

角色权限差异（重要）：
- **教师端**任何查询/操作只能访问 `teacher_id == 当前用户.id` 的学生，否则返回 403。
- **校区负责人**（sub_principal / campus_head）：数据范围=自己校区**全部**学生（非自己名下）；可管理本校区教师（新增教师固定为 teacher 角色）；可登记/查看本校区收支、看本校区收入；**不可**操作/查看其他校区数据（403）。
- **总校长**（principal）：归属校区后（`campus_id` 有值）操作范围=本校区（学生/教师/收支/收入均按本校区过滤）；未归属校区（存量）保持全校可操作；校区管理页始终可见**全部校区**概况与汇总行（只读总览），可设置校区、为各校区开/换/取消校长管理号。
- **新增教师账号固定为 `teacher` 角色**（`/auth/register` 只允许创建教师；总校长/校长管理号由平台/总校长另行开号）。
- 路由守卫：`/deleted-students` 仅总校长；`/platform` 仅平台管理员；`/income`、`/teachers`、`/subjects`（只读）、`/campuses` 对总校长+校区负责人开放。
- **学生归属与打卡**：总校长/校区负责人/教师的学生按负责教师（`teacher_id`）分开；**总校长和校区负责人也可以拥有自己的学生**（可被选为负责教师，`/auth/teachers` 含总校长；未归属校区的总校长可拥有任意校区学生）。打卡（`POST /learning/attendance`）各角色**只能给自己负责的学生**打卡，PC/小程序学生管理的打卡按钮仅对自己名下学生显示。

---

## 5. 核心业务规则（硬约束）

1. **打卡唯一性**：同一学生同一学科同一天只能打卡一次，重复返回 400「该学生今天已打卡，一天只能打卡一次」。
2. **教师数据隔离**：教师只能查看/操作自己负责的学生（JOIN Student 过滤 `teacher_id`）。
3. **校区负责人数据隔离**：校区负责人（sub_principal / 存量 campus_head）只能查看/操作**本校区**全部学生与数据（过滤 `campus_id == 当前用户.campus_id`），跨校区返回 403。
4. **总校长归属校区**：principal 设置 `campus_id` 后，操作范围自动限定本校区（学生/教师/收支/收入均按校区过滤）；未设置时保持全校（存量兼容）。校区管理页仍显示全校只读总览。
5. **课时收费**：一次性收完，按次核销，次数可跨学期使用直至用完。
6. **学生打卡核销**：打卡成功后，自动查找该生最早有剩余次数的收费记录，核销 1 次（`used_sessions + 1`）。
7. **学科课时**：学生-学科关联 `StudentSubject` 支持两种计费方式——
   - 按课时：`total_sessions` 有值，打卡时 `used_sessions + 1`，剩余 = total - used。
   - 按到期时间：`total_sessions` 为 NULL，配置 `duration_value` + `duration_unit`（天/月/年），到期日 = 该生第一次在该学科打卡的日期 + 时长。
8. **到期提醒**：Dashboard 提前 5 天（`FEE_REMIND_DAYS=5`）提醒收费到期/学科到期；机构账号提前 7 天（`REMIND_DAYS=7`）。
9. **学生删除**：软删除（`deleted=True`），保留收费历史；同时清除积分数据。
10. **收入权限**：教师角色不可见机构月收入——`dashboard.py` 对 `UserRole.TEACHER` 将 `month_income` 置 0；小程序工作台「本月收入」卡片 `v-if="!store.isTeacher"` 隐藏。校区负责人/总校长可见（本校区/归属校区口径）。
11. **新增教师固定为 teacher**：`/auth/register` 只允许 `role == "teacher"`；校区负责人（sub_principal）开号只能通过总校长在「校区管理」页操作（`POST /campuses/{id}/head`）。
12. **打卡权限分离（学生分开管理）**：总校长/校区负责人/教师的学生分开，各角色只能给自己负责的学生打卡（`POST /learning/attendance` 校验 `teacher_id == 当前用户.id`，否则 403「只能给自己负责的学生打卡」）；总校长和校区负责人也可以拥有自己的学生（可被选为负责教师），此时同样只能给名下学生打卡。成绩/作业/课堂表现仍按原角色数据范围（教师=自己负责；校区负责人/总校长=本校区）。

---

## 6. 数据库模型要点

- `StudentSubject`（`student_subjects` 表）：`student_id`、`subject_id`、`total_sessions`、`used_sessions`、`duration_value`、`duration_unit`、`expire_date`。
- `Student`：`school`、`enrollment_date`、`grade`、`status`、`points`、`deleted`。
- `Attendance`：`subject_id`（打卡学科）、`date`、`status`、`org_id`。
- 数据库加列需手动 `ALTER TABLE`（SQLite 无自动迁移）。

---

## 7. 前端页面与路由（均已 UI 优化，逻辑不变）

| 路由 | 页面 |
|------|------|
| `/login` | Login 登录 |
| `/dashboard` | 工作台：统计卡、收入趋势、学科分布、到期提醒 |
| `/students` | 学生列表（概览卡 + 课时剩余进度条 + 状态圆点） |
| `/student/:id` | 学生档案（指标条 + 成绩着色 + 课时进度） |
| `/income` | 收费管理（收支概览 + 到期标签 + 核销进度） |
| `/teachers` | 教师管理（统计卡 + 角色标签 + 状态圆点） |
| `/subjects` | 学科管理（统计卡 + 分类标签；校区负责人只读） |
| `/points` | 积分奖励（金银铜排行榜条 + 涨跌配色） |
| `/campuses` | 校区管理（总校长全校只读总览 + 校区设置/负责人开号；负责人仅本校区） |
| `/platform` | 机构开户管理（平台） |
| `/deleted-students` | 已删除学生（仅总校长，概览 + 语义化列表） |
| `/student-attendance` | 全体学生考勤日历（工作台「进入日历」入口；按学生×日期查看月度打卡，行内可打卡） |

---

## 8. 近期改动记录

- **2026-08-16 · 完整系统 Dockerfile（PC 前端 + 后端一体化镜像）**：
  - 根目录新增 `Dockerfile`（多阶段：node:22-alpine 构建前端 → python:3.14-slim 运行后端）与 `.dockerignore`；
  - 后端新增 `FRONTEND_DIST` 配置：设置后由 FastAPI 同端口托管 PC 前端构建产物（`/assets` 静态资源 + 其余路径兜底返回 `index.html`，支持 history 路由；`/api`、`/static`、`/docs` 优先匹配）；
  - 镜像默认 `DATABASE_URL=sqlite:////data/tortoise.db`（挂载卷持久化），启动时幂等执行 `seed_admin` 初始化管理员与默认学科；健康检查 `/health`；
  - 部署说明见 `DEPLOY_CLOUD.md` §四；微信云托管仍使用 `backend/Dockerfile`。
- **2026-08-16 · 教师上下班打卡 + 全体学生考勤日历 + 学生打卡权限分离**：
  - **教师上下班打卡**：新增 `TeacherAttendance` 表与 `users.work_start_time/work_end_time` 字段（启动 `_ensure_schema` 自动建表/加列，`migrate.py` 同步）；教师在 PC/小程序工作台进行上班/下班打卡（`POST /learning/teacher-attendance`）；校区负责人在教师管理页设置上下班时间（PC「上下班」按钮 / 小程序教师列表「上下班」入口，`PUT /auth/users/{id}/work-time`）；月度考勤汇总（`GET /dashboard/attendance-summary`）按排班工作日计算，未打卡标记「缺勤」、晚于上班标记「迟到」、早于下班标记「早退」，校区负责人查看本校区教师汇总、教师查看自己汇总、总校长不展示。
  - **全体学生考勤日历**：后端 `GET /dashboard/attendance-summary?month=YYYY-MM` 返回学生×日期考勤明细；PC 工作台新增「本月学生考勤（日历）」卡片（`给学生打卡` 对话框 + `进入日历`）+ 独立页 `/student-attendance`；小程序工作台新增「📅 查看日历」入口 + 注册 `pages/student/attendance` 全体学生考勤日历页（每行一名学生、每列一天、彩色圆点标记 正常/迟到/缺勤/请假/早退/未记录），学生列表「考勤」按钮也可进入。
  - **学生分开管理（打卡权限分离）**：总校长/校区负责人/教师的学生按负责教师（`teacher_id`）分开；总校长和校区负责人也可以拥有自己的学生（`/auth/teachers` 增加总校长可选为负责教师；`students.py` 同校区校验放宽：负责教师未归属校区时不受限）。**打卡接口只允许给自己负责的学生打卡**（`learning.py` 新增 `_check_student_own`，`POST /learning/attendance` 校验 `teacher_id == 当前用户`），PC 学生列表/档案、小程序学生列表/详情中的打卡按钮仅对自己负责的学生显示。
  - 小程序登录 `weapp/src/utils/openid.js` 增加 2 秒超时兜底（开发者工具 `uni.login` 不回调时不再卡死）。
- **2026-08-16 · 平台超级管理员 PC/小程序界面一致**：
  - 小程序新增「机构开户管理」页（`weapp/src/pages/platform/platform.vue`，对应 PC `/platform`）：机构列表（校长账号/计费/交费金额/到期状态/启停用/编辑/续费/流水/重置密码）+ 开户流水统计（总金额/按机构汇总/待收款·已到期），全部复用后端 `/api/platform/*` 接口。
  - admin 在小程序登录后 `uni.reLaunch` **直达**机构开户管理页（隐藏 工作台/学生/我的 tab），与 PC 端一致；平台页底部提供退出登录。
  - `weapp/src/pages.json` 注册 `pages/platform/platform`；mine.vue 平台角色显示「机构开户管理」入口；dashboard/学生列表对平台角色做了引导兜底。
- **2026-08-16 · 平台超级管理员机构运营总览**：
  - 后端 `platform.py` 新增 `_org_overview`（本月收支/待缴/学生/在读/教师/今日打卡），机构列表响应带 `overview`；新增 `GET /api/platform/overview` 全机构汇总。
  - PC `PlatformManage.vue` 增加全机构运营统计卡（学生/教师/本月收入/待缴）+ 表格运营列；小程序 platform 页机构卡片增加「运营情况」区块，工作台平台视图增加运营汇总卡。
  - 真实 AppID `wxf8b95700bdb6a877` 已写入 `weapp/src/manifest.json`，小程序已构建并**上传体验版 v1.0.0**（274.5KB）。
  - ⚠️ 部署状态：**云托管后端未部署**（需在云开发控制台建环境+云托管服务，从 GitHub 仓库构建 `backend/Dockerfile`；`backend/.env` 未配置 WX_SECRET，真实登录需在云托管环境变量配置 `WX_APPID`/`WX_SECRET`；部署后把云托管域名填入 `weapp/src/utils/request.js` BASE_URL 并重新构建上传）。详见 `DEPLOY_CLOUD.md`。
- **2026-08-16 · 角色体系梳理（总校长端 / 校长管理号）**：
  - 新增角色 `sub_principal`（校区负责人·校长管理号）：由总校长在「校区管理」页开号（`POST /campuses/{id}/head` 新建账号或指定教师，角色改为 `SUB_PRINCIPAL`）；权限与旧 `campus_head` 完全一致（存量 campus_head 账号兼容，零迁移）。
  - **总校长（principal）数据范围**：归属校区后（`campus_id` 有值）学生/教师/收支/收入操作均限本校区；未归属（存量）保持全校；校区管理页始终可见全校各校区概况+汇总行（只读总览）。
  - **校区负责人数据范围**：从「等同教师（仅自己负责学生）」改为「本校区全部学生」，各 router（students/learning/income/points/dashboard/subjects/campuses）统一用 `is_head_role()` + `_scope_*` 过滤；跨校区访问 403。
  - **新增教师不再有校长角色**：`/auth/register` 只允许 `role == "teacher"`；PC 端「新增教师账号」表单移除「校长（管理员）」选项；校区负责人开号统一走校区管理页。
  - 前端：`userStore` 新增 `isSubPrincipal`；路由/菜单对 `sub_principal` 开放（income/teachers/subjects 只读/campuses）；角色文案统一为「总校长 / 校长管理号 / 教师」；PC 端与小程序端同步。
  - 后端冒烟测试通过：平台开户→总校长→开校长管理号→数据隔离（跨校区 403）→归属校区后操作限本校区。
- **校区管理功能（校长 + 校区负责人）**：
  - 新增 `Campus`（校区）与 `CampusTransaction`（手工收支）模型；`Student`/`User` 增加 `campus_id`（可选归属，历史数据为"未分校区"）。
  - 新增角色 `campus_head`（校区负责人）：只能登记/查看自己校区的收支；学生数据权限等同教师。**可进行教师管理**（仅限本校区：列表/新建/编辑/停用/删除/重置密码，新教师自动归属本校区）。
  - 校长可设置校区（名称/地址/电话/备注/停用）。**校区负责人由总校长手动编辑**：设置负责人时可「手动新建账号」（姓名/登录账号/密码/电话一键创建）或「从现有教师中选择」，支持随时更换/取消（原负责人自动降为教师）。
  - **总校长可查看各校区情况**：校区管理页每校区卡片显示资金（本月收入/支出/结余/待缴）、学生数、教师数、今日打卡；卡片上的"学生/教师"可点击直达对应校区筛选列表；学生管理/教师管理页新增"按校区筛选"（校区负责人自动限定本校区）。
  - 收支口径：学费收入按缴费学生所属校区自动归属；手工登记非学费收入（餐费/杂费/其他）与支出（房租/工资/水电/其他）；本月口径 + 全机构汇总行 + "未分校区"分组。
  - 接口：`/api/campuses`（列表/概况/CRUD）、`/api/campuses/{id}/head`、`/api/campuses/transactions`（登记/明细/删除）、`/api/campuses/options`（下拉）。
  - 前端：PC 新增"校区管理"页（`/campuses`，校长+负责人可见）；小程序新增校区页与收支明细页；学生/教师表单支持选择校区。
  - 数据库迁移：`backend/migrate.py` 已加 `students.campus_id`、`users.campus_id` 两列（SQLite 手动 ALTER）。
- **2026-08-15 · 三端 UI 全面优化**：PC 10 页 + 小程序 10 页；统计卡片+数字高亮、状态标签+颜色语义化、进度条（课时/分期/积分占比）、提醒横幅、排行榜条、空状态优化；teal 主题统一；**仅展示层，逻辑/后端 0 改动**（详见 §12）。
- 学生新增表单支持「学校信息」「课时数」「时长（天/月/年）」。
- 学生档案「课时核销情况」进度条；非核销课时学科显示到期时间与状态标签。
- 学生列表「托管班」列 → 「入学时间」列。
- 微信小程序完成真实登录联调、与 PC 数据互通、考勤核销一致性验证。
- 教师角色工作台不显示机构月收入（后端置 0 + 前端 v-if 双保险）。

---

## 9. 开发注意事项

- 改字段需同步：模型 → 路由 Pydantic → 前端表单 → 前端展示。
- 前端请求统一走 `@/utils/request`（自动带 token、统一错误提示）。
- 角色判断用 `userStore.isPrincipal / isSubPrincipal / isTeacher / isPlatform`（校区负责人新旧角色统一走 `isSubPrincipal`，后端对应 `is_head_role()`）。
- **UI 改动遵循 `C:\Users\DZY\Desktop\后台管理系统\.tmp\UI_GUIDE.md` 设计规范**（含全局工具类清单），PC 端工具类在 `frontend/src/style.css`，小程序端在 `weapp/src/App.vue` 全局样式 + `uni.scss` 主题变量。
- 新增展示型统计/格式化：只加纯展示 computed/helper，不动请求逻辑（本次优化全部遵循此原则）。

---

## 10. 微信小程序（weapp/）

| 项 | 说明 |
|----|------|
| 框架 | uni-app（Vue3 + Vite + Pinia） |
| 登录 | 微信授权 + 账号密码绑定：`User.wx_openid`；接口 `POST /api/auth/wx-bind`（绑定）、`POST /api/auth/wx-login`（静默） |
| 凭证 | `backend/.env` 的 `WX_APPID`/`WX_SECRET`；未配置时退化为本地模拟（code 当 openid） |
| BASE_URL | `weapp/src/utils/request.js`，默认 `http://127.0.0.1:8000` |
| AppID | 测试号 `wxb50df87e7a46f2c6`（`weapp/src/manifest.json`） |
| 编译 | `npm run build:mp-weixin`，产物 `weapp/dist/build/mp-weixin` |
| **开发者工具（实际安装位置，注意是 E 盘）** | `E:\微信小程序开发工具\微信web开发者工具\cli.bat`（旧文档写的 D:\ 有误） |
| CLI 导入命令（已验证可行） | `& "E:\微信小程序开发工具\微信web开发者工具\cli.bat" open --project "C:\Users\DZY\Desktop\后台管理系统\weapp\dist\build\mp-weixin"` |

> 说明：`admin` 为平台账号（无机构 ID），看不到机构学生数据；小程序应使用总校长/校长管理号/教师账号登录绑定。

---

## 11. 环境问题与解决方案汇总（重点 · 下次遇到直接对照）

### ① Git 安装与 winget
- 现象：系统无 git；`winget install Git.Git` 无输出退出码 1（winget 自身 HTTPS 走 schannel 失败）。
- 方案：用 Node.js（OpenSSL）从 GitHub Releases 下载 MinGit 便携版解压使用；后用户手动安装 Git 到 `E:\Git安装\Git`。
- 注意：`E:\Git安装` 目录在会话中曾凭空消失（PATH 仍在但目录没了），重新安装后恢复——疑似环境隔离/安装未完成，若再遇到 `git` 找不到，检查该目录是否存在。

### ② 网络环境
- 现象：PowerShell/.NET/curl 的 HTTPS 全部失败（schannel `SEC_E_NO_CREDENTIALS`）；`http://` 正常。
- 结论：**系统级 TLS（schannel）在此环境不可用，Node.js / Python（OpenSSL）的 HTTPS 正常**。
- 网络白名单：`api.github.com`、`codeload.github.com` 稳定可达；`github.com` 间歇性超时（20.205.243.166）；`objects.githubusercontent.com` 仅 `185.199.110.133` 一个 IP 可达。
- 下载方案：Node 自定义 `lookup`（DNS 劫持到可达 IP）+ 重试（github.com 时好时坏）。
- PyPI / npm registry 均可达。

### ③ 沙箱文件限制
- 临时目录每次调用轮换（`%TEMP%\dsh-XXXX`），**大文件不跨调用保留** → 下载+解压要在单次调用内完成，或写入工作区（持久）。
- `pip install` 写临时目录被拒 → 需 `danger-full-access` 权限（会弹用户授权），或用系统 pip `--python` 选项直装 venv。
- Vite dev / uni build 启动时 `spawn EPERM`（Node 子进程管道限制）→ 需 `danger-full-access` 启动。
- venv 创建成功但 `ensurepip` 失败（pip 写 temp 被拒）→ 用 `python -m pip --python .venv\Scripts\python.exe install -r requirements.txt`（pip 26+ 支持 `--python`，须放在子命令前）。
- 编辑文件时 Vite 文件监听可能因编辑工具临时文件锁 EBUSY 崩溃 → `frontend/vite.config.js` 已加 `server.watch.ignored`（忽略 `.??*`、`*.tmp` 等），勿删。

### ④ Git + SSH（私有仓库）
- Git for Windows 自带 Cygwin `ssh.exe`/`sh.exe` 无法创建信号管道（Win32 error 5）→ 直接 clone/fetch 会失败。
- 系统原生 ssh（`C:\Windows\System32\OpenSSH\ssh.exe`）正常，但无参数时按 `%USERPROFILE%\.ssh` 找密钥（不会用 `HOME`），且会卡在交互提示。
- 解决方案（已验证）：`C:\Users\DZY\Desktop\后台管理系统\.ssh\git-ssh.cmd` 包装脚本：
  ```
  @echo off
  "C:\Windows\System32\OpenSSH\ssh.exe" -i "%~dp0id_ed25519" -o StrictHostKeyChecking=no -o UserKnownHostsFile="%~dp0known_hosts" -o BatchMode=yes -o ConnectTimeout=20 %*
  ```
  使用：`$env:GIT_SSH = "C:\Users\DZY\Desktop\后台管理系统\.ssh\git-ssh.cmd"`（git 直接 exec .cmd，不走 sh）。
  仓库本地已配 `core.sshCommand`（正常终端可用）；`%USERPROFILE%\.ssh` 目录不存在（沙箱拒写用户目录），密钥放工作区 `.ssh\`（已 .git/info/exclude 排除）。
- 私钥无密码（ed25519）；公钥已添加到 GitHub 账号 Mr-Simple1998。

### ⑤ 其他
- 系统 Python 仅 3.14；requirements 各包均有 cp314 wheel，可正常安装（bcrypt 5.0.0 / pydantic-core 等 OK）。
- npm 11 的 allow-scripts：core-js/esbuild/vue-demi 的 postinstall 未执行（仅警告），esbuild 二进制走 optionalDependencies，**不影响构建**。
- `.ssh/`、`.git-tools/`、`.tmp/`、`.pip-cache/`、`.npm-cache/`、`.pipwork-*/` 已加入 `.git/info/exclude`，不入库、不影响 git status。

---

## 12. 三端 UI 优化说明（2026-08-15）

### 设计规范
- 主文档：`C:\Users\DZY\Desktop\后台管理系统\.tmp\UI_GUIDE.md`（工具类清单 + 展示模式 + 铁律：不改逻辑）。
- PC 端全局工具类：`frontend/src/style.css` 末尾「数据直观化工具类」区块：
  `.mini-stats/.mini-stat`、`.mini-progress(.mp-track/.mp-bar/.mp-text)`、`.status-dot`、`.amount`、`.trend`、`.kv-row`、`.banner.is-*`、`.info-row`、`.rank-row/.rank-badge(.is-top1/2/3)`、`.section-title`、`.card-grid`、`.empty-hint`、`.num-strong` 等。
- 小程序端全局工具类：`weapp/src/App.vue` 全局 `<style>`：
  `.stat-card(.is-blue/green/orange/red/purple)`、`.stat-grid`、`.tag(.tag-success/danger/warn/info/primary/grey/plain)`、`.dot(.dot-*)`、`.progress(.is-warn/danger/info)`、`.banner.is-*`、`.kv-row`、`.info-row`、`.rank-row/.rank-badge(.top1/2/3)`、`.amount(.income)`、`.empty`、`.section-title`、`.divider` 等；主题变量在 `uni.scss`（teal）。

### 各页优化要点（逻辑零改动）
- **PC**：学生列表（概览卡+课时剩余进度条+状态圆点）、学生档案（指标条+成绩按得分率着色）、收费管理（收支概览+到期标签+核销/分期进度）、机构开户（teal 统一+金额配色）、登录/学科/教师/积分/已删除学生（统计卡+排行榜条+状态标签+空状态）。
- **小程序**：工作台（彩色统计卡+到期横幅+标签提醒）、学生三页（概览卡+课时进度+到期横幅）、收费（欠费横幅+次数进度）、积分（排行榜条+涨绿跌红）、教师/学科/登录/我的（信息行+角色标签+卡片网格+视觉升级）。

### 验证方式（本次用过，可复用）
- PC 页面编译：Vite 按需编译 `http://localhost:5173/src/views/<Page>.vue` 返回 200。
- 小程序页面校验：用 `frontend/node_modules/@vue/compiler-sfc` 对 weapp 页面做 parse + compileScript + compileTemplate。
- 逻辑零改动核对：`git diff backend/` 为空；`git status --short` 只应有 UI 文件。

---

## 13. 校区负责人多选 + 离职交接功能（2026-08-16）

本次新增三项核心功能（后端 + PC + 小程序三端同步）：

### ① 校区负责人多选（选项含总校长）
- 新表 `campus_heads`（campus_id + user_id 关联）：一个校区可有多名负责人。
- `POST /api/campuses/{id}/head`：`user_ids` 多选（替换语义）；可同时传 username/password/name 新建账号并加入。
- 候选接口 `GET /api/campuses/head-candidates`：本机构全部账号（含总校长 principal、其他校区负责人、教师），离职/停用账号前端置灰。
- 权限升级：`security.managed_campus_ids(db, user)` 返回用户可管辖校区集合（users.campus_id ∪ campus_heads），总校长返回 None。students/income/learning/points/dashboard/subjects/campuses/auth 全部按该集合做多校区范围过滤。
- 存量兼容：启动时 `main._ensure_schema()` 自动建表/加列并把存量单负责人回填到 campus_heads（migrate.py 同步支持）。

### ② 校区负责人离职 → 数据保留 + 重新建号迁移
- `POST /api/campuses/{id}/head/resign`：账号停用并标记 `resigned`，移除负责人关联（不再担任任何校区则降级为教师）；校区全部数据（学生/教师/收支/收费记录）原样保留；负责人名下直接负责的学生 teacher_id 置空暂存校区。
- 重新建号 = 负责人对话框「同时新建账号」或教师管理页新建账号后指定，新负责人登录即自动接管校区全部数据（数据按 campus_id 归属，天然交接）。

### ③ 教师离职 → 学生暂存校区负责人 → 再分配
- `POST /api/auth/users/{id}/resign`：教师账号停用标记离职；名下学生 teacher_id 置空（未分校区学生自动归入教师所属校区），数据全部保留。
- `POST /api/students/assign`：总校长/校区负责人批量把暂存学生分配给其他教师（或置空=暂存回校区负责人），跨校区批量会拦截。
- 学生编辑（PC 列表弹窗 / 小程序详情页「更换教师」）支持选择负责教师，列表端“暂存校区”黄色标签提示。
- `users.resigned` / `users.resigned_at` 字段；`update_user is_active=true` 重新启用时自动清除离职标记。

### 约定
- 总校长（principal）不可办理离职；平台管理员不可设为负责人。
- 校区删除仍受保护（有学生/教师/收支时禁止删除，需先停用或转移）。
- 测试方式：后端可直接调用路由函数做冒烟测试（无 httpx 时绕过 TestClient）；Vite/uni 构建需 `danger-full-access`（spawn EPERM 见 §11③）。
