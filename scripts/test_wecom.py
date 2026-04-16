import requests

# 逐个测试：先只保留 main_title
for name, payload in [
    ("main_title only", {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "main_title": {"title": "AI 日报精选", "desc": "每日 AI 行业资讯速递"},
            "card_action": {"type": 1, "url": "https://tt11369958-gif.github.io/ai-daily/"}
        }
    }),
    ("main_title + card_image", {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "main_title": {"title": "AI 日报精选", "desc": "每日 AI 行业资讯速递"},
            "card_image": {"url": "https://tt11369958-gif.github.io/ai-daily/assets/cover.png", "aspect_ratio": 2},
            "card_action": {"type": 1, "url": "https://tt11369958-gif.github.io/ai-daily/"}
        }
    }),
    ("main_title + source", {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "source": {"desc": "2026-04-14 周二 · AI 日报"},
            "main_title": {"title": "AI 日报精选", "desc": "每日 AI 行业资讯速递"},
            "card_action": {"type": 1, "url": "https://tt11369958-gif.github.io/ai-daily/"}
        }
    }),
    ("full with image_text_area", {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "news_notice",
            "source": {"desc": "2026-04-14 周二 · AI 日报"},
            "main_title": {"title": "AI 日报精选", "desc": "每日 AI 行业资讯速递"},
            "card_image": {"url": "https://tt11369958-gif.github.io/ai-daily/assets/cover.png", "aspect_ratio": 2},
            "image_text_area": {
                "type": 1, "url": "https://tt11369958-gif.github.io/ai-daily/",
                "title": "OpenAI 发布 GPT-5", "desc": "来源：OpenAI"
            },
            "jump_list": [{"type": 1, "title": "查看完整 AI 日报", "url": "https://tt11369958-gif.github.io/ai-daily/"}],
            "card_action": {"type": 1, "url": "https://tt11369958-gif.github.io/ai-daily/"}
        }
    }),
]:
    r = requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=626a0387-1734-46e8-9895-5bf60a525ca1",
        json=payload, timeout=15
    )
    result = r.json()
    print(f"{name}: errcode={result.get('errcode')} errmsg={result.get('errmsg','')}")
