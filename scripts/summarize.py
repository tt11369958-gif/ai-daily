"""
summarize.py — 用大模型筛选最有价值的文章并生成中文摘要
"""

import json
import os
import re

def load_config():
    import json
    base = os.path.dirname(os.path.dirname(__file__))
    for fname in ["config.json", "config.example.json"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}

def _g(cfg, *keys, default=""):
    for k in keys:
        if isinstance(cfg, dict): cfg = cfg.get(k, default)
        else: return default
    return cfg if cfg else default

def get_llm_client(config):
    """构建 OpenAI 兼容的 LLM 客户端（支持嵌套 llm.* 和扁平 openai_* 两种格式）"""
    api_key = os.environ.get("OPENAI_API_KEY") or \
              _g(config, "llm", "api_key", default="") or \
              _g(config, "openai_api_key", default="")
    api_base = os.environ.get("OPENAI_API_BASE") or \
               _g(config, "llm", "api_base", default="") or \
               _g(config, "openai_api_base", default="https://api.deepseek.com/v1")
    model = os.environ.get("AI_MODEL") or \
            _g(config, "llm", "model", default="") or \
            _g(config, "ai_model", default="deepseek-chat")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=api_base)
        return client, model
    except ImportError:
        import requests
        return {"api_key": api_key, "api_base": api_base, "model": model}, "custom"

def call_llm(client, model, messages, max_tokens=3000):
    """统一调用接口"""
    try:
        if isinstance(client, dict):
            # 手动 HTTP 调用
            import requests
            resp = requests.post(
                f"{client['api_base']}/chat/completions",
                headers={"Authorization": f"Bearer {client['api_key']}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens},
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        else:
            response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
            return response.choices[0].message.content
    except Exception as e:
        print(f"  ⚠ LLM 调用失败: {e}")
        return None

def score_and_summarize(articles, config):
    """调用 LLM 对文章评分排序并生成中文摘要"""
    print("\n🤖 正在调用大模型筛选 & 摘要...")

    client, model = get_llm_client(config)
    max_articles = _g(config, "sources", "max_final", default=10)

    # 分批处理（避免 token 溢出）
    batch_size = 15
    scored = []

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        prompt = build_scoring_prompt(batch)

        response = call_llm(client, model, [{"role": "user", "content": prompt}])
        if not response:
            # fallback：直接取前 max_articles 篇
            scored.extend([(a, 5) for a in batch[:max_articles]])
            continue

        parsed = parse_llm_response(response, batch)
        scored.extend(parsed)
        print(f"  ✓ 批次 {i//batch_size + 1} 完成，筛选 {len(parsed)} 篇")

    # 排序取 top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top_articles = [a for a, _ in scored[:max_articles]]

    # 为每篇生成正式摘要
    print(f"\n✍️ 正在生成 {len(top_articles)} 条中文摘要...")
    final = []
    for idx, article in enumerate(top_articles):
        summary = generate_summary(article, client, model, idx + 1, len(top_articles))
        article["chinese_summary"] = summary
        final.append(article)
        print(f"  ✓ [{idx+1}/{len(top_articles)}] {article['title'][:40]}...")

    return final

def build_scoring_prompt(batch):
    """构建评分 prompt"""
    articles_text = "\n".join([
        f"[{i+1}] 来源: {a['source']}\n    标题: {a['title']}\n    摘要: {a['summary'][:150]}"
        for i, a in enumerate(batch)
    ])
    return f"""你是一个资深的 AI 科技记者。请对以下文章按新闻价值打分（1-10分），输出 JSON 数组。

评分标准：
- 重大突破 / 行业里程碑 → 9-10分
- 大厂重要动态 / 产品发布 → 7-8分
- 有趣但非核心 → 4-6分
- 普通资讯 → 1-3分

文章列表：
{articles_text}

请只输出纯 JSON 数组，格式：[{{"index": 1, "score": 9, "reason": "原因"}}, ...]，不要有其他文字。"""

def parse_llm_response(response, batch):
    """解析 LLM 评分响应"""
    import re, json
    try:
        # 提取 JSON 部分
        match = re.search(r'\[[\s\S]*\]', response)
        if not match:
            return [(a, 5) for a in batch[:5]]
        data = json.loads(match.group())
        index_map = {item["index"] - 1: item["score"] for item in data if "index" in item and "score" in item}
        return [(batch[i], int(index_map.get(i, 5))) for i in range(len(batch)) if i in index_map]
    except:
        return [(a, 5) for a in batch[:5]]

def generate_summary(article, client, model, idx, total):
    """为单篇文章生成 100-150 字的中文精华摘要"""
    prompt = f"""请将以下 AI 科技文章翻译并提炼为 100-150 字的中文精华摘要。
要求：专业、流畅、有信息量，保留核心数据和关键结论。

原文标题：{article['title']}
原文链接：{article['url']}
原文摘要：{article['summary'][:300]}

请直接输出摘要，不要加标题，不要加引号，不要有其他说明文字。"""

    response = call_llm(client, model, [{"role": "user", "content": prompt}], max_tokens=400)
    return response.strip() if response else article["summary"][:150]

if __name__ == "__main__":
    import json, os
    config = load_config()
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "raw_articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    summarized = score_and_summarize(articles, config)
    with open(os.path.join(base, "summarized_articles.json"), "w", encoding="utf-8") as f:
        json.dump(summarized, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(summarized)} 篇摘要到 summarized_articles.json")
