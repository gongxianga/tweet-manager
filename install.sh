#!/bin/bash
set -e

echo "=============================="
echo "  推文管理工具 一键安装"
echo "=============================="
echo ""

# 1. 系统依赖
echo "[1/5] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-venv python3-full pipx curl -qq
echo "      完成"

# 2. 虚拟环境 + Python 依赖
echo "[2/5] 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate
pip install flask anthropic --quiet
echo "      完成"

# 3. 安装 agent-reach（含 xfetch）
echo "[3/5] 安装 xfetch..."
pipx ensurepath --force
export PATH="$PATH:$HOME/.local/bin"

# 优先用镜像，超时则用原地址
if pipx install "https://mirror.ghproxy.com/https://github.com/Panniantong/agent-reach/archive/main.zip" --force 2>/dev/null; then
    echo "      镜像安装成功"
else
    echo "      镜像失败，尝试原地址..."
    pipx install "https://github.com/Panniantong/agent-reach/archive/main.zip" --force
fi
echo "      完成"

# 4. 初始化 twitter 频道
echo "[4/5] 初始化 twitter 支持..."
agent-reach install --env=auto --channels=twitter
echo "      完成"

# 5. 生成启动脚本
echo "[5/5] 生成启动脚本..."
cat > start.sh << 'STARTEOF'
#!/bin/bash
cd "$(dirname "$0")"
export PATH="$PATH:$HOME/.local/bin"
source .venv/bin/activate
python3 app.py
STARTEOF
chmod +x start.sh
echo "      完成"

echo ""
echo "=============================="
echo "  安装完成！"
echo "=============================="
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}'):8888"
echo "下次启动: bash start.sh"
echo ""
echo "正在启动..."
export PATH="$PATH:$HOME/.local/bin"
python3 app.py
