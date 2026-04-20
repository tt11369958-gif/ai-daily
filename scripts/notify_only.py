"""
notify_only.py — 仅发送企业微信通知（GitHub Actions 部署后调用）
用法: python scripts/notify_only.py
从 output/ 目录读取 summarized_articles.json
页面地址从环境变量 GITHUB_PAGES_URL 获取
"""
import os, json, sys, re, glob
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(BASE)

def get(cfg, *keys, default=""):
    for k in keys:
        if isinstance(cfg, dict):
            cfg = cfg.get(k, default)
        else:
            return default
    return cfg if cfg else default

def load_config():
    for fname in ["config.json", "config.example.json"]:
        path = os.path.join(BASE_DIR, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}

def build_pages_url():
    """构建 GitHub Pages URL"""
    # 优先从环境变量获取（GitHub Actions 部署后会自动设置）
    url = os.environ.get("GITHUB_PAGES_URL", "").strip()
    if url:
        return url
    # fallback: 从 config 或环境变量构建
    config = load_config()
    user = os.environ.get("GH_USER", "") or get(config, "github", "user", default="tt11369958-gif")
    repo = os.environ.get("GH_REPO", "") or get(config, "github", "repo", default="ai-daily")
    if user:
        return f"https://{user}.github.io/{repo}"
    return "https://tt11369958-gif.github.io/ai-daily"

def build_cover_url(pages_url=""):
    """构建封面图 URL：优先用 pollinations AI 每日生成，fallback 用默认图"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    # 用 pollinations AI 生成每日不同的封面图
    prompt = "AI technology news daily briefing, futuristic digital interface, neural network visualization, dark theme, professional"
    import urllib.parse, time
    encoded = urllib.parse.quote(prompt)
    seed = int(today.replace("-", "")) % 10000
    ts = int(time.time())
    cover_url = f"https://image.pollinations.ai/prompt/{encoded}?seed={seed}&width=1200&height=600&nologo=true&t={ts}"
    return cover_url

def send_wecom_notification(articles, pages_url="", cover_url=""):
    """发送模板卡片到企业微信群"""
    webhook = os.environ.get("WECOM_WEBHOOK", "")
    if not webhook:
        config = load_config()
        webhook = get(config, "wecom", "webhook", default="")

    if not webhook:
        print("⚠ 未配置 WECOM_WEBHOOK，跳过企微推送")
        return

    if not articles:
        print("⚠ 无文章数据，跳过企微推送")
        return

    # 确保 pages_url 不为空
    if not pages_url:
        pages_url = build_pages_url()

    # 构建文章摘要
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]

    headline = articles[0]
    headline_title = headline.get("chinese_summary", headline.get("title", ""))[:50]
    headline_source = headline.get("source", "")

    # 构建要闻列表
    highlights = []
    for a in articles[1:8]:
        t = a.get("chinese_summary", a.get("title", ""))[:40]
        src = a.get("source", "")
        highlights.append(f"• {t} [{src}]")
    digest = "\n".join(highlights) if highlights else "查看完整日报获取更多资讯"

    # 封面图 URL
    if not cover_url:
        cover_url = build_cover_url(pages_url)
    card_image = {"url": cover_url, "aspect_ratio": 2}

    payload = {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "source": {
                "icon_url": "https://cdn-icons-png.flaticon.com/512/5968/5968751.png",
                "desc": f"{date_str} {weekday} · AI Daily"
            },
            "main_title": {
                "title": f"🤖 {headline_title[:30]}",
                "desc": f"来源：{headline_source}"
            },
            "card_image": card_image,
            "card_action": {
                "type": 1,
                "url": pages_url
            }
        }
    }

    import requests
    print(f"发送企微卡片...")
    print(f"  URL: {pages_url}")
    print(f"  封面: {cover_url}")

    r = requests.post(webhook, json=payload, timeout=15)
    if r.status_code == 200:
        result = r.json()
        if result.get("errcode") == 0:
            print(f"✅ 企微推送成功！")
        else:
            print(f"❌ 企微推送失败: {result}")
    else:
        print(f"❌ 企微推送请求失败: {r.status_code} - {r.text}")

def run():
    print("=" * 50)
    print("  📲 企微通知发送")
    print("=" * 50)

    articles_path = os.path.join(BASE_DIR, "output", "summarized_articles.json")
    if not os.path.exists(articles_path):
        articles_path = os.path.join(BASE_DIR, "summarized_articles.json")

    if os.path.exists(articles_path):
        with open(articles_path, encoding="utf-8") as f:
            articles = json.load(f)
        print(f"  → 读取到 {len(articles)} 条文章")
    else:
        print("⚠ 未找到文章数据，跳过推送")
        return

    pages_url = build_pages_url()
    cover_url = build_cover_url(pages_url)

    print(f"  → 页面地址: {pages_url}")
    print(f"  → 封面图: {cover_url}")

    send_wecom_notification(articles, pages_url=pages_url, cover_url=cover_url)

if __name__ == "__main__":
    run()
