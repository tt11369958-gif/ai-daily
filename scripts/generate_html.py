"""
generate_html.py — 生成精美的暗色卡片式 HTML 页面（含历史日报功能）
"""

import json, os, re
from datetime import datetime, timedelta

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
    横向日期选择器 + 嵌入式历史 banner，不依赖下拉框。
    """
    today = datetime.now()
    days = []
    for i in range(7):  # 今天 + 过去6天，共7天
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        weekday_short = ["周一","周二","周三","周四","周五","周六","周日"][d.weekday()]
        day_num = date_str[5:]  # MM-DD
        if i == 0:
            tag = "今天"
            cls = "hs-date hs-today active"
        else:
            tag = f"{i}天前" if i <= 7 else ""
            cls = "hs-date"
        days.append(f'''
      <span class="{cls}" data-date="{date_str}" onclick="onDateClick(this)">
        <span class="hs-day">{weekday_short}</span>
        <span class="hs-num">{day_num}</span>
        <span class="hs-tag">{tag}</span>
      </span>''')

    return f'''
  <div class="history-strip-wrap">
    <div class="history-strip" id="historyStrip">
  {chr(10).join(days)}
    </div>
  </div>
  <div id="historyBanner" style="display:none;background:#1a1035;border:1px solid #8b5cf640;border-radius:.75rem;padding:.75rem 1.25rem;margin:.5rem auto;max-width:700px;font-size:.82rem;color:#94a3b8;text-align:center;">
    正在查看历史日报：<strong id="historyDateLabel"></strong>
    &nbsp;·&nbsp;<a href="#" onclick="loadToday();return false;" style="color:#8b5cf6;">← 返回今日</a>
  </div>'''


def _escape_html(text):
    """简单 HTML 实体转义"""
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;"))


def generate_html(articles, config, output_path=None, pages_url="", user="", repo="", token=""):
    print("[generate_html] generating...")

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

    # 卡片（点击打开 AI 总结详情弹窗）
    cards = []
    for i, a in enumerate(articles):
        color = CATEGORY_COLORS.get(a["category"], "#8b5cf6")
        icon = CATEGORY_ICONS.get(a["category"], "📌")
        rank = i + 1
        rank_color = "#ffd700" if rank == 1 else ("#c0c0c0" if rank == 2 else ("#cd7f32" if rank == 3 else "#555"))
        title_text = _escape_html(a.get("title", ""))
        summary_text = _escape_html(a.get("chinese_summary", a.get("summary", ""))[:300])
        article_url = _escape_html(a.get("url", "#"))
        published = _escape_html(a.get("published", "")[:10])
        source_name = _escape_html(a.get("source", ""))
        cat_name = _escape_html(a.get("category", ""))

        cards.append(f'''
        <article class="news-card" data-rank="{rank}" data-idx="{i}" data-category="{cat_name}"
                 onclick="goDetail({i})" style="cursor:pointer">
            <div class="card-header">
                <div class="card-meta">
                    <span class="rank" style="color:{rank_color}">#{rank}</span>
                    <span class="source-tag" style="background:{color}20;color:{color}">{icon} {source_name}</span>
                    <span class="cat-tag" style="background:{color}30;color:{color}">{cat_name}</span>
                </div>
            </div>
            <h2 class="card-title">{title_text}</h2>
            <p class="card-summary">{summary_text}</p>
            <div class="card-footer">
                <span class="read-more">🔬 AI 总结</span>
                <span class="pub-date">{published}</span>
            </div>
        </article>''')

    cards_html = "\n".join(cards)

    # 用 replace() 代替 .format()，彻底避免 {placeholder} 被二次解析
    articles_json = json.dumps(articles, ensure_ascii=False)
    html = (HTML_TEMPLATE
        .replace("{title}", config.get("newspaper_title", "AI 日报"))
        .replace("{date_str}", date_str)
        .replace("{weekday}", weekday)
        .replace("{article_count}", str(len(articles)))
        .replace("{category_nav}", category_nav)
        .replace("{cards_html}", cards_html)
        .replace("{sources_html}", sources_html)
        .replace("{pages_url}", pages_url or "#")
        .replace("{history_nav}", history_nav)
        .replace("{articles_json}", articles_json)
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[generate_html] done: {output_path}")
    return output_path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜{date_str}</title>
<style>
  :root {
    --bg: #0a0a0f;
    --card-bg: #13131c;
    --card-border: #1e1e2e;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --accent: #8b5cf6;
    --accent2: #06b6d4;
  }
  * { margin:0; padding:0; box-sizing:border-box }
  body { font-family:'Inter','PingFang SC','Microsoft YaHei',sans-serif;
         background:var(--bg); color:var(--text);
         min-height:100vh; line-height:1.6 }
  a { color:inherit; text-decoration:none }

    header {
    background:linear-gradient(135deg,#0f0f1a 0%,#1a1035 100%);
    border-bottom:1px solid #2a2a4a;
    padding:2.5rem 1.5rem 1.5rem;
    text-align:center;
    position:sticky;top:0;z-index:100;
    max-width:100%;
    overflow:hidden;
  }
  .header-badge {
    display:inline-block;
    background:linear-gradient(135deg,#8b5cf6,#06b6d4);
    color:#fff;font-size:.7rem;font-weight:700;
    padding:.25rem .75rem;border-radius:2rem;
    letter-spacing:.05em;margin-bottom:.75rem;
  }
  h1 { font-size:2rem;font-weight:800;letter-spacing:-.02em;margin-bottom:.25rem }
  .subtitle { color:var(--text-dim);font-size:.9rem }
  .subtitle span { margin:0 .5rem }

  /* ── 横滑日期选择器 ── */
  .history-strip-wrap {
    overflow-x:auto;white-space:nowrap;
    scrollbar-width:none;-ms-overflow-style:none;
    margin-bottom:.25rem;
    -webkit-overflow-scrolling: touch;
    width:100%;
  }
  .history-strip-wrap::-webkit-scrollbar { display:none }
  .history-strip {
    display:inline-flex;gap:.4rem;
    padding:.25rem .5rem;
    width:max-content;
    min-width:100%;
  }
  .hs-date {
    display:inline-flex;flex-direction:column;align-items:center;
    background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
    border-radius:.75rem;padding:.4rem .65rem;cursor:pointer;
    transition:all .2s ease;user-select:none;
    -webkit-tap-highlight-color:transparent;
  }
  .hs-date.active {
    background:linear-gradient(135deg,#8b5cf6,#06b6d4);border-color:transparent;
    color:#fff;
  }
  .hs-day { font-size:.65rem;color:var(--text-dim);margin-bottom:.1rem }
  .hs-date.active .hs-day { color:rgba(255,255,255,.8) }
  .hs-num { font-size:.82rem;font-weight:700 }
  .hs-date .hs-tag { font-size:.6rem;color:var(--text-dim);margin-top:.1rem }
  .hs-date.active .hs-tag { color:rgba(255,255,255,.7) }
  .hs-date .hs-num { font-size:.82rem;font-weight:700 }
  .hs-date .hs-tag { font-size:.6rem;color:var(--text-dim);margin-top:.1rem }
  .hs-date.active .hs-tag { color:rgba(255,255,255,.8) }

  .filter-bar {
    display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;
    padding:1.25rem 2rem;background:#0d0d18;
    border-bottom:1px solid #1e1e2e;
    position:sticky;top:85px;z-index:99;
  }
  .cat-btn {
    background:#1a1a2e;border:1px solid #2a2a4a;color:var(--text-dim);
    padding:.4rem 1rem;border-radius:.5rem;cursor:pointer;
    font-size:.82rem;transition:all .2s;
  }
  .cat-btn:hover { border-color:var(--accent);color:var(--accent) }
  .cat-btn.active { background:var(--accent);color:#fff;border-color:var(--accent) }

  main { max-width:900px;margin:0 auto;padding:2rem 1.5rem }

  .news-grid {
    display:grid;grid-template-columns:1fr;
    gap:1rem;
  }
  @media(min-width:640px) {
    .news-grid { grid-template-columns:repeat(2,1fr) }
  }

  .news-card {
    background:var(--card-bg);border:1px solid var(--card-border);
    border-radius:.875rem;padding:1.25rem;
    transition:transform .25s,border-color .25s,box-shadow .25s;
    animation:fadeIn .5s ease backwards;
  }
  .news-card:hover {
    transform:translateY(-3px);border-color:var(--accent);
    box-shadow:0 8px 32px #8b5cf620;
  }
  .card-header { display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem }
  .rank { font-size:.75rem;font-weight:800 }
  .source-tag,.cat-tag {
    font-size:.68rem;padding:.15rem .5rem;border-radius:.25rem;font-weight:600
  }
  .cat-tag { opacity:.85 }
  .card-title { font-size:.95rem;font-weight:700;line-height:1.4;margin-bottom:.75rem }
  .card-summary {
    font-size:.82rem;color:var(--text-dim);line-height:1.65;
    display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden
  }
  .card-footer {
    display:flex;justify-content:space-between;align-items:center;
    margin-top:1rem;padding-top:.75rem;border-top:1px solid #1e1e2e
  }
  .read-more { font-size:.78rem;color:var(--accent);font-weight:600 }
  .pub-date { font-size:.72rem;color:#555 }

  footer {
    text-align:center;padding:3rem 2rem;
    color:#555;font-size:.78rem;
    border-top:1px solid #1a1a2e;margin-top:3rem
  }
  footer a { color:var(--accent) }

  .sources-section { margin-top:1.25rem;padding-top:1rem;border-top:1px solid #1a1a2e }
  .sources-label { font-size:.72rem;color:#444;margin-bottom:.3rem }
  .sources-list { font-size:.75rem;color:#555;line-height:1.8 }

  .hidden { display:none !important }

  @keyframes fadeIn {
    from{opacity:0;transform:translateY(12px)}
    to{opacity:1;transform:translateY(0)}
  }

  .stats-bar {
    display:flex;justify-content:center;gap:2rem;
    padding:1rem;font-size:.8rem;color:var(--text-dim)
  }
  .stats-bar strong { color:var(--accent) }
</style>
</head>
<body>

<header>
  <div class="header-badge">🤖 每日 AI 资讯精选</div>
  <h1>{title}</h1>
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
// ── 颜色/图标映射 ──
const CAT_COLORS = {
  "研究突破":"#f59e0b","行业动态":"#10b981","融资并购":"#ef4444",
  "产品发布":"#3b82f6","政策监管":"#f97316","活动会议":"#ec4899"
};
const CAT_ICONS = {
  "研究突破":"🔬","行业动态":"📊","融资并购":"💰",
  "产品发布":"🛠","政策监管":"📋","活动会议":"🎪"
};
const WEEKDAYS = ["周日","周一","周二","周三","周四","周五","周六"];

// 修复：YYYY-MM-DD 按本地时区解析，避免 UTC 偏移导致 weekday 错位
function getWeekday(dateStr) {
  const [y,m,d] = dateStr.split('-').map(Number);
  return WEEKDAYS[new Date(y, m-1, d).getDay()];
}

// ── 文章数据（Python 注入）──
const ARTICLES = {articles_json};

// ── 今日文章点击 → 跳转详情页 ──
function goDetail(idx) {
  sessionStorage.setItem('ai_articles', JSON.stringify(ARTICLES));
  sessionStorage.setItem('ai_date', '{date_str}');
  window.location.href = `detail.html?idx=${idx}`;
}

// ── 历史文章点击 → 跳转详情页 ──
function goDetailFromEl(el) {
  try {
    const raw = el.getAttribute('data-json');
    if (!raw) return;
    const a = JSON.parse(raw.replace(/&quot;/g, '"'));
    const rank = parseInt(el.dataset.rank, 10) || 1;
    const date = el.dataset.date || '{date_str}';
    // 历史文章存单条
    sessionStorage.setItem('ai_detail_single', JSON.stringify({article: a, rank, date}));
    window.location.href = `detail.html?single=1`;
  } catch(e) { console.error('goDetailFromEl:', e); }
}

// ── 分类过滤 ──
function bindCatBtns() {
  const btns = document.querySelectorAll('.cat-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      document.querySelectorAll('#newsGrid .news-card').forEach(card => {
        if (cat === '全部') {
          card.classList.remove('hidden');
        } else {
          if (card.dataset.category === cat) {
            card.classList.remove('hidden');
          } else {
            card.classList.add('hidden');
          }
        }
      });
    });
  });
}
bindCatBtns();

// ── 入场动画 stagger ──
document.querySelectorAll('#newsGrid .news-card').forEach((card, i) => {
  card.style.animationDelay = `${i * 0.07}s`;
});

// ── 今日数据备份 ──
const todayGrid = document.getElementById('newsGrid').innerHTML;
const todaySubtitle = document.querySelector('.subtitle') ? document.querySelector('.subtitle').innerHTML : '';

// ── 切换回今日 ──
function loadToday() {
  document.getElementById('newsGrid').innerHTML = todayGrid;
  const sub = document.querySelector('.subtitle');
  if (sub) sub.innerHTML = todaySubtitle;
  document.getElementById('historyBanner').style.display = 'none';
  document.querySelectorAll('.hs-date').forEach(d => d.classList.remove('active'));
  const todayEl = document.querySelector('.hs-today');
  if (todayEl) todayEl.classList.add('active');
  bindCatBtns();
  document.querySelectorAll('#newsGrid .news-card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.07}s`;
  });
}

// ── 横滑日期：点击加载历史 ──
async function onDateClick(el) {
  const date = el.dataset.date;
  if (!date || el.classList.contains('loading')) return;
  if (el.classList.contains('active')) return;

  document.querySelectorAll('.hs-date').forEach(d => d.classList.remove('active'));
  el.classList.add('active');

  if (el.classList.contains('hs-today')) { loadToday(); return; }

  el.classList.add('loading');
  const banner = document.getElementById('historyBanner');
  const label = document.getElementById('historyDateLabel');
  if (banner) banner.style.display = 'block';
  if (label) label.textContent = date;

  const grid = document.getElementById('newsGrid');
  grid.innerHTML = '<div style="text-align:center;padding:3rem;color:#555;">⏳ 加载中...</div>';

  try {
    const resp = await fetch(`history/${date}.json`);
    if (!resp.ok) throw new Error(resp.status);
    const data = await resp.json();
    renderHistoryArticles(data.articles || data, date);
  } catch(err) {
    grid.innerHTML = `<div style="text-align:center;padding:3rem;color:#ef4444;">❌ 加载失败：${err.message}</div>`;
  } finally {
    el.classList.remove('loading');
  }
}

// ── 渲染历史文章 ──
function renderHistoryArticles(articles, dateStr) {
  const grid = document.getElementById('newsGrid');
  const weekday = getWeekday(dateStr);
  const sub = document.querySelector('.subtitle');
  if (sub) sub.innerHTML = `<span>${dateStr}</span>·<span>${weekday}</span>·<span><strong>${articles.length}</strong> 条精选</span>`;

  grid.innerHTML = articles.map((a, i) => {
    const rank = i + 1;
    const rankColor = rank===1?'#ffd700':rank===2?'#c0c0c0':rank===3?'#cd7f32':'#555';
    const color = CAT_COLORS[a.category] || '#8b5cf6';
    const icon = CAT_ICONS[a.category] || '📌';
    const title = (a.title||'').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"');
    const summary = (a.chinese_summary || a.summary || '').substring(0, 250);
    const pubDate = (a.published||'').substring(0,10);
    const safeJson = JSON.stringify(a).replace(/"/g, '&quot;');
    return `<article class="news-card" data-rank="${rank}" data-category="${a.category}" data-json="${safeJson}" data-date="${dateStr}"
      onclick="goDetailFromEl(this)" style="animation-delay:${i*0.07}s;cursor:pointer">
      <div class="card-header"><div class="card-meta">
        <span class="rank" style="color:${rankColor}">#${rank}</span>
        <span class="source-tag" style="background:${color}20;color:${color}">${icon} ${a.source}</span>
        <span class="cat-tag" style="background:${color}30;color:${color}">${a.category}</span>
      </div></div>
      <h2 class="card-title">${title}</h2>
      <p class="card-summary">${summary}</p>
      <div class="card-footer">
        <span class="read-more">🔬 AI 总结</span>
        <span class="pub-date">${pubDate}</span>
      </div>
    </article>`;
  }).join('');

  bindCatBtns();
}

// ── 初始化：从 history_index.json 补充历史日期（最多 6 个）──
(async function initHistoryStrip() {
  const stripWrap = document.getElementById('historyStrip') ? document.getElementById('historyStrip').parentElement : null;
  const strip = document.getElementById('historyStrip');
  if (!strip) return;

  // 触摸滑动时不触发页面滚动
  if (stripWrap) {
    stripWrap.addEventListener('touchstart', function(e) {
      this._startX = e.touches[0].clientX;
    }, {passive: true});
    stripWrap.addEventListener('touchmove', function(e) {
      if (Math.abs(e.touches[0].clientX - (this._startX || 0)) > 5) {
        e.preventDefault();
      }
    }, {passive: false});
  }

  const today = '{date_str}';
  try {
    const resp = await fetch('history_index.json');
    if (!resp.ok) return;
    const idx = await resp.json();
    const dates = (idx.dates || []).filter(d => d !== today);
    dates.slice(0, 6).forEach(d => {
      const wd = getWeekday(d);
      const short = d.substring(5);
      const el = document.createElement('span');
      el.className = 'hs-date';
      el.dataset.date = d;
      el.onclick = function() { onDateClick(this); };
      el.innerHTML = `<span class="hs-day">${wd}</span><span class="hs-num">${short}</span>`;
      strip.appendChild(el);
    });
  } catch(e) {
    console.warn('history_index.json load failed:', e);
  }
})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    import os, json as j
    base = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(base, "summarized_articles.json"), encoding="utf-8") as f:
        articles = j.load(f)
    generate_html(articles, {})