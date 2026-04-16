"""
notify_wecom.py — 企业微信群机器人推送（模板卡片 3.0 正式版）
来源角标 + 主标题 + 封面大图 + 跳转按钮
"""

import os, json, re, requests
from datetime import datetime
import html

def load_config():
    base = os.path.dirname(os.path.dirname(__file__))
    for fname in ["config.json", "config.example.json"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}

def _g(cfg, *keys, default=""):
    for k in keys:
        if isinstance(cfg, dict):
            cfg = cfg.get(k, default)
        else:
            return default
    return cfg if cfg else default

def _clean(text):
    """清理 HTML 实体"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _truncate(text, length):
    if len(text) <= length:
        return text
    return text[:length] + "..."

def send_wecom_notification(articles, pages_url="", title="AI 日报", cover_url=""):
    """发送模板卡片：来源角标 + 主标题 + 封面大图 + 跳转"""
    config = load_config()
    webhook = os.environ.get("WECOM_WEBHOOK") or \
              _g(config, "wecom", "webhook", default="") or \
              _g(config, "wecom_webhook", default="")

    if not webhook or "key=" not in webhook:
        print("⚠️  未配置企业微信 Webhook，跳过推送")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]

    headline = articles[0] if articles else {}
    chinese_summary = _clean(headline.get("chinese_summary", ""))

    # 从摘要第一句提取标题
    if chinese_summary:
        sentences = re.split(r"[。！？；，\n]", chinese_summary)
        headline_title = _truncate(sentences[0].strip(), 20)
    else:
        headline_title = "今日暂无更新"

    emoji_map = {
        "研究突破": "🔬", "融资并购": "💰", "产品发布": "🛠",
        "行业动态": "📊", "政策监管": "📋", "活动会议": "🎪", "开源工具": "🧩"
    }
    cat_emoji = emoji_map.get(headline.get("category", ""), "📌")
    headline_source = _clean(headline.get("source", ""))

    # 封面图：优先使用传入的 URL，否则用默认
    if not cover_url:
        cover_url = "https://tt11369958-gif.github.io/ai-daily/assets/cover.png"

    # ── 模板卡片 payload（企业微信官方格式，已验证可用） ──
    payload = {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "source": {
                "icon_url": "https://cdn-icons-png.flaticon.com/512/5968/5968751.png",
                "desc": f"{date_str} {weekday} · AI 日报"
            },
            "main_title": {
                "title": f"{cat_emoji} {headline_title}",
                "desc": f"来源：{headline_source}"
            },
            "card_image": {
                "url": cover_url,
                "aspect_ratio": 2
            },
            "card_action": {
                "type": 1,
                "url": pages_url
            }
        }
    }

    try:
        resp = requests.post(webhook, json=payload, timeout=15)
        result = resp.json()
        if result.get("errcode") == 0:
            print("✅ 企业微信推送成功！")
        else:
            print(f"❌ 推送失败：{result}")
    except Exception as e:
        print(f"❌ 推送异常：{e}")


if __name__ == "__main__":
    demo = [{
        "chinese_summary": "OpenAI 今日正式发布 GPT-5，新版支持高达 200 万 Token 的上下文窗口，可一次性处理整本书籍或代码库；推理能力较 GPT-4 提升 3 倍。",
        "source": "OpenAI",
        "category": "产品发布"
    }]
    send_wecom_notification(demo, "https://tt11369958-gif.github.io/ai-daily/")
