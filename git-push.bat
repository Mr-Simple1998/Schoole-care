@echo off
setlocal enabledelayedexpansion

REM ============================================
REM   一键推送代码到 GitHub
REM   用法：双击运行；自动 commit 未提交改动并 push
REM   用工作区 .ssh 密钥连接，无需手动配置 SSH
REM ============================================

set "ROOT=%~dp0"
set "GIT_SSH_COMMAND="C:\Windows\System32\OpenSSH\ssh.exe" -i "%ROOT%.ssh\id_ed25519" -o StrictHostKeyChecking=no -o UserKnownHostsFile="%ROOT%.ssh\known_hosts" -o BatchMode=yes -o ConnectTimeout=25"

cd /d "%ROOT%"

echo ============================================
echo   一键推送代码到 GitHub
echo ============================================

echo [1/4] 连接 GitHub 并拉取最新状态...
git fetch origin
if errorlevel 1 (
    echo [错误] 连接 GitHub 失败，请检查网络或 .ssh 密钥。
    pause
    exit /b 1
)

echo.
echo [2/4] 以下提交将推送到 GitHub：
git log --oneline origin/main..HEAD
if errorlevel 1 echo     （无待推送提交）

echo.
echo [3/4] 检查未提交的改动...
set "HAS=0"
for /f "delims=" %%i in ('git status --porcelain') do set HAS=1
if "!HAS!"=="1" (
    set /p MSG=请输入提交说明（直接回车用默认）: 
    if "!MSG!"=="" set "MSG=update %date% %time%"
    > "%TEMP%\dsh_git_msg.txt" echo !MSG!
    powershell -NoProfile -Command "$s=[IO.File]::ReadAllText($env:TEMP+'\dsh_git_msg.txt',[Text.Encoding]::GetEncoding(936));[IO.File]::WriteAllText($env:TEMP+'\dsh_git_msg_utf8.txt',$s,[Text.Encoding]::UTF8)"
    git add -A
    git commit -F "%TEMP%\dsh_git_msg_utf8.txt"
    del "%TEMP%\dsh_git_msg.txt" "%TEMP%\dsh_git_msg_utf8.txt" 2>nul
    if errorlevel 1 (
        echo [错误] 提交失败。
        pause
        exit /b 1
    )
) else (
    echo     没有未提交的改动，跳过 commit
)

echo.
echo [4/4] 推送到 GitHub...
git push origin main
if errorlevel 1 (
    echo [错误] 推送失败，请检查网络或密钥。
    pause
    exit /b 1
)
echo.
echo 推送成功！本地与 GitHub 已同步，代码不会丢失。
echo 当前版本：
git log --oneline -3
pause
