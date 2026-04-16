"""
fetch_news.py — 从多个 AI 媒体源抓取新闻
"""

import feedparser
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

RSS_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "InfoQ": "https://feed.infoq.com/",
    "ZDNet AI": "https://www.zdnet.com/news/rss/",
    "Hacker News": "https://hnrss.org/frontpage",
    "Towards Data Science": "https://towardsdatascience.com/feed",
    "AI Papers (arXiv)": "https://arxiv.org/rss/cs.AI",
}

MAX_AGE_DAYS = 1  # 只保留最近 1 天内的文章

def fetch_feed(name, url):
    """抓取单个 RSS 源，返回文章列表"""
    articles = []
    try:
        feed = feedparser.parse(url)
        cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
        for entry in feed.entries[:20]:
            # 解析发布时间
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # 判断是否 AI 相关（标题或摘要含关键词）
            title = entry.get("title", "")
            summary = strip_html(entry.get("summary", ""))
            text = title + " " + summary
            ai_keywords = [
                "ai", "artificial intelligence", "machine learning", "llm",
                "gpt", "chatgpt", "openai", "deep learning", "neural",
                "claude", "gemini", "anthropic", "stable diffusion",
                "langchain", "rag", "transformer", "nlp", "nvidia",
                "agent", "大模型", "人工智能", "生成式", "AIGC"
            ]
            is_ai = any(k.lower() in text.lower() for k in ai_keywords)

            if not is_ai:
                continue
            if pub_date and pub_date < cutoff:
                continue

            articles.append({
                "title": title.strip(),
                "url": entry.get("link", ""),
                "summary": summary[:300],
                "source": name,
                "published": pub_date.isoformat() if pub_date else "",
                "score": 0,
                "category": categorize(text),
            })
    except Exception as e:
        print(f"  ⚠ 抓取 {name} 失败: {e}")
    return name, articles

def strip_html(text):
    """去掉 HTML 标签"""
    import re
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return text.strip()

def categorize(text):
    """根据内容打标签"""
    text_lower = text.lower()
    if any(k in text_lower for k in ["research", "paper", "arxiv", "study", "discover", "breakthrough"]):
        return "研究突破"
    if any(k in text_lower for k in ["funding", "acqui", "invest", "raise", "series", "million", "估值", "融资", "收购"]):
        return "融资并购"
    if any(k in text_lower for k in ["open source", "github", "release", "launch", "product", "feature", "update", "开源", "发布", "产品"]):
        return "产品发布"
    if any(k in text_lower for k in ["regulation", "policy", "law", "ban", "china", "europe", "监管", "政策", "禁令"]):
        return "政策监管"
    if any(k in text_lower for k in ["hackathon", "demo", "showcase", "conference", "event", "活动"]):
        return "活动会议"
    return "行业动态"

def fetch_all():
    """并发抓取所有源，返回去重后的文章列表"""
    print("📡 正在抓取 AI 新闻源...")
    all_articles = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_feed, name, url): name for name, url in RSS_FEEDS.items()}
        for future in as_completed(futures):
            name, articles = future.result()
            all_articles.extend(articles)
            print(f"  ✓ {name}: {len(articles)} 篇")

    # 去重（按标题相似度）
    seen = set()
    unique = []
    for a in all_articles:
        key = a["title"][:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    print(f"\n✅ 共抓取 {len(unique)} 篇去重文章")
    return unique

if __name__ == "__main__":
    articles = fetch_all()
    import json
    with open("raw_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("已保存到 raw_articles.json")
