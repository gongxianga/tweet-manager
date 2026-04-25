@echo off
chcp 65001 >nul
title 推文管理工具

echo ==============================
echo   推文管理工具 启动中...
echo ==============================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安装依赖
echo [1/2] 安装依赖...
pip install flask anthropic --quiet

:: 安装 agent-reach（含 xreach）
echo [2/2] 检查 xreach...
xreach --version >nul 2>&1
if errorlevel 1 (
    echo 正在安装 agent-reach...
    pip install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
)

echo.
echo 启动成功！浏览器即将自动打开...
echo 如未自动打开，请手动访问: http://localhost:8888
echo 关闭此窗口即可停止程序
echo.
python app.py
pause
