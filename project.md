# 机构后台学习管理系统 — 项目说明

> 后端托管的机构后台管理系统，含平台开户、校长/教师双端、学生档案、收费核销、积分、考勤等功能。
> 本文件用于快速了解项目架构与开发约定，避免下次更新时重新扫描全项目。

---

## 1. 技术栈

| 端 | 技术 |
|----|------|
| 后端 | Python 3.12 + FastAPI 0.141 + SQLAlchemy 2.0 + Pydantic 2 + SQLite |
| 前端 | Vue 3.5 + Vite 8 + Element Plus 2.14 + Pinia + Vue Router 4 + ECharts |
| 认证 | JWT（python-jose）+ bcrypt 密码哈希 |
| 数据库 | SQL 文件：`backend/tortoise.db`（默认，见 `config.py`） |

依赖清单：后端 `backend/requirements.txt`，前端 `frontend/package.json`。

---

## 2. 目录结构

```
d:\AI项目\机构后台管理系统\
├─ backend\
│  ├─ app\
│  │  ├─ main.py            # FastAPI 入口，注册全部路由、CORS、静态目录
│  │  ├─ config.py          # 配置（app_name / database_url / debug）
│  │  ├─ database.py        # 引擎 / SessionLocal / get_db
│  │  ├─ security.py        # JWT、密码哈希、get_current_user / get_current_principal
│  │  ├─ seed_admin.py      # 初始化默认管理员 + 默认学科
│  │  ├─ models.py          # Organization / Payment / User / Student
│  │  ├─ models_income.py   # FeeRecord / Invoice（收费）
│  │  ├─ models_learning.py # Score / Attendance / Homework / ClassPerformance
│  │  ├─ models_points.py   # PointRecord（积分）
│  │  ├─ models_subject.py  # Subject / StudentSubject（学科+课时）
│  │  └─ routers\
│  │     ├─ auth.py         # /api/auth   登录、当前用户
│  │     ├─ students.py     # /api/students  学生 CRUD + 学科课时
│  │     ├─ income.py       # /api/income   收费管理
│  │     ├─ learning.py     # /api/learning 成绩/考勤/作业/课堂表现
│  │     ├─ points.py       # /api/points   积分
│  │     ├─ dashboard.py    # /api/dashboard 工作台统计+到期提醒
│  │     ├─ subjects.py     # /api/subjects  学科管理
│  │     ├─ profile.py      # /api/profile   个人资料
│  │     └─ platform.py     # /api/platform  平台开户管理
│  └─ tortoise.db           # SQLite 数据库
└─ frontend\
   └─ src\
      ├─ main.js / App.vue / style.css
      ├─ router\index.js    # 路由 + 登录/角色守卫
      ├─ stores\user.js     # Pinia 用户状态（token/user/角色判断）
      ├─ utils\request.js   # axios 封装（token 注入 + 401/403 处理）
      ├─ layouts\MainLayout.vue
      ├─ components\ProfileDialog.vue
      └─ views\
         ├─ Login.vue / Dashboard.vue / PlatformManage.vue
         ├─ StudentList.vue / StudentDetail.vue
         ├─ IncomeManage.vue / TeacherManage.vue
         ├─ SubjectManage.vue / PointsSystem.vue
```

---

## 3. 启动方式

