#!/usr/bin/env python3
"""
Tweet Manager - 推文搜索与汇总工具
使用 xreach 获取推文，使用 Claude AI 进行汇总
"""

import subprocess
import json
import sys
import argparse
import os


def run_xreach(args: list) -> dict | list | None:
    """运行 xreach 命令并返回 JSON 结果"""
    try:
        result = subprocess.run(
            ["xreach"] + args + ["--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"xreach 错误: {result.stderr.strip()}", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("错误: 未找到 xreach，请先运行 setup.sh 安装依赖", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("错误: 请求超时", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"错误: 无法解析返回数据 - {e}", file=sys.stderr)
        return None


def format_tweet(tweet: dict) -> str:
    """格式化单条推文"""
    author = tweet.get("author", {})
    name = author.get("name", "未知用户")
    username = author.get("username", "")
    text = tweet.get("text", "")
    created_at = tweet.get("created_at", "")
    metrics = tweet.get("public_metrics", {})
    likes = metrics.get("like_count", 0)
    retweets = metrics.get("retweet_count", 0)
    replies = metrics.get("reply_count", 0)

    lines = [
        f"@{username} ({name})",
        f"{text}",
        f"点赞: {likes}  转推: {retweets}  回复: {replies}",
    ]
    if created_at:
        lines.append(f"时间: {created_at}")
    return "\n".join(lines)


def summarize_with_claude(tweets_text: str, query: str) -> str:
    """使用 Claude API 汇总推文"""
    try:
        import anthropic
    except ImportError:
        print("提示: 未安装 anthropic 库，跳过 AI 汇总 (pip install anthropic)", file=sys.stderr)
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("提示: 未设置 ANTHROPIC_API_KEY 环境变量，跳过 AI 汇总", file=sys.stderr)
        return ""

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""以下是关于"{query}"的推文内容，请用中文做一个简洁的汇总：
1. 主要话题和观点
2. 热门内容亮点
3. 整体舆论倾向

推文内容：
{tweets_text}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def cmd_search(args):
    """搜索推文"""
    print(f"\n正在搜索: {args.query} (获取 {args.count} 条)...\n")
    data = run_xreach(["search", args.query, "-n", str(args.count)])
    if not data:
        return

    tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
    if not tweets:
        print("未找到相关推文")
        return

    print(f"找到 {len(tweets)} 条推文\n" + "=" * 50)
    tweets_texts = []
    for i, tweet in enumerate(tweets, 1):
        formatted = format_tweet(tweet)
        print(f"\n[{i}]\n{formatted}\n{'-' * 40}")
        tweets_texts.append(tweet.get("text", ""))

    if args.summarize:
        print("\n" + "=" * 50)
        print("AI 汇总分析:")
        print("=" * 50)
        summary = summarize_with_claude("\n\n".join(tweets_texts), args.query)
        if summary:
            print(summary)


def cmd_user(args):
    """获取用户时间线"""
    username = args.username.lstrip("@")
    print(f"\n正在获取 @{username} 的推文 ({args.count} 条)...\n")
    data = run_xreach(["tweets", f"@{username}", "-n", str(args.count)])
    if not data:
        return

    tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
    if not tweets:
        print(f"未找到 @{username} 的推文")
        return

    print(f"@{username} 最新 {len(tweets)} 条推文\n" + "=" * 50)
    tweets_texts = []
    for i, tweet in enumerate(tweets, 1):
        formatted = format_tweet(tweet)
        print(f"\n[{i}]\n{formatted}\n{'-' * 40}")
        tweets_texts.append(tweet.get("text", ""))

    if args.summarize:
        print("\n" + "=" * 50)
        print(f"@{username} 推文 AI 汇总:")
        print("=" * 50)
        summary = summarize_with_claude("\n\n".join(tweets_texts), f"@{username} 的推文")
        if summary:
            print(summary)


def cmd_thread(args):
    """获取推文对话串"""
    print(f"\n正在获取对话串...\n")
    data = run_xreach(["thread", args.url])
    if not data:
        return

    tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
    if not tweets:
        print("未找到对话内容")
        return

    print(f"对话串共 {len(tweets)} 条\n" + "=" * 50)
    for i, tweet in enumerate(tweets, 1):
        formatted = format_tweet(tweet)
        print(f"\n[{i}]\n{formatted}\n{'-' * 40}")


def main():
    parser = argparse.ArgumentParser(
        description="推文管理工具 - 搜索与汇总 X/Twitter 内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tweet_manager.py search "AI新闻" -n 20 --summarize
  python tweet_manager.py user @elonmusk -n 10 --summarize
  python tweet_manager.py thread https://x.com/user/status/123456
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # search 子命令
    p_search = subparsers.add_parser("search", help="搜索推文")
    p_search.add_argument("query", help="搜索关键词")
    p_search.add_argument("-n", "--count", type=int, default=10, help="获取数量 (默认: 10)")
    p_search.add_argument("-s", "--summarize", action="store_true", help="使用 AI 汇总")
    p_search.set_defaults(func=cmd_search)

    # user 子命令
    p_user = subparsers.add_parser("user", help="获取用户时间线")
    p_user.add_argument("username", help="用户名 (如 @elonmusk 或 elonmusk)")
    p_user.add_argument("-n", "--count", type=int, default=10, help="获取数量 (默认: 10)")
    p_user.add_argument("-s", "--summarize", action="store_true", help="使用 AI 汇总")
    p_user.set_defaults(func=cmd_user)

    # thread 子命令
    p_thread = subparsers.add_parser("thread", help="获取推文对话串")
    p_thread.add_argument("url", help="推文 URL 或 ID")
    p_thread.set_defaults(func=cmd_thread)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
