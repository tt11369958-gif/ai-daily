"""
run.py — AI 日报 一键运行脚本
用法: python scripts/run.py

完整流程: 抓取新闻 → LLM 筛选摘要 → 生成 HTML → 发布 GitHub Pages → 推送企业微信
"""

import os, sys, json, time
import io

# 修复 Windows 控制台 GBK 编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 确保脚本目录在 path
sys.path.insert(0, os.path.dirname(__file__))

BASE = os.path.dirname(__file__)

def _g(cfg, *keys, default=""):
    for k in keys:
        if isinstance(cfg, dict):
            cfg = cfg.get(k, default)
        else:
            return default
    return cfg if cfg else default

def log(msg, emoji="📋"):
    print(f"{emoji} {msg}")

def run():
    start = time.time()
    print("=" * 50)
    print("  🤖 AI 日报自动化系统  v1.0")
    print("=" * 50)

    # ── Step 1: 加载配置 ──────────────────────────
    config = {}
    for fname in ["config.json", "config.example.json"]:
        path = os.path.join(BASE, "..", fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                config = json.load(f)
            break

    model  = _g(config, "llm", "model",    default="deepseek-chat")
    apikey = _g(config, "llm", "api_key",  default="") or \
             os.environ.get("OPENAI_API_KEY", "")
    base   = _g(config, "llm", "api_base", default="") or \
             os.environ.get("OPENAI_API_BASE", "")

    print(f"\n📁 配置加载: {model}")
    if base: print(f"   API Base: {base}")

    if not apikey:
        log("⚠ 未配置 LLM API Key，请在 config.json 的 llm.api_key 中设置", "⚠")
        return

    config["_effective_api_key"] = apikey
    config["_effective_api_base"] = base
    config["_effective_model"]    = model

    # GitHub 配置（历史日报功能需要）
    github_user  = _g(config, "github", "user",  default="") or os.environ.get("GITHUB_USER", "")
    github_repo  = _g(config, "github", "repo",  default="ai-daily")
    github_token  = _g(config, "github", "token", default="") or os.environ.get("GITHUB_TOKEN", "")

    # ── Step 2: 抓取新闻 ────────────────────────────
    log("步骤 1/5：抓取 AI 新闻...")
    from fetch_news import fetch_all
    articles = fetch_all()
    if not articles:
        log("未抓取到任何文章，请检查 RSS 源是否可达", "❌")
        return
    with open(os.path.join(BASE, "..", "raw_articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    log(f"抓取完成，共 {len(articles)} 条原始文章")

    # ── Step 3: LLM 筛选 & 摘要 ─────────────────────
    log("步骤 2/5：大模型筛选 & 生成中文摘要...")
    from summarize import score_and_summarize
    summarized = score_and_summarize(articles, config)
    if not summarized:
        log("LLM 处理失败，使用 fallback 策略", "⚠")
        summarized = [{"title": a.get("title","无标题"),
                       "summary": (a.get("summary","") or a.get("description",""))[:200],
                       "source": a.get("source",""), "url": a.get("url",""),
                       "importance": 5, "category": "资讯"}
                      for a in articles[:10]]
    with open(os.path.join(BASE, "..", "summarized_articles.json"), "w", encoding="utf-8") as f:
        json.dump(summarized, f, ensure_ascii=False, indent=2)
    log(f"筛选完成，精选 {len(summarized)} 条")

    # ── Step 4: 生成 HTML ───────────────────────────
    log("步骤 3/5：生成精美 HTML 页面（含历史导航）...")
    from generate_html import generate_html
    html_path = os.path.join(BASE, "..", "index.html")
    generate_html(summarized, config, html_path,
                  user=github_user, repo=github_repo, token=github_token)
    log(f"HTML 生成完成: {html_path}")

    # ── Step 5: 发布 GitHub Pages ────────────────────
    pages_url = ""
    cover_url = ""
    log("步骤 4/5：发布 GitHub Pages...")
    from publish_github import publish
    try:
        result = publish(html_path, articles=summarized)
        if isinstance(result, tuple):
            pages_url, cover_url = result
        else:
            pages_url = result or ""
    except Exception as e:
        log(f"GitHub 发布失败（可跳过）: {e}", "⚠")

    # ── Step 6: 企业微信推送 ───────────────────────
    log("步骤 5/5：推送企业微信群...")
    from notify_wecom import send_wecom_notification
    try:
        send_wecom_notification(summarized, pages_url=pages_url, cover_url=cover_url)
    except Exception as e:
        log(f"企微推送失败: {e}", "⚠")

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"  ✅ 完成！耗时 {elapsed:.1f} 秒")
    if pages_url:
        print(f"  🌐 页面地址: {pages_url}")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
