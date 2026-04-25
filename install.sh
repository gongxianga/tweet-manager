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
echo "[1/4] Python 已就绪"

# 创建工作目录
mkdir -p ~/tweet-manager && cd ~/tweet-manager

# 下载 app.py
echo "[2/4] 下载程序文件..."
curl -fsSL "https://raw.githubusercontent.com/gongxianga/tweet-manager/main/app.py" -o app.py

# 安装 Python 依赖
echo "[3/4] 安装依赖..."
pip3 install flask anthropic --quiet

# 安装 xreach
echo "[4/4] 安装 xreach..."
if ! command -v xreach &>/dev/null; then
    pip3 install "https://github.com/Panniantong/agent-reach/archive/main.zip" --quiet
    agent-reach install --env=auto --channels=twitter
fi

# 创建启动脚本
cat > ~/tweet-manager/start.sh << 'EOF'
#!/bin/bash
cd ~/tweet-manager
python3 app.py
EOF
chmod +x ~/tweet-manager/start.sh

echo ""
echo "=============================="
echo "  安装完成，正在启动..."
echo "=============================="
echo ""
echo "请在浏览器打开: http://localhost:8888"
echo "按 Ctrl+C 停止程序"
echo ""
python3 app.py
