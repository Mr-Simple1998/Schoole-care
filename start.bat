@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo   教学机构校长后台管理系统 - 一键启动
echo ============================================
echo.

REM ---- 自动把 Python / Node 常见安装目录临时加入 PATH ----
REM 这样即使没有加入系统 PATH，也能直接在脚本里调用 python / npm
set "PATH=D:\dev\python;D:\dev\python\Scripts;C:\Program Files\nodejs;%PATH%"
if exist "%LOCALAPPDATA%\Programs\Python\" (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do set "PATH=%%i;%%i\Scripts;!PATH!"
)
if exist "C:\Python*" (
    for /d %%i in ("C:\Python*") do set "PATH=%%i;%%i\Scripts;!PATH!"
)

REM ---- 检查 python 是否可用 ----
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 并勾选 "Add to PATH"，然后重新运行。
    echo        官方网站: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ---- 检查 npm 是否可用 ----
where npm >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Node.js/npm，请先安装 Node.js LTS，然后重新运行。
    echo        官方网站: https://nodejs.org/zh-cn
    pause
    exit /b 1
)

set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend

REM 检查后端环境
if not exist "%BACKEND%\.venv\Scripts\python.exe" (
    echo [1/3] 首次运行，正在创建后端虚拟环境...
    cd /d "%BACKEND%"
    python -m venv .venv
    "%BACKEND%\.venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    echo [1/3] 后端虚拟环境已存在
)

REM 初始化数据库（创建默认校长账号 admin/admin123）
echo [2/3] 初始化数据库...
cd /d "%BACKEND%"
"%BACKEND%\.venv\Scripts\python.exe" -m app.seed_admin

REM 检查前端依赖
if not exist "%FRONTEND%\node_modules" (
    echo [3/3] 首次运行，正在安装前端依赖...
    cd /d "%FRONTEND%"
    call npm install
) else (
    echo [3/3] 前端依赖已存在
)

echo.
echo 启动服务中，请稍候...
echo 后端: http://127.0.0.1:8000  (API 文档 /docs)
echo 前端: http://localhost:5173   (系统界面)
echo 默认校长账号: admin / admin123
echo.
echo 关闭本窗口将停止服务。
echo ============================================

REM 启动后端
start "后端服务" cmd /k "cd /d %BACKEND% && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM 启动前端
start "前端服务" cmd /k "cd /d %FRONTEND% && npm run dev"

echo 服务已启动！请用浏览器打开 http://localhost:5173
pause