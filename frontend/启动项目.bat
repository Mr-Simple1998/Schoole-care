@echo off
chcp 65001 >nul
title 机构后台管理系统 - 启动器
echo ============================================
echo   机构后台管理系统 一键启动器
echo ============================================
echo.

set "ROOT=%~dp0"

REM ---------- 检查后端依赖 ----------
echo [1/3] 检查后端依赖...
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
    echo   未找到后端正环境，请先执行: cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo   后端虚拟环境 OK

REM ---------- 检查前端依赖 ----------
echo [2/3] 检查前端依赖...
if not exist "%ROOT%frontend\node_modules" (
    echo   未找到前端依赖，正在安装，请稍候...
    pushd "%ROOT%frontend"
    call npm install
    popd
)
echo   前端依赖 OK

echo [3/3] 启动服务...
echo.

REM ---------- 启动后端 (uvicorn, 端口 8000) ----------
start "后端服务 :8000" cmd /k "cd /d "%ROOT%backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM ---------- 启动前端 (vite, 端口 5173) ----------
start "前端服务 :5173" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

echo.
echo 已启动，请打开浏览器访问:
echo   前端   http://localhost:5173
echo   后端   http://localhost:8000/docs
echo.
echo 默认账号: admin / admin123
echo 关闭请直接关闭弹出的两个命令行窗口。
echo.
pause