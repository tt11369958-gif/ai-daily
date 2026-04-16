"""
generate_html.py — 生成精美的暗色卡片式 HTML 页面（含历史日报功能）
"""

import json, os, re, html as html_mod
from datetime import datetime

CATEGORY_COLORS = {
    "全部": "#8b5cf6",
    "研究突破": "#f59e0b",
    "行业动态": "#10b981",
    "融资并购": "#ef4444",
    "产品发布": "#3b82f6",
    "政策监管": "#f97316",
    "活动会议": "#ec4899",
}

CATEGORY_ICONS = {
    "全部": "🤖",
    "研究突破": "🔬",
    "行业动态": "📊",
    "融资并购": "💰",
    "产品发布": "🛠",
    "政策监管": "📋",
    "活动会议": "🎪",
}

def _generate_history_nav(user, repo, token):
    """
    生成历史日报导航区域 HTML。
    下拉选项在浏览器端通过 fetch('history_index.json') 动态加载，
    选择历史日期后通过 fetch('history/YYYY-MM-DD.json') 动态渲染卡片，
    完全不依赖服务端目录跳转，避免 404。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    today_weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]

    return f'''
  <div class="history-nav">
    <span class="history-label">📜 历史日报</span>
    <select class="history-select" id="historySelect">
      <option value="">-- 加载中 --</option>
    </select>
  </div>
  <div id="historyBanner" style="display:none;background:#1a1035;border:1px solid #8b5cf640;border-radius:.75rem;padding:.75rem 1.25rem;margin:.5rem auto;max-width:700px;font-size:.82rem;color:#94a3b8;text-align:center;">
    正在查看历史日报：<strong id="historyDateLabel"></strong>
    &nbsp;·&nbsp;<a href="#" onclick="loadToday();return false;" style="color:#8b5cf6;">← 返回今日</a>
  </div>'''


def generate_html(articles, config, output_path=None, pages_url="", user="", repo="", token=""):
    print("🎨 正在生成 HTML 页面...")

    if not output_path:
        base = os.path.dirname(os.path.dirname(__file__))
        output_path = os.path.join(base, "index.html")

    categories = ["全部"] + sorted(set(a["category"] for a in articles))
    date_str = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.now().weekday()]

    # 分类导航
    category_nav = "\n".join([
        f'        <button class="cat-btn{" active" if c=="全部" else ""}" data-cat="{c}">'
        f'{CATEGORY_ICONS.get(c,"📌")} {c}</button>'
        for c in categories
    ])

    # 数据来源
    sources_used = sorted(set(a["source"] for a in articles))
    sources_html = " · ".join(sources_used)

    # 历史日报导航
    history_nav = _generate_history_nav(user, repo, token)

    # 卡片
    cards = []
    for i, a in enumerate(articles):
        color = CATEGORY_COLORS.get(a["category"], "#8b5cf6")
        icon = CATEGORY_ICONS.get(a["category"], "📌")
        rank = i + 1
        rank_color = "#ffd700" if rank == 1 else ("#c0c0c0" if rank == 2 else ("#cd7f32" if rank == 3 else "#555"))

        title_text = html_mod.unescape(a.get("title", ""))
        cards.append(f'''
        <article class="news-card" data-category="{a["category"]}" data-rank="{rank}">
            <div class="card-header">
                <div class="card-meta">
                    <span class="rank" style="color:{rank_color}">#{rank}</span>
                    <span class="source-tag" style="background:{color}20;color:{color}">{icon} {a["source"]}</span>
                    <span class="cat-tag" style="background:{color}30;color:{color}">{a["category"]}</span>
                </div>
            </div>
            <h2 class="card-title">
                <a href="{a["url"]}" target="_blank" rel="noopener">{title_text}</a>
            </h2>
            <p class="card-summary">{a.get("chinese_summary", a.get("summary",""))[:250]}</p>
            <div class="card-footer">
                <a class="read-more" href="{a["url"]}" target="_blank" rel="noopener">▶ 阅读原文</a>
                <span class="pub-date">{a.get("published", "")[:10]}</span>
            </div>
        </article>''')

    cards_html = "\n".join(cards)

    html = HTML_TEMPLATE.format(
        title=config.get("newspaper_title", "AI 日报"),
        date_str=date_str,
        weekday=weekday,
        article_count=len(articles),
        category_nav=category_nav,
        cards_html=cards_html,
        sources_html=sources_html,
        pages_url=pages_url or "#",
        history_nav=history_nav,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML 已生成: {output_path}")
    return output_path

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜{date_str}</title>
<style>
  :root {{
    --bg: #0a0a0f;
    --card-bg: #13131c;
    --card-border: #1e1e2e;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --accent: #8b5cf6;
    --accent2: #06b6d4;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box }}
  body {{ font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif;
         background:var(--bg); color:var(--text);
         min-height:100vh; line-height:1.6 }}
  a {{ color:inherit; text-decoration:none }}

  header {{
    background:linear-gradient(135deg,#0f0f1a 0%,#1a1035 100%);
    border-bottom:1px solid #2a2a4a;
    padding:2.5rem 2rem 2rem;
    text-align:center;
    position:sticky;top:0;z-index:100;
  }}
  .header-badge {{
    display:inline-block;
    background:linear-gradient(135deg,#8b5cf6,#06b6d4);
    color:#fff;font-size:.7rem;font-weight:700;
    padding:.25rem .75rem;border-radius:2rem;
    letter-spacing:.05em;margin-bottom:.75rem;
  }}
  h1 {{ font-size:2rem;font-weight:800;letter-spacing:-.02em;margin-bottom:.25rem }}
  .subtitle {{ color:var(--text-dim);font-size:.9rem }}
  .subtitle span {{ margin:0 .5rem }}

  /* 历史日报导航 */
  .history-nav {{
    display:flex;align-items:center;justify-content:center;gap:.75rem;
    margin-bottom:1.25rem;
  }}
  .history-label {{
    font-size:.8rem;color:var(--text-dim);
  }}
  .history-select {{
    background:#1a1a2e;border:1px solid #2a2a4a;color:var(--text);
    padding:.35rem .75rem;border-radius:.5rem;font-size:.82rem;
    cursor:pointer;outline:none;
  }}
  .history-select option {{ background:#13131c }}

  .filter-bar {{
    display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;
    padding:1.25rem 2rem;background:#0d0d18;
    border-bottom:1px solid #1e1e2e;
    position:sticky;top:85px;z-index:99;
  }}
  .cat-btn {{
    background:#1a1a2e;border:1px solid #2a2a4a;color:var(--text-dim);
    padding:.4rem 1rem;border-radius:.5rem;cursor:pointer;
    font-size:.82rem;transition:all .2s;
  }}
  .cat-btn:hover {{ border-color:var(--accent);color:var(--accent) }}
  .cat-btn.active {{ background:var(--accent);color:#fff;border-color:var(--accent) }}

  main {{ max-width:900px;margin:0 auto;padding:2rem 1.5rem }}

  .hero-card {{
    background:linear-gradient(135deg,#1a1035,#0f2540);
    border:1px solid #8b5cf640;border-radius:1rem;
    padding:1.75rem;margin-bottom:1.5rem;
    animation:fadeIn .5s ease;
  }}
  .hero-card .hero-label {{
    font-size:.7rem;color:#8b5cf6;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;margin-bottom:.5rem
  }}
  .hero-card h2 {{ font-size:1.4rem;line-height:1.3;margin-bottom:.75rem }}
  .hero-card h2 a:hover {{ color:var(--accent) }}
  .hero-card p {{ color:var(--text-dim);font-size:.9rem;line-height:1.7 }}
  .hero-card .read-more {{
    display:inline-block;margin-top:1rem;
    background:var(--accent);color:#fff;
    padding:.5rem 1.25rem;border-radius:.5rem;font-size:.85rem;
    transition:opacity .2s;
  }}
  .hero-card .read-more:hover {{ opacity:.85 }}

  .news-grid {{
    display:grid;grid-template-columns:1fr;
    gap:1rem;
  }}
  @media(min-width:640px) {{
    .news-grid {{ grid-template-columns:repeat(2,1fr) }}
  }}

  .news-card {{
    background:var(--card-bg);border:1px solid var(--card-border);
    border-radius:.875rem;padding:1.25rem;
    transition:transform .25s,border-color .25s,box-shadow .25s;
    animation:fadeIn .5s ease backwards;
  }}
  .news-card:hover {{
    transform:translateY(-3px);border-color:var(--accent);
    box-shadow:0 8px 32px #8b5cf620;
  }}
  .card-header {{ display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem }}
  .rank {{ font-size:.75rem;font-weight:800 }}
  .source-tag,.cat-tag {{
    font-size:.68rem;padding:.15rem .5rem;border-radius:.25rem;font-weight:600
  }}
  .cat-tag {{ opacity:.85 }}
  .card-title {{ font-size:.95rem;font-weight:700;line-height:1.4;margin-bottom:.75rem }}
  .card-title a:hover {{ color:var(--accent) }}
  .card-summary {{
    font-size:.82rem;color:var(--text-dim);line-height:1.65;
    display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden
  }}
  .card-footer {{
    display:flex;justify-content:space-between;align-items:center;
    margin-top:1rem;padding-top:.75rem;border-top:1px solid #1e1e2e
  }}
  .read-more {{ font-size:.78rem;color:var(--accent);font-weight:600 }}
  .read-more:hover {{ opacity:.8 }}
  .pub-date {{ font-size:.72rem;color:#555 }}

  footer {{
    text-align:center;padding:3rem 2rem;
    color:#555;font-size:.78rem;
    border-top:1px solid #1a1a2e;margin-top:3rem
  }}
  footer a {{ color:var(--accent) }}

  .sources-section {{ margin-top:1.25rem;padding-top:1rem;border-top:1px solid #1a1a2e }}
  .sources-label {{ font-size:.72rem;color:#444;margin-bottom:.3rem }}
  .sources-list {{ font-size:.75rem;color:#555;line-height:1.8 }}

  .hidden {{ display:none }}

  @keyframes fadeIn {{
    from{{opacity:0;transform:translateY(12px)}}
    to{{opacity:1;transform:translateY(0)}}
  }}

  .stats-bar {{
    display:flex;justify-content:center;gap:2rem;
    padding:1rem;font-size:.8rem;color:var(--text-dim)
  }}
  .stats-bar strong {{ color:var(--accent) }}
</style>
</head>
<body>

<header>
  <div class="header-badge">🤖 每日 AI 资讯精选</div>
  <h1>{title}</h1>
  <div class="subtitle">
    <span>{date_str}</span>·<span>{weekday}</span>·<span><strong>{article_count}</strong> 条精选</span>
  </div>
{history_nav}
</header>

<div class="filter-bar">
{category_nav}
</div>

<main>
  <div class="stats-bar">
    <span>🔍 已过滤低价值内容，点击分类查看</span>
    <span>🚀 <a href="{pages_url}" target="_blank">GitHub Pages</a></span>
  </div>

  <div class="news-grid" id="newsGrid">
{cards_html}
  </div>
</main>

<footer>
  <p>由 <strong>AI 日报自动化系统</strong> 生成 · 每日更新</p>
  <div class="sources-section">
    <p class="sources-label">📡 数据来源</p>
    <p class="sources-list">{sources_html}</p>
  </div>
</footer>

<script>
// ── 分类过滤 ──
function bindCatBtns() {{
  const btns = document.querySelectorAll('.cat-btn');
  btns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      document.querySelectorAll('.news-card').forEach(card => {{
        card.classList.toggle('hidden', cat !== '全部' && card.dataset.category !== cat);
      }});
    }});
  }});
}}
bindCatBtns();

// ── 入场动画 stagger ──
document.querySelectorAll('.news-card').forEach((card, i) => {{
  card.style.animationDelay = `${{i * 0.07}}s`;
}});

// ── 历史日报：颜色/图标映射 ──
const CAT_COLORS = {{
  "研究突破":"#f59e0b","行业动态":"#10b981","融资并购":"#ef4444",
  "产品发布":"#3b82f6","政策监管":"#f97316","活动会议":"#ec4899"
}};
const CAT_ICONS = {{
  "全部":"🤖","研究突破":"🔬","行业动态":"📊","融资并购":"💰",
  "产品发布":"🛠","政策监管":"📋","活动会议":"🎪"
}};
const WEEKDAYS = ["周日","周一","周二","周三","周四","周五","周六"];

// ── 今日数据（内嵌静态卡片备份）──
const todayGrid = document.getElementById('newsGrid').innerHTML;
const todayFilterBar = document.querySelector('.filter-bar') ? document.querySelector('.filter-bar').innerHTML : '';
const todaySubtitle = document.querySelector('.subtitle') ? document.querySelector('.subtitle').innerHTML : '';

// ── 加载并渲染历史日报 ──
function renderHistoryArticles(articles, dateStr) {{
  const grid = document.getElementById('newsGrid');
  const weekday = WEEKDAYS[new Date(dateStr).getDay()];

  // 更新副标题
  const sub = document.querySelector('.subtitle');
  if (sub) sub.innerHTML = `<span>${{dateStr}}</span>·<span>${{weekday}}</span>·<span><strong>${{articles.length}}</strong> 条精选</span>`;

  // 生成卡片
  grid.innerHTML = articles.map((a, i) => {{
    const rank = i + 1;
    const rankColor = rank===1?'#ffd700':rank===2?'#c0c0c0':rank===3?'#cd7f32':'#555';
    const color = CAT_COLORS[a.category] || '#8b5cf6';
    const icon = CAT_ICONS[a.category] || '📌';
    const title = (a.title||'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"').replace(/&#8217;/g,"'").replace(/&#8216;/g,"'");
    const summary = (a.chinese_summary || a.summary || '').substring(0, 250);
    const pubDate = (a.published||'').substring(0,10);
    return `<article class="news-card" data-category="${{a.category}}" data-rank="${{rank}}" style="animation-delay:${{i*0.07}}s">
      <div class="card-header">
        <div class="card-meta">
          <span class="rank" style="color:${{rankColor}}">#${{rank}}</span>
          <span class="source-tag" style="background:${{color}}20;color:${{color}}">${{icon}} ${{a.source}}</span>
          <span class="cat-tag" style="background:${{color}}30;color:${{color}}">${{a.category}}</span>
        </div>
      </div>
      <h2 class="card-title"><a href="${{a.url}}" target="_blank" rel="noopener">${{title}}</a></h2>
      <p class="card-summary">${{summary}}</p>
      <div class="card-footer">
        <a class="read-more" href="${{a.url}}" target="_blank" rel="noopener">▶ 阅读原文</a>
        <span class="pub-date">${{pubDate}}</span>
      </div>
    </article>`;
  }}).join('');

  // 重新绑定分类过滤
  bindCatBtns();
  // 重置分类按钮到"全部"
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.cat==='全部'));
}}

// ── 切换回今日 ──
function loadToday() {{
  document.getElementById('newsGrid').innerHTML = todayGrid;
  const sub = document.querySelector('.subtitle');
  if (sub) sub.innerHTML = todaySubtitle;
  document.getElementById('historyBanner').style.display = 'none';
  const sel = document.getElementById('historySelect');
  if (sel) {{ for(let o of sel.options) if(o.dataset.today==='1') o.selected=true; }}
  bindCatBtns();
  document.querySelectorAll('.news-card').forEach((card, i) => {{ card.style.animationDelay = `${{i * 0.07}}s`; }});
}}

// ── 历史下拉响应 ──
function onHistoryChange(sel) {{
  const val = sel.value;
  if (!val || val === 'today') {{ loadToday(); return; }}

  const banner = document.getElementById('historyBanner');
  const label = document.getElementById('historyDateLabel');
  if (banner) banner.style.display = 'block';
  if (label) label.textContent = val;

  const grid = document.getElementById('newsGrid');
  grid.innerHTML = '<div style="text-align:center;padding:3rem;color:#555;">⏳ 加载中...</div>';

  fetch(`history/${{val}}.json`)
    .then(r => {{ if(!r.ok) throw new Error(r.status); return r.json(); }})
    .then(data => {{
      const articles = data.articles || data;
      renderHistoryArticles(articles, val);
    }})
    .catch(err => {{
      grid.innerHTML = `<div style="text-align:center;padding:3rem;color:#ef4444;">❌ 加载失败：${{err.message}}<br><small>history/${{val}}.json</small></div>`;
    }});
}}

// ── 页面加载后动态填充历史下拉 ──
(async function initHistorySelect() {{
  const sel = document.getElementById('historySelect');
  if (!sel) return;

  const today = '{date_str}';
  const weekday = '{weekday}';

  sel.innerHTML = `<option value="today" data-today="1" selected>📅 ${{today}} ${{weekday}}（今天）</option>`;
  sel.onchange = () => onHistoryChange(sel);

  try {{
    const resp = await fetch('history_index.json');
    if (!resp.ok) throw new Error(resp.status);
    const idx = await resp.json();
    const dates = (idx.dates || []).filter(d => d !== today);
    dates.forEach(d => {{
      const opt = document.createElement('option');
      opt.value = d;
      opt.textContent = `📄 ${{d}}`;
      sel.appendChild(opt);
    }});
    if (dates.length === 0) {{
      const opt = document.createElement('option');
      opt.disabled = true;
      opt.textContent = '（暂无更多历史）';
      sel.appendChild(opt);
    }}
  }} catch(e) {{
    const opt = document.createElement('option');
    opt.disabled = true;
    opt.textContent = '（历史索引加载失败）';
    sel.appendChild(opt);
    console.warn('history_index.json load failed:', e);
  }}
}})();
</script>
</body>
</html>"""

if __name__ == "__main__":
    import os, json as j
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "summarized_articles.json"), encoding="utf-8") as f:
        articles = j.load(f)
    generate_html(articles, {})
