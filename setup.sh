#!/bin/bash
# 推文管理工具 - 一键安装脚本

set -e

echo "=============================="
echo "  推文管理工具 安装脚本"
echo "=============================="
echo ""

# 1. 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "错误: 请先安装 Python 3.8+"
    exit 1
fi
echo "[1/4] Python 已就绪: $(python3 --version)"

# 2. 安装 Python 依赖
echo "[2/4] 安装 Python 依赖..."
pip install anthropic --quiet
echo "      anthropic 已安装"

# 3. 安装 agent-reach (包含 xreach)
echo "[3/4] 安装 agent-reach..."
if command -v pipx &>/dev/null; then
    pipx install "https://github.com/Panniantong/agent-reach/archive/main.zip" --force
else
    pip install "https://github.com/Panniantong/agent-reach/archive/main.zip"
fi
agent-reach install --env=auto --channels=twitter
echo "      xreach 已安装"

# 4. 配置 X/Twitter Cookie
echo ""
echo "[4/4] 配置 X/Twitter 认证"
echo "-------------------------------"
echo "请按以下步骤获取 Cookie:"
echo "  1. 在浏览器登录 x.com"
echo "  2. 安装 Cookie-Editor 扩展:"
echo "     https://chromewebstore.google.com/detail/cookie-editor/"
echo "  3. 点击扩展 -> Export -> Header String"
echo "  4. 将复制的内容粘贴到下方"
echo ""
echo "建议使用小号，避免主账号被封！"
echo "-------------------------------"
read -p "请粘贴 Cookie Header String (按 Enter 跳过): " cookie_string

if [ -n "$cookie_string" ]; then
    agent-reach configure twitter-cookies "$cookie_string"
    echo "Cookie 配置成功"
else
    echo "已跳过 Cookie 配置，之后可运行: agent-reach configure twitter-cookies \"YOUR_COOKIE\""
fi

# 5. 设置 Claude API Key (可选)
echo ""
echo "-------------------------------"
echo "可选: 设置 Claude API Key 以启用 AI 汇总功能"
echo "获取地址: https://console.anthropic.com/"
echo "-------------------------------"
read -p "请输入 ANTHROPIC_API_KEY (按 Enter 跳过): " api_key

if [ -n "$api_key" ]; then
    # 写入 shell 配置文件
    SHELL_RC="$HOME/.bashrc"
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    echo "export ANTHROPIC_API_KEY=\"$api_key\"" >> "$SHELL_RC"
    export ANTHROPIC_API_KEY="$api_key"
    echo "API Key 已保存到 $SHELL_RC"
else
    echo "已跳过，之后可在 shell 配置文件中添加: export ANTHROPIC_API_KEY=\"your_key\""
fi

echo ""
echo "=============================="
echo "  安装完成!"
echo "=============================="
echo ""
echo "使用方法:"
echo "  python3 tweet_manager.py search \"AI新闻\" -n 20 --summarize"
echo "  python3 tweet_manager.py user @elonmusk -n 10 --summarize"
echo "  python3 tweet_manager.py thread https://x.com/user/status/123"
echo ""
echo "运行健康检查:"
echo "  agent-reach doctor"
