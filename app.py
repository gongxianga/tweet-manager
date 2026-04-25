#!/usr/bin/env python3
"""
Tweet Manager - 本地网页版
运行: python app.py  然后打开 http://localhost:8888
"""

import subprocess
import json
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tweet_manager_config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"api_key": ""}


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def run_xreach(args):
    try:
        result = subprocess.run(
            ["xreach"] + args + ["--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None, result.stderr.strip() or "xreach 返回错误"
        data = json.loads(result.stdout)
        tweets = data if isinstance(data, list) else data.get("tweets", data.get("data", []))
        return tweets, None
    except FileNotFoundError:
        return None, "未找到 xreach，请先运行 setup.sh 安装"
    except subprocess.TimeoutExpired:
        return None, "请求超时，请重试"
    except Exception as e:
        return None, str(e)


def summarize_with_claude(texts, query, api_key):
    try:
        import anthropic
    except ImportError:
        return None, "请先安装 anthropic：pip install anthropic"
    if not api_key:
        return None, "请在设置页面填写 Claude API Key"
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (f'以下是关于"{query}"的推文，请用中文汇总：\n'
              f'1. 主要话题和观点\n2. 热门内容亮点\n3. 整体舆论倾向\n\n'
              + "\n\n".join(texts))
    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text, None


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>推文管理工具</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", Arial, sans-serif; background: #f5f8fa; color: #333; }
  header { background: #1d9bf0; color: white; padding: 16px 24px; font-size: 20px; font-weight: bold; }
  .container { max-width: 900px; margin: 24px auto; padding: 0 16px; }
  .tabs { display: flex; gap: 4px; margin-bottom: 0; }
  .tab { padding: 10px 20px; cursor: pointer; background: #dce; border-radius: 8px 8px 0 0;
         background: #e1e8ed; color: #555; font-size: 14px; border: none; }
  .tab.active { background: white; color: #1d9bf0; font-weight: bold; }
  .panel { display: none; background: white; border-radius: 0 8px 8px 8px;
           padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .panel.active { display: block; }
  .row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
  input[type=text], input[type=password], input[type=number] {
    border: 1px solid #ccd6dd; border-radius: 6px; padding: 8px 12px; font-size: 14px; }
  input[type=text]:focus, input[type=password]:focus { outline: none; border-color: #1d9bf0; }
  .btn { background: #1d9bf0; color: white; border: none; border-radius: 6px;
         padding: 8px 20px; font-size: 14px; cursor: pointer; }
  .btn:hover { background: #1a8cd8; }
  .btn-outline { background: white; color: #1d9bf0; border: 1px solid #1d9bf0; }
  .btn-outline:hover { background: #e8f5fe; }
  label { font-size: 14px; display: flex; align-items: center; gap: 6px; cursor: pointer; }
  .result { margin-top: 16px; background: #f5f8fa; border-radius: 8px;
            padding: 16px; min-height: 200px; font-size: 13px; line-height: 1.8;
            white-space: pre-wrap; word-break: break-all; max-height: 520px; overflow-y: auto; }
  .tweet-card { background: white; border: 1px solid #e1e8ed; border-radius: 10px;
                padding: 14px; margin-bottom: 12px; }
  .tweet-author { font-weight: bold; color: #1d9bf0; margin-bottom: 4px; }
  .tweet-text { margin-bottom: 8px; line-height: 1.6; }
  .tweet-meta { font-size: 12px; color: #888; }
  .summary-box { background: #e8f5fe; border-left: 4px solid #1d9bf0;
                 border-radius: 0 8px 8px 0; padding: 14px; margin-top: 16px; line-height: 1.8; }
  .summary-title { font-weight: bold; color: #1d9bf0; margin-bottom: 8px; }
  .loading { color: #888; font-style: italic; }
  .error { color: #e0245e; background: #fde8ef; padding: 10px 14px; border-radius: 6px; }
  .hint { font-size: 12px; color: #888; margin-top: 6px; }
  .settings-label { font-size: 14px; font-weight: bold; margin: 16px 0 6px; }
</style>
</head>
<body>
<header>🐦 X / Twitter 推文管理工具</header>
<div class="container">
  <div class="tabs">
    <button class="tab active" onclick="switchTab('search')">搜索推文</button>
    <button class="tab" onclick="switchTab('user')">用户推文</button>
    <button class="tab" onclick="switchTab('thread')">对话串</button>
    <button class="tab" onclick="switchTab('settings')">设置</button>
  </div>

  <!-- 搜索 -->
  <div id="tab-search" class="panel active">
    <div class="row">
      <input type="text" id="search-query" placeholder="输入关键词，如：AI新闻" style="width:260px">
      <input type="number" id="search-count" value="10" min="5" max="50" style="width:70px">
      <label><input type="checkbox" id="search-summarize"> AI 汇总</label>
      <button class="btn" onclick="doSearch()">搜索</button>
    </div>
    <div id="search-result" class="result" style="min-height:80px;display:none"></div>
  </div>

  <!-- 用户 -->
  <div id="tab-user" class="panel">
    <div class="row">
      <input type="text" id="user-name" placeholder="@用户名，如：@elonmusk" style="width:220px">
      <input type="number" id="user-count" value="10" min="5" max="50" style="width:70px">
      <label><input type="checkbox" id="user-summarize"> AI 汇总</label>
      <button class="btn" onclick="doUser()">获取</button>
    </div>
    <div id="user-result" class="result" style="min-height:80px;display:none"></div>
  </div>

  <!-- 对话串 -->
  <div id="tab-thread" class="panel">
    <div class="row">
      <input type="text" id="thread-url" placeholder="推文链接，如：https://x.com/user/status/..." style="width:420px">
      <button class="btn" onclick="doThread()">获取对话</button>
    </div>
    <div id="thread-result" class="result" style="min-height:80px;display:none"></div>
  </div>

  <!-- 设置 -->
  <div id="tab-settings" class="panel">
    <div class="settings-label">Claude API Key（用于 AI 汇总）</div>
    <div class="row">
      <input type="password" id="api-key" placeholder="sk-ant-..." style="width:400px">
      <button class="btn" onclick="saveSettings()">保存</button>
    </div>
    <p class="hint">获取地址：https://console.anthropic.com/</p>

    <div class="settings-label" style="margin-top:24px">X / Twitter Cookie 配置</div>
    <p class="hint" style="margin-bottom:10px">
      1. 在浏览器登录 x.com &nbsp;
      2. 安装 <a href="https://chromewebstore.google.com/detail/cookie-editor/" target="_blank">Cookie-Editor</a> 扩展 &nbsp;
      3. 点击扩展 → Export → Header String &nbsp;
      4. 粘贴到下方
    </p>
    <div class="row">
      <input type="text" id="cookie-str" placeholder="粘贴 Cookie Header String..." style="width:500px">
      <button class="btn btn-outline" onclick="configureCookie()">配置 Cookie</button>
    </div>
    <div id="settings-msg"></div>
  </div>
</div>

<script>
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
}

function renderTweets(tweets) {
  return tweets.map((t, i) => {
    const a = t.author || {};
    const m = t.public_metrics || {};
    const date = (t.created_at || '').slice(0,10);
    return `<div class="tweet-card">
      <div class="tweet-author">@${a.username||''}（${a.name||''}）</div>
      <div class="tweet-text">${escHtml(t.text||'')}</div>
      <div class="tweet-meta">点赞 ${m.like_count||0} &nbsp; 转推 ${m.retweet_count||0} &nbsp; 回复 ${m.reply_count||0} &nbsp; ${date}</div>
    </div>`;
  }).join('');
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function doSearch() {
  const query = document.getElementById('search-query').value.trim();
  const count = document.getElementById('search-count').value;
  const summarize = document.getElementById('search-summarize').checked;
  if (!query) { alert('请输入搜索关键词'); return; }
  const el = document.getElementById('search-result');
  el.style.display = 'block';
  el.innerHTML = '<span class="loading">正在搜索...</span>';
  const res = await fetch('/api/search', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({query, count, summarize})
  }).then(r => r.json());
  if (res.error) { el.innerHTML = `<div class="error">${res.error}</div>`; return; }
  el.innerHTML = `<b>搜索「${escHtml(query)}」找到 ${res.tweets.length} 条推文</b><br><br>` + renderTweets(res.tweets);
  if (res.summary) el.innerHTML += `<div class="summary-box"><div class="summary-title">AI 汇总分析</div>${escHtml(res.summary)}</div>`;
}

async function doUser() {
  const username = document.getElementById('user-name').value.trim().replace(/^@/,'');
  const count = document.getElementById('user-count').value;
  const summarize = document.getElementById('user-summarize').checked;
  if (!username) { alert('请输入用户名'); return; }
  const el = document.getElementById('user-result');
  el.style.display = 'block';
  el.innerHTML = '<span class="loading">正在获取...</span>';
  const res = await fetch('/api/user', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({username, count, summarize})
  }).then(r => r.json());
  if (res.error) { el.innerHTML = `<div class="error">${res.error}</div>`; return; }
  el.innerHTML = `<b>@${escHtml(username)} 最新 ${res.tweets.length} 条推文</b><br><br>` + renderTweets(res.tweets);
  if (res.summary) el.innerHTML += `<div class="summary-box"><div class="summary-title">AI 汇总分析</div>${escHtml(res.summary)}</div>`;
}

async function doThread() {
  const url = document.getElementById('thread-url').value.trim();
  if (!url) { alert('请输入推文链接'); return; }
  const el = document.getElementById('thread-result');
  el.style.display = 'block';
  el.innerHTML = '<span class="loading">正在获取对话串...</span>';
  const res = await fetch('/api/thread', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url})
  }).then(r => r.json());
  if (res.error) { el.innerHTML = `<div class="error">${res.error}</div>`; return; }
  el.innerHTML = `<b>对话串共 ${res.tweets.length} 条</b><br><br>` + renderTweets(res.tweets);
}

async function saveSettings() {
  const api_key = document.getElementById('api-key').value.trim();
  const res = await fetch('/api/settings', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({api_key})
  }).then(r => r.json());
  document.getElementById('settings-msg').innerHTML =
    res.ok ? '<p style="color:green;margin-top:8px">保存成功</p>' : '<p style="color:red;margin-top:8px">保存失败</p>';
}

async function configureCookie() {
  const cookie = document.getElementById('cookie-str').value.trim();
  if (!cookie) { alert('请先粘贴 Cookie 字符串'); return; }
  const res = await fetch('/api/configure-cookie', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({cookie})
  }).then(r => r.json());
  const msg = document.getElementById('settings-msg');
  if (res.ok) {
    msg.innerHTML = '<p style="color:green;margin-top:8px">Cookie 配置成功！</p>';
    document.getElementById('cookie-str').value = '';
  } else {
    msg.innerHTML = `<p style="color:red;margin-top:8px">失败：${res.error}</p>`;
  }
}

// 加载已保存的 API Key
fetch('/api/settings').then(r=>r.json()).then(d => {
  if (d.api_key) document.getElementById('api-key').value = d.api_key;
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.json
    query = data.get("query", "")
    count = int(data.get("count", 10))
    summarize = data.get("summarize", False)
    tweets, err = run_xreach(["search", query, "-n", str(count)])
    if err:
        return jsonify({"error": err})
    result = {"tweets": tweets}
    if summarize:
        texts = [t.get("text", "") for t in tweets]
        summary, err = summarize_with_claude(texts, query, load_config().get("api_key", ""))
        result["summary"] = summary or err
    return jsonify(result)


@app.route("/api/user", methods=["POST"])
def api_user():
    data = request.json
    username = data.get("username", "").lstrip("@")
    count = int(data.get("count", 10))
    summarize = data.get("summarize", False)
    tweets, err = run_xreach(["tweets", f"@{username}", "-n", str(count)])
    if err:
        return jsonify({"error": err})
    result = {"tweets": tweets}
    if summarize:
        texts = [t.get("text", "") for t in tweets]
        summary, err = summarize_with_claude(texts, f"@{username} 的推文", load_config().get("api_key", ""))
        result["summary"] = summary or err
    return jsonify(result)


@app.route("/api/thread", methods=["POST"])
def api_thread():
    data = request.json
    url = data.get("url", "")
    tweets, err = run_xreach(["thread", url])
    if err:
        return jsonify({"error": err})
    return jsonify({"tweets": tweets})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify(load_config())
    cfg = load_config()
    cfg["api_key"] = request.json.get("api_key", "")
    save_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/configure-cookie", methods=["POST"])
def api_configure_cookie():
    cookie = request.json.get("cookie", "")
    try:
        result = subprocess.run(
            ["agent-reach", "configure", "twitter-cookies", cookie],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": result.stderr.strip()})
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "未找到 agent-reach，请先运行安装脚本"})


if __name__ == "__main__":
    import webbrowser
    print("启动推文管理工具...")
    print("浏览器将自动打开 http://localhost:8888")
    webbrowser.open("http://localhost:8888")
    app.run(host="0.0.0.0", port=8888, debug=False)
