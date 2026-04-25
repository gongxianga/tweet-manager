#!/bin/bash
set -e

echo "=============================="
echo "  推文管理工具 一键安装"
echo "=============================="
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "正在安装 Python..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv python3-full
fi
echo "[1/4] Python 已就绪"

# 创建虚拟环境
echo "[2/4] 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
echo "[3/4] 安装依赖..."
pip install flask anthropic --quiet

# 安装 xreach
echo "[4/4] 安装 xreach..."
if ! command -v xreach &>/dev/null; then
    pip install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
fi

# 生成启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python3 app.py
EOF
chmod +x start.sh

echo ""
echo "=============================="
echo "  安装完成，正在启动..."
echo "=============================="
echo ""
echo "请在浏览器打开: http://localhost:8888"
echo "下次启动只需运行: bash start.sh"
echo "按 Ctrl+C 停止程序"
echo ""
python3 app.py
