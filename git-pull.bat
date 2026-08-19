@echo off
setlocal

REM ============================================
REM   一键从 GitHub 拉取最新代码
REM   用法：双击运行；更新本地到远程最新版本
REM ============================================

set "ROOT=%~dp0"
set "GIT_SSH_COMMAND="C:\Windows\System32\OpenSSH\ssh.exe" -i "%ROOT%.ssh\id_ed25519" -o StrictHostKeyChecking=no -o UserKnownHostsFile="%ROOT%.ssh\known_hosts" -o BatchMode=yes -o ConnectTimeout=25"

cd /d "%ROOT%"

echo ============================================
echo   一键从 GitHub 拉取最新代码
echo ============================================

echo [1/2] 连接 GitHub 并拉取...
git fetch origin
if errorlevel 1 (
    echo [错误] 连接 GitHub 失败，请检查网络或 .ssh 密钥。
    pause
    exit /b 1
)

echo [2/2] 更新本地分支...
git merge --ff-only origin/main
if errorlevel 1 (
    echo [提示] 更新失败，可能原因：
    echo   1. 本地有未推送的提交 -^> 先双击 git-push.bat 推送后再拉取
    echo   2. 本地有未提交的改动 -^> 先提交，或用 git status 查看
    echo   3. 远程与本地各自有新提交 -^> 需要手动解决冲突
    echo 查看详情：git status / git log --oneline -5
    pause
    exit /b 1
)

echo.
echo 更新完成！当前版本：
git log --oneline -3
pause
