@echo off
chcp 65001 >nul
title 推文管理工具 - 安装并启动

echo ==============================
echo   推文管理工具 一键安装
echo ==============================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo [1/4] Python 已就绪

:: 创建工作目录
if not exist "%USERPROFILE%\tweet-manager" mkdir "%USERPROFILE%\tweet-manager"
cd /d "%USERPROFILE%\tweet-manager"

:: 下载 app.py
echo [2/4] 下载程序文件...
curl -fsSL "https://raw.githubusercontent.com/gongxianga/tweet-manager/main/app.py" -o app.py
if errorlevel 1 (
    echo [错误] 下载失败，请检查网络连接
    pause
    exit /b 1
)

:: 安装 Python 依赖
echo [3/4] 安装依赖...
pip install flask anthropic --quiet

:: 安装 xreach
echo [4/4] 安装 xreach...
xreach --version >nul 2>&1
if errorlevel 1 (
    pip install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
)

:: 创建桌面快捷方式（下次直接双击启动）
set SHORTCUT="%USERPROFILE%\Desktop\推文管理工具.bat"
echo @echo off > %SHORTCUT%
echo chcp 65001 ^>nul >> %SHORTCUT%
echo cd /d "%USERPROFILE%\tweet-manager" >> %SHORTCUT%
echo python app.py >> %SHORTCUT%
echo pause >> %SHORTCUT%
echo.
echo 桌面快捷方式已创建，下次直接双击桌面图标启动

echo.
echo ==============================
echo   安装完成，正在启动...
echo ==============================
echo.
echo 浏览器即将自动打开 http://localhost:8888
echo 关闭此窗口即可停止程序
echo.
python app.py
pause
