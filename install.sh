#!/bin/bash
set -e

echo "=============================="
echo "  推文管理工具 一键安装"
echo "=============================="
echo ""

# 1. 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "正在安装 Python..."
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv python3-full
fi
echo "[1/5] Python 已就绪"

# 2. 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate
pip install flask anthropic --quiet
echo "      依赖安装完成"

# 3. 安装 pipx
echo "[3/5] 安装 pipx..."
if ! command -v pipx &>/dev/null; then
    sudo apt-get install -y pipx -qq
fi
pipx ensurepath --force
export PATH="$PATH:$HOME/.local/bin"
echo "      pipx 已就绪"

# 4. 安装 agent-reach（含 xfetch）
echo "[4/5] 安装 xfetch..."
pipx install "https://mirror.ghproxy.com/https://github.com/Panniantong/agent-reach/archive/main.zip" --force
agent-reach install --env=auto --channels=twitter
echo "      xfetch 安装完成"

# 5. 生成启动脚本
echo "[5/5] 生成启动脚本..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
export PATH="$PATH:$HOME/.local/bin"
source .venv/bin/activate
python3 app.py
EOF
chmod +x start.sh

echo ""
echo "=============================="
echo "  安装完成，正在启动..."
echo "=============================="
echo ""
echo "请在浏览器打开: http://$(hostname -I | awk '{print $1}'):8888"
echo "下次启动只需运行: bash start.sh"
echo "按 Ctrl+C 停止程序"
echo ""
export PATH="$PATH:$HOME/.local/bin"
python3 app.py
