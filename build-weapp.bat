@echo off
chcp 65001 >nul
setlocal

REM ============================================
REM   小程序一键构建 + 自动打开微信开发者工具
REM   1) 重新编译 uni-app -> dist\build\mp-weixin
REM   2) 用开发者工具 CLI 打开正确的项目目录
REM ============================================

set "ROOT=%~dp0"
set "CLI=E:\微信小程序开发工具\微信web开发者工具\cli.bat"
set "TARGET=%ROOT%weapp\dist\build\mp-weixin"

REM ---- 临时把常见 Node 安装目录加入 PATH ----
if exist "%LOCALAPPDATA%\Programs\Node\" (
    for /d %%i in ("%LOCALAPPDATA%\Programs\Node\*") do set "PATH=%%i;!PATH!"
)
if exist "E:\Nod.js" set "PATH=E:\Nod.js;!PATH!"

where npm >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 npm，请先安装 Node.js 并勾选 "Add to PATH"。
    pause
    exit /b 1
)

echo ============================================
echo   小程序一键构建 + 打开开发者工具
echo ============================================

echo [1/2] 构建小程序（npm run build:mp-weixin）...
cd /d "%ROOT%weapp"
call npm run build:mp-weixin
if errorlevel 1 (
    echo [错误] 构建失败，请查看上方错误信息。
    pause
    exit /b 1
)
echo [1/2] 构建完成。

echo [2/2] 打开微信开发者工具...
if not exist "%CLI%" (
    echo [错误] 未找到开发者工具 CLI：%CLI%
    echo 请手动导入项目目录：
    echo     %TARGET%
    pause
    exit /b 1
)
call "%CLI%" open --project "%TARGET%"
if errorlevel 1 (
    echo [提示] 自动打开失败。
    echo   若提示未开启服务端口：开发者工具 -^> 设置 -^> 安全设置 -^> 开启"服务端口"，然后重跑本脚本。
    echo   也可以手动导入目录：
    echo       %TARGET%
    pause
    exit /b 1
)
echo [2/2] 已请求开发者工具打开项目，请稍候（若工具未运行会自动启动）。
echo.
echo 打开后请确认：AppID = wxb50df87e7a46f2c6
echo 首次使用请用 admin / admin123 点「登录并绑定微信」。
pause
