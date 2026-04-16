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
    url = os.environ.get("GITHUB_PAGES_URL", "").strip()
    if url:
        return url
    config = load_config()
    user = os.environ.get("GH_USER", "") or get(config, "github", "user", default="")
    repo = os.environ.get("GH_REPO", "") or get(config, "github", "repo", default="ai-daily")
    if user:
        return f"https://{user}.github.io/{repo}"
    return ""

def build_cover_url(pages_url):
    """从 output/assets/ 找到封面图，构建公网 URL"""
    if not pages_url:
        return ""
    covers = glob.glob(os.path.join(BASE_DIR, "output", "assets", "cover-*.png"))
    if covers:
        latest = max(covers, key=os.path.getmtime)
        cover_name = os.path.basename(latest)
        return f"{pages_url.rstrip('/')}/assets/{cover_name}"
    return ""

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

    headline = articles[0]
    title = headline.get("title", "AI 资讯日报")[:50]

    highlights = []
    for a in articles[1:7]:
        t = a.get("title", "")[:30]
        src = a.get("source", "")
        highlights.append(f"• {t} [{src}]")

    digest = "\n".join(highlights) if highlights else "查看完整日报获取更多资讯"

    payload = {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "source": {"desc": "AI Daily", "desc_color": 1},
            "main_title": {"title": title, "desc": "每日 AI 资讯精选 · "},
            "card_image": cover_url,
            "quote_area": {"title": "📰 要闻速览", "digest": digest[:500]},
            "action_menu": {
                "desc": "查看完整日报",
                "action_list": [{"text": "📖 阅读完整原文", "type": 1}]
            },
            "card_action": {
                "type": 1,
                "url": pages_url
            }
        }
    }

    import requests
    r = requests.post(webhook, json=payload, timeout=15)
    if r.status_code == 200:
        result = r.json()
        if result.get("errcode") == 0:
            print(f"✅ 企微推送成功！")
        else:
            print(f"❌ 企微推送失败: {result.get('errmsg')}")
    else:
        print(f"❌ 企微推送请求失败: {r.status_code}")

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
