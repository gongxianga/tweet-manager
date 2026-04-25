#!/bin/bash
echo "=============================="
echo "  推文管理工具 启动中..."
echo "=============================="
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 安装依赖
echo "[1/2] 安装依赖..."
pip3 install flask anthropic --quiet

# 检查并安装 xreach
echo "[2/2] 检查 xreach..."
if ! command -v xreach &>/dev/null; then
    echo "正在安装 agent-reach..."
    pip3 install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
fi

echo ""
echo "启动成功！浏览器即将自动打开..."
echo "如未自动打开，请手动访问: http://localhost:8888"
echo "按 Ctrl+C 停止程序"
echo ""
python3 app.py
