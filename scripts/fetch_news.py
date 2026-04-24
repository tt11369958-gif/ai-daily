"""
fetch_news.py — 从多个 AI 媒体源抓取新闻
"""

import feedparser
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

RSS_FEEDS = {
    # 🤖 AI/人工智能相关 (11个)
    "机器之心": "https://decemberpei.cyou/rssbox/wechat-jiqizhixin.xml",
    "量子位": "https://decemberpei.cyou/rssbox/wechat-liangziwei.xml",
    "新智元": "https://decemberpei.cyou/rssbox/wechat-xinzhiyuan.xml",
    "DeepTech深科技": "https://decemberpei.cyou/rssbox/wechat-shenkeji.xml",
    "PaperWeekly": "https://decemberpei.cyou/rssbox/wechat-paperweekly.xml",
    "计算机视觉life": "https://decemberpei.cyou/rssbox/wechat-jisuanjishijuelife.xml",
    "AI前线": "https://decemberpei.cyou/rssbox/wechat-aiqianxian.xml",
    "夕小瑶科技说": "https://decemberpei.cyou/rssbox/wechat-xixiaoyaokejishuo.xml",
    "海外独角兽": "https://decemberpei.cyou/rssbox/wechat-haiwaidujiaoshou.xml",
    "甲子光年": "https://decemberpei.cyou/rssbox/wechat-jiaziguangnian.xml",
    "集智俱乐部": "https://decemberpei.cyou/rssbox/wechat-jizhijvlebu.xml",
    # 📰 科技/互联网媒体 (10个)
    "晚点LatePost": "https://decemberpei.cyou/rssbox/wechat-wandian.xml",
    "36氪": "https://decemberpei.cyou/rssbox/wechat-36ke.xml",
    "36氪Pro": "https://decemberpei.cyou/rssbox/wechat-sanliukepro.xml",
    "虎嗅App": "https://decemberpei.cyou/rssbox/wechat-huxiuapp.xml",
    "极客公园": "https://decemberpei.cyou/rssbox/wechat-jikegongyuan.xml",
    "少数派": "https://decemberpei.cyou/rssbox/wechat-shaoshupai.xml",
    "APPSO": "https://decemberpei.cyou/rssbox/wechat-appso.xml",
    "爱范儿": "https://decemberpei.cyou/rssbox/wechat-anfaner.xml",
    "差评": "https://decemberpei.cyou/rssbox/wechat-chaping.xml",
    "钛媒体": "https://decemberpei.cyou/rssbox/wechat-taimeiti.xml",
    # 💻 技术/开发者 (7个)
    "InfoQ": "https://decemberpei.cyou/rssbox/wechat-infoq.xml",
    "阿里云开发者": "https://decemberpei.cyou/rssbox/wechat-aliyunkaifazhe.xml",
    "腾讯技术工程": "https://decemberpei.cyou/rssbox/wechat-tengxunjishugongcheng.xml",
    "前端之巅": "https://decemberpei.cyou/rssbox/wechat-qianduanzhidian.xml",
    "架构师之路": "https://decemberpei.cyou/rssbox/wechat-jiagoushizhilu.xml",
    "GitHubDaily": "https://decemberpei.cyou/rssbox/wechat-githubdaily.xml",
    # 💰 财经/投资 (8个)
    "华尔街见闻": "https://decemberpei.cyou/rssbox/wechat-huaerjiejianwen.xml",
    "财经杂志": "https://decemberpei.cyou/rssbox/wechat-caijingzazhi.xml",
    "第一财经YiMagazine": "https://decemberpei.cyou/rssbox/wechat-diyicaijing.xml",
    "经纬创投": "https://decemberpei.cyou/rssbox/wechat-jingweichuangtou.xml",
    "红杉汇": "https://decemberpei.cyou/rssbox/wechat-hongshanhui.xml",
    "42章经": "https://decemberpei.cyou/rssbox/wechat-sierzhangjing.xml",
    "远川投资评论": "https://decemberpei.cyou/rssbox/wechat-chuanyuanyouzipinglun.xml",
    "泽平宏观展望": "https://decemberpei.cyou/rssbox/wechat-zepinghongguanzhanwang.xml",
    # ✍️ 高质量个人博主 (13个)
    "caoz的梦呓": "https://decemberpei.cyou/rssbox/wechat-caozdemengyi.xml",
    "L先生说": "https://decemberpei.cyou/rssbox/wechat-lxianshengshuo.xml",
    "槽边往事": "https://decemberpei.cyou/rssbox/wechat-caobianwangshi.xml",
    "孟岩": "https://decemberpei.cyou/rssbox/wechat-mengyan.xml",
    "刘润": "https://decemberpei.cyou/rssbox/wechat-liurun.xml",
    "辉哥奇谭": "https://decemberpei.cyou/rssbox/wechat-huigeqitan.xml",
    "warfalcon": "https://decemberpei.cyou/rssbox/wechat-warfalcon.xml",
    "玉树芝兰": "https://decemberpei.cyou/rssbox/wechat-yushuzhilan.xml",
    "九边": "https://decemberpei.cyou/rssbox/wechat-jiubian.xml",
    "也谈钱": "https://decemberpei.cyou/rssbox/wechat-yetanqian.xml",
    "keso怎么看": "https://decemberpei.cyou/rssbox/wechat-kesozenmekan.xml",
    "阑夕": "https://decemberpei.cyou/rssbox/wechat-lanxi.xml",
    # 🎯 产品/商业 (6个)
    "人人都是产品经理": "https://decemberpei.cyou/rssbox/wechat-renrendoushichanpinjingli.xml",
    "互联网怪盗团": "https://decemberpei.cyou/rssbox/wechat-hulianwangguaidaotuan.xml",
    "乱翻书": "https://decemberpei.cyou/rssbox/wechat-luanfanshu.xml",
    "刘言飞语": "https://decemberpei.cyou/rssbox/wechat-liuyanfeiyu.xml",
    "产品犬舍": "https://decemberpei.cyou/rssbox/wechat-chanpinquanshe.xml",
    "FounderPark": "https://decemberpei.cyou/rssbox/wechat-founderpark.xml",
    # 🌐 英文科技/AI 媒体 (11个)
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

# ── 标题相似度去重 ──────────────────────────────────────
import re, urllib.parse

def _normalize(text):
    """标题标准化：去除标点、数字、英文、语气词，返回字符集合"""
    # 去除英文/数字/标点，保留中文
    text = re.sub(r'[a-zA-Z0-9]', '', text)
    text = re.sub(r'[\s\.,，。、！？!?\:\：\-\_\—\/\[\]【】]', '', text)
    # 去除常见噪音词
    noise = ['突发', '刚刚', '重磅', '刚刚', '快讯', '最新', '今日', '昨夜', '刚刚', '刚刚']
    for w in noise:
        text = text.replace(w, '')
    return set(text)

def _jaccard(s1, s2):
    """两个字符集合的 Jaccard 相似度 [0~1]"""
    if not s1 or not s2:
        return 0.0
    inter = len(s1 & s2)
    union = len(s1 | s2)
    return inter / union if union else 0.0

def _title_similar(t1, t2, threshold=0.65):
    """判断两个标题是否相似（超过 threshold 返回 True）"""
    s1, s2 = _normalize(t1), _normalize(t2)
    # 标题极短时，提高阈值避免误判
    if len(s1) < 5 or len(s2) < 5:
        return _jaccard(s1, s2) > 0.85
    return _jaccard(s1, s2) > threshold

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

    # ── 两层去重 ──────────────────────────────────────────
    # 第一层：URL 精确去重
    url_seen = set()
    by_url = []
    for a in all_articles:
        if a["url"] and a["url"] not in url_seen:
            url_seen.add(a["url"])
            by_url.append(a)

    # 第二层：标题相似度去重（中文优化）
    unique = []
    dup_count = 0
    for a in by_url:
        is_dup = False
        for u in unique:
            # URL 相同直接跳过（已在第一层防护）
            if u["url"] == a["url"]:
                is_dup = True
                break
            # 标题相似度 > 0.65 视为重复
            if _title_similar(u["title"], a["title"], threshold=0.65):
                is_dup = True
                # 保留评分更高的
                if (a.get("score") or 0) > (u.get("score") or 0):
                    unique.remove(u)
                    unique.append(a)
                dup_count += 1
                break
        if not is_dup:
            unique.append(a)

    print(f"\n✅ 共抓取 {len(unique)} 篇去重文章（过滤 {len(all_articles) - len(unique)} 篇重复，含 URL 去重 {len(all_articles) - len(by_url)} 篇 + 标题相似去重 {dup_count} 篇）")
    return unique

if __name__ == "__main__":
    articles = fetch_all()
    import json
    with open("raw_articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("已保存到 raw_articles.json")