### 后端（端口 8000）
```powershell
cd d:\AI项目\机构后台管理系统\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
首次建表由 `main.py` 的 `Base.metadata.create_all` 自动完成；初始化管理员/学科：
```powershell
.\.venv\Scripts\python.exe -m app.seed_admin
```

### 前端（端口 5173）
```powershell
cd d:\AI项目\机构后台管理系统\frontend
$env:Path = 'C:\Program Files\nodejs;' + $env:Path
& 'C:\Program Files\nodejs\npm.cmd' run dev
```
> 注意：`npm` 可能不在 PATH，需用完整路径 `C:\Program Files\nodejs\npm.cmd` 启动。

### 微信小程序（uni-app，端口无关，导出到微信开发者工具）
```powershell
cd d:\AI项目\机构后台管理系统\weapp
$env:Path = 'C:\Program Files\nodejs;' + $env:Path
& 'C:\Program Files\nodejs\npm.cmd' run build:mp-weixin   # 或 dev:mp-weixin
```
构建产物在 `weapp/dist/build/mp-weixin`（dev 在 `dist/dev/mp-weixin`）。用微信开发者工具「导入项目」打开该目录即可运行；本地联调需勾选「不校验合法域名」。后端地址在小程序 `weapp/src/utils/request.js` 的 `BASE_URL`（默认 `http://127.0.0.1:8000`）。

---

## 4. 账号与角色

| 角色 | 说明 | 默认账号 |
|------|------|----------|
| `platform` | 平台超级管理员（机构开户） | `admin / admin123` |
| `principal` | 校长/管理员（本机构全部数据） | 测试：`principal1` |
| `teacher`  | 教师（仅自己负责的学生） | 测试：`teacher` |

角色权限差异（重要）：
- 教师端任何查询/操作只能访问 `teacher_id == 当前用户.id` 的学生，否则返回 403。
- 校长端按 `org_id` 过滤，可看机构全部学生。
- 路由守卫：`/teachers`、`/subjects`、`/income` 仅校长；`/platform` 仅平台管理员。

---

## 5. 核心业务规则（硬约束）

1. **打卡唯一性**：同一学生同一学科同一天只能打卡一次，重复返回 400「该学生今天已打卡，一天只能打卡一次」。
2. **教师数据隔离**：教师只能查看/操作自己负责的学生（JOIN Student 过滤 `teacher_id`）。
3. **课时收费**：一次性收完，按次核销，次数可跨学期使用直至用完。
4. **学生打卡核销**：打卡成功后，自动查找该生最早有剩余次数的收费记录，核销 1 次（`used_sessions + 1`）。
5. **学科课时（新增）**：学生-学科关联 `StudentSubject` 支持两种计费方式——
   - 按课时：`total_sessions` 有值，打卡时 `used_sessions + 1`，剩余 = total - used。
   - 按到期时间：`total_sessions` 为 NULL，配置 `duration_value`（数值）+ `duration_unit`（天/月/年），**到期日 = 该生第一次在该学科打卡的日期 + 时长**，首次打卡时自动计算并写入 `expire_date`。
6. **到期提醒**：Dashboard 提前 5 天（`FEE_REMIND_DAYS=5`）提醒收费到期 / 学科到期；机构账号提前 7 天（`REMIND_DAYS=7`）。
7. **学生删除**：软删除（`deleted=True`），保留收费历史；同时清除积分数据。
8. **收入权限**：教师角色不可见机构月收入——`dashboard.py` 对 `UserRole.TEACHER` 将 `month_income` 置 0；小程序工作台「本月收入」卡片 `v-if="!store.isTeacher"` 隐藏。校长/平台正常可见。

---

## 6. 数据库模型要点

- `StudentSubject`（`student_subjects` 表）字段：`student_id`、`subject_id`、`total_sessions`、`used_sessions`、`duration_value`、`duration_unit`、`expire_date`。
- `Student`：含 `school`（学校）、`enrollment_date`（入学日期）、`grade`、`status`、`points`、`deleted`。
- `Attendance`：含 `subject_id`（打卡学科）、`date`、`status`、`org_id`。
- 学生列表页已移除「托管班」列，改为显示「入学时间」。

---

## 7. 前端页面与路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/login` | Login | 登录 |
| `/dashboard` | Dashboard | 工作台：统计卡片、收入趋势、学科分布、缴费/到期提醒 |
| `/students` | StudentList | 学生管理（新增含学校+学科课时/时长配置） |
| `/student/:id` | StudentDetail | 学习档案：成绩、考勤（含课时核销概览+到期时间）、作业、课堂表现 |
| `/income` | IncomeManage | 收费管理（校长） |
| `/teachers` | TeacherManage | 教师管理（校长） |
| `/subjects` | SubjectManage | 学科管理（校长） |
| `/points` | PointsSystem | 积分奖励 |
| `/platform` | PlatformManage | 机构开户管理（平台） |

