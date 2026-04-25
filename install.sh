#!/bin/bash
set -e

echo "=============================="
echo "  推文管理工具 一键安装"
echo "=============================="
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 Python，正在安装..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip
fi
echo "[1/3] Python 已就绪"

# 安装 Python 依赖
echo "[2/3] 安装依赖..."
pip3 install flask anthropic --quiet

# 安装 xreach
echo "[3/3] 安装 xreach..."
if ! command -v xreach &>/dev/null; then
    pip3 install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
fi

echo ""
echo "=============================="
echo "  安装完成，正在启动..."
echo "=============================="
echo ""
echo "请在浏览器打开: http://localhost:8888"
echo "按 Ctrl+C 停止程序"
echo ""
python3 app.py
