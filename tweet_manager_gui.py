#!/usr/bin/env python3
"""
Tweet Manager - X/Twitter 推文搜索与汇总工具 (GUI 版)
"""

import subprocess
import json
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


# ── 配置文件路径 ────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tweet_manager_config.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"api_key": ""}


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── xreach 调用 ─────────────────────────────────────────────
def run_xreach(args: list) -> list | None:
    try:
        result = subprocess.run(
            ["xreach"] + args + ["--json"],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode != 0:
            return None, result.stderr.strip()
        data = json.loads(result.stdout)
        tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
        return tweets, None
    except FileNotFoundError:
        return None, "未找到 xreach，请先完成安装配置"
    except subprocess.TimeoutExpired:
        return None, "请求超时，请重试"
    except Exception as e:
        return None, str(e)


def format_tweet(tweet: dict) -> str:
    author = tweet.get("author", {})
    name = author.get("name", "未知用户")
    username = author.get("username", "")
    text = tweet.get("text", "")
    created_at = tweet.get("created_at", "")[:10] if tweet.get("created_at") else ""
    metrics = tweet.get("public_metrics", {})
    likes = metrics.get("like_count", 0)
    retweets = metrics.get("retweet_count", 0)
    parts = [f"@{username}（{name}）  {created_at}", text,
             f"点赞 {likes}  转推 {retweets}", "─" * 50]
    return "\n".join(parts)


def summarize_with_claude(tweets_text: str, query: str, api_key: str) -> str:
    try:
        import anthropic
    except ImportError:
        return "请先安装 anthropic 库：pip install anthropic"
    if not api_key:
        return "请在设置中填写 Claude API Key"
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (f'以下是关于"{query}"的推文，请用中文汇总：\n'
              f'1. 主要话题和观点\n2. 热门内容亮点\n3. 整体舆论倾向\n\n{tweets_text}')
    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


# ── 主界面 ──────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("推文管理工具")
        self.geometry("820x640")
        self.resizable(True, True)
        self.configure(bg="#f0f0f0")
        self.config_data = load_config()
        self._build_ui()

    def _build_ui(self):
        # 顶部标题
        header = tk.Frame(self, bg="#1d9bf0", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="X / Twitter 推文管理工具",
                 font=("Microsoft YaHei", 16, "bold"),
                 bg="#1d9bf0", fg="white").pack()

        # 标签页
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_search_tab(nb)
        self._build_user_tab(nb)
        self._build_thread_tab(nb)
        self._build_settings_tab(nb)

    # ── 搜索 Tab ──
    def _build_search_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  搜索推文  ")

        row = tk.Frame(frame, pady=8)
        row.pack(fill="x", padx=12)
        tk.Label(row, text="关键词：", font=("Microsoft YaHei", 11)).pack(side="left")
        self.search_entry = ttk.Entry(row, width=35, font=("Microsoft YaHei", 11))
        self.search_entry.pack(side="left", padx=6)
        tk.Label(row, text="数量：", font=("Microsoft YaHei", 11)).pack(side="left")
        self.search_count = ttk.Spinbox(row, from_=5, to=50, width=5, font=("Microsoft YaHei", 11))
        self.search_count.set(10)
        self.search_count.pack(side="left", padx=4)
        self.search_summary_var = tk.BooleanVar()
        ttk.Checkbutton(row, text="AI 汇总", variable=self.search_summary_var).pack(side="left", padx=8)
        ttk.Button(row, text="搜索", command=self._do_search).pack(side="left", padx=4)

        self.search_result = scrolledtext.ScrolledText(frame, font=("Microsoft YaHei", 10), wrap="word")
        self.search_result.pack(fill="both", expand=True, padx=12, pady=6)

    # ── 用户时间线 Tab ──
    def _build_user_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  用户推文  ")

        row = tk.Frame(frame, pady=8)
        row.pack(fill="x", padx=12)
        tk.Label(row, text="用户名：", font=("Microsoft YaHei", 11)).pack(side="left")
        self.user_entry = ttk.Entry(row, width=25, font=("Microsoft YaHei", 11))
        self.user_entry.insert(0, "@")
        self.user_entry.pack(side="left", padx=6)
        tk.Label(row, text="数量：", font=("Microsoft YaHei", 11)).pack(side="left")
        self.user_count = ttk.Spinbox(row, from_=5, to=50, width=5, font=("Microsoft YaHei", 11))
        self.user_count.set(10)
        self.user_count.pack(side="left", padx=4)
        self.user_summary_var = tk.BooleanVar()
        ttk.Checkbutton(row, text="AI 汇总", variable=self.user_summary_var).pack(side="left", padx=8)
        ttk.Button(row, text="获取", command=self._do_user).pack(side="left", padx=4)

        self.user_result = scrolledtext.ScrolledText(frame, font=("Microsoft YaHei", 10), wrap="word")
        self.user_result.pack(fill="both", expand=True, padx=12, pady=6)

    # ── 对话串 Tab ──
    def _build_thread_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  对话串  ")

        row = tk.Frame(frame, pady=8)
        row.pack(fill="x", padx=12)
        tk.Label(row, text="推文链接：", font=("Microsoft YaHei", 11)).pack(side="left")
        self.thread_entry = ttk.Entry(row, width=50, font=("Microsoft YaHei", 11))
        self.thread_entry.pack(side="left", padx=6)
        ttk.Button(row, text="获取对话", command=self._do_thread).pack(side="left", padx=4)

        self.thread_result = scrolledtext.ScrolledText(frame, font=("Microsoft YaHei", 10), wrap="word")
        self.thread_result.pack(fill="both", expand=True, padx=12, pady=6)

    # ── 设置 Tab ──
    def _build_settings_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="  设置  ")

        tk.Label(frame, text="Claude API Key（用于 AI 汇总功能）",
                 font=("Microsoft YaHei", 11)).pack(anchor="w", padx=16, pady=(16, 4))
        self.api_key_entry = ttk.Entry(frame, width=60, font=("Microsoft YaHei", 11), show="*")
        self.api_key_entry.insert(0, self.config_data.get("api_key", ""))
        self.api_key_entry.pack(anchor="w", padx=16)

        ttk.Button(frame, text="保存设置", command=self._save_settings).pack(anchor="w", padx=16, pady=10)

        tk.Label(frame,
                 text="获取 Claude API Key：https://console.anthropic.com/\n\n"
                      "X Cookie 配置（首次使用需要）：\n"
                      "  1. 在浏览器登录 x.com\n"
                      "  2. 安装 Cookie-Editor 扩展\n"
                      "  3. 点击扩展 → Export → Header String\n"
                      "  4. 在下方粘贴并点击配置",
                 font=("Microsoft YaHei", 10), justify="left", fg="#555"
                 ).pack(anchor="w", padx=16, pady=(8, 4))

        cookie_row = tk.Frame(frame)
        cookie_row.pack(fill="x", padx=16, pady=4)
        self.cookie_entry = ttk.Entry(cookie_row, width=55, font=("Microsoft YaHei", 10))
        self.cookie_entry.pack(side="left", padx=(0, 8))
        ttk.Button(cookie_row, text="配置 Cookie", command=self._configure_cookie).pack(side="left")

    # ── 操作函数 ──
    def _set_result(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.config(state="normal")

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return
        count = int(self.search_count.get())
        self._set_result(self.search_result, "正在搜索，请稍候...")
        threading.Thread(target=self._search_worker, args=(query, count), daemon=True).start()

    def _search_worker(self, query, count):
        tweets, err = run_xreach(["search", query, "-n", str(count)])
        if err:
            self.after(0, self._set_result, self.search_result, f"错误：{err}")
            return
        lines = [f"搜索「{query}」找到 {len(tweets)} 条推文\n{'=' * 50}\n"]
        texts = []
        for i, t in enumerate(tweets, 1):
            lines.append(f"[{i}]\n{format_tweet(t)}\n")
            texts.append(t.get("text", ""))
        result = "\n".join(lines)
        if self.search_summary_var.get():
            result += "\n\n正在 AI 汇总...\n"
            self.after(0, self._set_result, self.search_result, result)
            summary = summarize_with_claude("\n\n".join(texts), query,
                                           self.config_data.get("api_key", ""))
            result += f"\n{'=' * 50}\nAI 汇总分析\n{'=' * 50}\n{summary}"
        self.after(0, self._set_result, self.search_result, result)

    def _do_user(self):
        username = self.user_entry.get().strip().lstrip("@")
        if not username:
            messagebox.showwarning("提示", "请输入用户名")
            return
        count = int(self.user_count.get())
        self._set_result(self.user_result, "正在获取，请稍候...")
        threading.Thread(target=self._user_worker, args=(username, count), daemon=True).start()

    def _user_worker(self, username, count):
        tweets, err = run_xreach(["tweets", f"@{username}", "-n", str(count)])
        if err:
            self.after(0, self._set_result, self.user_result, f"错误：{err}")
            return
        lines = [f"@{username} 最新 {len(tweets)} 条推文\n{'=' * 50}\n"]
        texts = []
        for i, t in enumerate(tweets, 1):
            lines.append(f"[{i}]\n{format_tweet(t)}\n")
            texts.append(t.get("text", ""))
        result = "\n".join(lines)
        if self.user_summary_var.get():
            result += "\n\n正在 AI 汇总...\n"
            self.after(0, self._set_result, self.user_result, result)
            summary = summarize_with_claude("\n\n".join(texts), f"@{username} 的推文",
                                           self.config_data.get("api_key", ""))
            result += f"\n{'=' * 50}\nAI 汇总分析\n{'=' * 50}\n{summary}"
        self.after(0, self._set_result, self.user_result, result)

    def _do_thread(self):
        url = self.thread_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入推文链接")
            return
        self._set_result(self.thread_result, "正在获取对话串，请稍候...")
        threading.Thread(target=self._thread_worker, args=(url,), daemon=True).start()

    def _thread_worker(self, url):
        tweets, err = run_xreach(["thread", url])
        if err:
            self.after(0, self._set_result, self.thread_result, f"错误：{err}")
            return
        lines = [f"对话串共 {len(tweets)} 条\n{'=' * 50}\n"]
        for i, t in enumerate(tweets, 1):
            lines.append(f"[{i}]\n{format_tweet(t)}\n")
        self.after(0, self._set_result, self.thread_result, "\n".join(lines))

    def _save_settings(self):
        self.config_data["api_key"] = self.api_key_entry.get().strip()
        save_config(self.config_data)
        messagebox.showinfo("成功", "设置已保存")

    def _configure_cookie(self):
        cookie = self.cookie_entry.get().strip()
        if not cookie:
            messagebox.showwarning("提示", "请先粘贴 Cookie 字符串")
            return
        try:
            result = subprocess.run(
                ["agent-reach", "configure", "twitter-cookies", cookie],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if result.returncode == 0:
                messagebox.showinfo("成功", "Cookie 配置成功！")
                self.cookie_entry.delete(0, "end")
            else:
                messagebox.showerror("失败", f"配置失败：{result.stderr.strip()}")
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到 agent-reach，请先运行安装脚本")


if __name__ == "__main__":
    app = App()
    app.mainloop()