---

## 8. 近期改动记录

- 学生新增表单支持「学校信息」「课时数」「时长（天/月/年）」。
- 学生列表「托管班」列 → 替换为「入学时间」列；年级列加宽且不换行。
- 学生档案新增「课时核销情况」概览（进度条），不按课时的学科显示到期时间及状态标签。
- 非核销课时学科到期日：首次打卡当日 + 时长自动计算（天/月/年）。
- Dashboard 新增学科到期提醒（提前 5 天）。
- 全局 UI 采用 teal 主色 `#10b981`、圆角卡片、侧边栏、翻页/数字动画。
- 微信小程序成功导入微信开发者工具并完成真实登录流程联调（教师账号 `sun123`）。
- 已验证小程序与 PC 端数据互通（同一后端+数据库，读写双向一致）。
- 已验证考勤核销一致性（打卡 → 数据库 `used_sessions+1` → PC 端档案接口一致）。
- 教师角色工作台不再显示机构月收入（后端置 0 + 前端 `v-if` 双保险）。

---

## 9. 开发注意事项

- 改字段需同步：模型（`models_subject.py` 等）→ 路由 Pydantic（`students.py`）→ 前端表单（`StudentList.vue`）→ 前端展示（`StudentDetail.vue`）。
- 数据库加列需手动执行 `ALTER TABLE`（SQLite 无自动迁移），参考脚本在 `c:\Users\段兆洋\.trae-cn\work\6a7c14432bf02d93d676a576\migrate_*.py`。
- 前端请求统一走 `@/utils/request`（自动带 token、统一错误提示）。
- 角色判断用 `userStore.isPrincipal / isTeacher / isPlatform`。

## 10. 微信小程序（weapp/）

| 项 | 说明 |
|----|------|
| 框架 | uni-app（Vue3 + Vite + Pinia），目录 `weapp/` |
| 登录 | 微信授权 + 账号密码绑定：`User.wx_openid` 字段；接口 `POST /api/auth/wx-bind`（绑定）、`POST /api/auth/wx-login`（静默） |
| 数据互通 | 小程序与 PC 共用同一后端 API + 数据库，JWT 鉴权一致，天然互通 |
| 真实微信 | 凭证在 `backend/.env` 的 `WX_APPID`/`WX_SECRET`，`config.py` 读取；`auth.py::_wx_openid()` 调 `sns/jscode2session` 换真实 openid |
| 兜底 | `_wx_openid()` 在未配置凭证或微信返回错误码(40013/40125/40029)时，回退把 code 当 openid（本地模拟）；前端 `uni.login` 失败时用本地 `wx_dev_openid` 标识 |
| 页面 | 登录、工作台、学生列表/新增/档案、考勤打卡、成绩/作业/课堂、收费、积分、教师、学科、我的 |
| BASE_URL | `weapp/src/utils/request.js`，默认 `http://127.0.0.1:8000` |
| AppID | 测试号 `wxb50df87e7a46f2c6`（在 `weapp/src/manifest.json` 的 `mp-weixin.appid`） |
| 编译 | `npm run build:mp-weixin`，产物在 `weapp/dist/build/mp-weixin`，微信开发者工具导入运行 |
| 开发者工具 CLI | `D:\微信小程序开发工具\微信web开发者工具\cli.bat`；`open --project <路径>` 导入，`islogin` 查登录；需先开启开发者工具「设置→安全设置→服务端口」 |

> 说明：`admin` 为平台账号（无机构 ID），登录后看不到机构学生数据；小程序应使用校长 `principal*` / 教师账号登录绑定，才能看到各自机构/负责的学生，与 PC 端一致。