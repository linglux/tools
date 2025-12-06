from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import os
import json
import re

app = Flask(__name__)

def translate_to_chinese(text: str) -> str:
    """使用 Google Translate API 将英文翻译成中文"""
    if not text or text.strip() == "" or text == "<p>(无文本)</p>":
        return text
    
    # 移除 HTML 标签，只翻译纯文本
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    if not clean_text:
        return text
    
    try:
        # 使用 Google Translate 免费 API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",  # 源语言：英文
            "tl": "zh-CN",  # 目标语言：简体中文
            "dt": "t",
            "q": clean_text
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        # 解析翻译结果
        translated_parts = []
        if result and result[0]:
            for part in result[0]:
                if part[0]:
                    translated_parts.append(part[0])
        
        translated_text = "".join(translated_parts)
        return translated_text if translated_text else text
    except Exception as e:
        print(f"翻译失败: {e}")
        return text  # 翻译失败时返回原文

DEFAULT_API = (
    "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses"
    "?exclude_replies=true&only_replies=false&with_muted=true"
)

TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Truth Social 微博列表</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg: #0f172a;
      --card: #111827;
      --muted: #94a3b8;
      --text: #e5e7eb;
      --accent: #38bdf8;
      --border: #1f2937;
      --highlight: #0ea5e9;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; background: linear-gradient(180deg, #0b1020, #0f172a);
      color: var(--text); font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Microsoft Yahei", sans-serif;
    }
    header {
      position: sticky; top: 0; z-index: 10;
      backdrop-filter: blur(8px);
      background: rgba(15, 23, 42, .7);
      border-bottom: 1px solid var(--border);
    }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 16px; }
    h1 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: .2px; }
    .toolbar {
      display: flex; gap: 8px; margin-top: 12px; align-items: center;
    }
    input[type="text"] {
      flex: 1; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border);
      background: #0b1220; color: var(--text); outline: none;
    }
    button {
      padding: 10px 14px; border: 1px solid #1e293b; border-radius: 10px;
      background: linear-gradient(180deg, #0ea5e9, #0284c7); color: white; cursor: pointer;
    }
    button:hover { filter: brightness(1.05); }
    .grid {
      display: list-item; grid-template-columns: 1fr; gap: 14px; margin-top: 16px;
    }
    @media (min-width: 700px) { .grid { grid-template-columns: 1fr 1fr; } }
    .card {
      background: radial-gradient(1200px 400px at -10% -20%, rgba(56,189,248,.08), transparent 50%),
                  radial-gradient(900px 300px at 120% 120%, rgba(56,189,248,.06), transparent 50%),
                  var(--card);
      border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
      box-shadow: 0 10px 30px rgba(2,6,23,.5);
      display: flex; flex-direction: column;
      margin-bottom: 15px;
    }
    .card-head { display: flex; gap: 12px; padding: 14px; border-bottom: 1px solid var(--border); align-items: center; }
    .avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 1px solid #243041; }
    .names { display: flex; flex-direction: column; min-width: 0; }
    .display { font-weight: 700; }
    .username { color: var(--muted); font-size: 13px; }
    .meta { margin-left: auto; color: var(--muted); font-size: 12px; }
    .content { padding: 14px; line-height: 1.6; color: #e8edf4; }
    .content p { margin: .4em 0; }
    .content a { color: var(--accent); text-decoration: none; }
    .content a:hover { text-decoration: underline; }
    .content-original { margin-bottom: 12px; }
    .content-translated { 
      padding: 12px; 
      background: rgba(56,189,248,.1); 
      border-radius: 8px; 
      border-left: 3px solid var(--accent);
      color: #bae6fd;
    }
    .translate-label { 
      font-size: 12px; 
      color: var(--accent); 
      font-weight: 600;
      display: block;
      margin-bottom: 6px;
    }
    .media { padding: 0 14px 14px; display: grid; gap: 10px; }
    .thumb, video {
      width: 100%; border-radius: 10px; border: 1px solid #223046; background: #0b1220;
    }
    .stats { padding: 12px 14px; display: flex; gap: 16px; border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; }
    .badge { display: inline-block; margin-left: 6px; padding: 2px 6px; font-size: 11px; border-radius: 20px; border: 1px solid #1e293b; color: #bae6fd; }
    .empty, .error {
      margin: 24px auto; max-width: 720px; padding: 16px; border-radius: 12px;
      border: 1px dashed #334155; background: rgba(2,6,23,.4); color: var(--muted);
    }
    footer { color: var(--muted); font-size: 12px; text-align: center; padding: 20px 0 40px; }
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Truth Social 微博列表</h1>
    </div>
  </header>

  <main class="wrap">
    {% if error %}
      <div class="error">请求失败：{{ error }}</div>
    {% elif not items %}
      <div class="empty">没有数据返回。</div>
    {% else %}
      <div class="grid">
        {% for s in items %}
          <article class="card">
            <div class="card-head">
              <div class="names">
                <div class="display">{{ s.account.display_name or s.account.username }}</div>
                <div class="username">@{{ s.account.acct }}</div>
              </div>
              <div class="meta" title="{{ s.created_at_raw }}">{{ s.created_at_fmt }}</div>
            </div>
            <div class="content">
              <div class="content-original">{{ s.content_text | safe }}</div>
              {% if s.content_text_cn and s.content_text_cn != s.content_text %}
              <div class="content-translated">
                <span class="translate-label">中文翻译：</span>
                {{ s.content_text_cn }}
              </div>
              {% endif %}
            </div>
          </article>
        {% endfor %}
      </div>
      <footer>数据来源：Truth Social API · 页面仅供演示</footer>
    {% endif %}
  </main>
</body>
</html>
"""

def make_flaresolverr_request(url, headers=None, params=None):
    """Use FlareSolverr to fetch a URL and return a response-like object."""
    flaresolverr_url = f"http://127.0.0.1:8191/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 25000,
    }
    if headers:
        payload["headers"] = headers
    if params:
        from urllib.parse import urlencode
        url = url + "?" + urlencode(params)
        payload["url"] = url

    try:
        resp = requests.post(flaresolverr_url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") != "ok":
            logger.error(f"FlareSolverr error: {result}")
            raise Exception(f"FlareSolverr error: {result}")
        response_content = result["solution"]["response"]

        # Mimic a requests.Response object for .json() and .text
        class FakeResponse:
            def __init__(self, content):
                self._content = content
            def jsonText(self):
                import json
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(self._content, "html.parser")
                pre = soup.find("pre")
                if pre:
                    try:
                        return pre.text
                    except Exception as e:
                        print(f"Failed to parse JSON from <pre>: {e}")
                        print(f"<pre> content (first 500 chars): {pre.text[:500]}")
                        raise
                    print("No <pre> tag found in FlareSolverr HTML response")
                    print(f"HTML content (first 500 chars): {self._content[:500]}")

            @property
            def text(self):
                return self._content
        return FakeResponse(response_content)
    except Exception as e:
        print(f"FlareSolverr request failed for {url}: {e}")
        raise

def fmt_time(iso_str: str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        local = dt.astimezone()  # 转为本地时区
        return local.strftime("%Y-%m-%d %H:%M:%S"), iso_str
    except Exception:
        return iso_str, iso_str

def extract_content_html(content: str) -> str:
    if not content:
        return ""
    cleaned = content.replace("<p></p>", "").strip()
    return cleaned or "<p>(无文本)</p>"

@app.route("/")
def home():
    api = request.args.get("api", DEFAULT_API)

    try:
        resp = make_flaresolverr_request(api)
        data = json.loads(resp.jsonText())
        if not isinstance(data, list):
            data = data.get("items") or []
    except Exception as e:
        return render_template_string(TEMPLATE, api=api, error=str(e), items=None, count=None)

    items = []
    for s in data:
        created_fmt, created_raw = fmt_time(s.get("created_at", ""))
        media = s.get("media_attachments") or []
        account = s.get("account") or {}
        items.append({
            "id": s.get("id"),
            "created_at_fmt": created_fmt,
            "created_at_raw": created_raw,
            "visibility": s.get("visibility"),
            "replies_count": s.get("replies_count", 0),
            "reblogs_count": s.get("reblogs_count", 0),
            "favourites_count": s.get("favourites_count", 0),
            "content_text": extract_content_html(s.get("content") or ""),
            "content_text_cn": translate_to_chinese(extract_content_html(s.get("content") or "")),
            "account": {
                "display_name": (account.get("display_name") or "").strip() or account.get("username"),
                "username": account.get("username"),
                "acct": account.get("acct"),
                "avatar": account.get("avatar"),
            },
            "media": [
                {
                    "type": m.get("type"),
                    "url": m.get("url"),
                    "preview_url": m.get("preview_url"),
                } for m in media
            ]
        })

    return render_template_string(TEMPLATE, api=api, error=None, items=items, count=len(items))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=True)