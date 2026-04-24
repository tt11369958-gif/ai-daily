# AI 日报自动化技能 (ai-daily)

> 从 66 个中英文媒体（55 个中文微信公众号 + 11 个英文科技/AI 媒体）自动抓取新闻，AI 智能筛选，生成精美暗色卡片 HTML 页面，发布 GitHub Pages 并推送企业微信群。

## 功能流程

```
① RSS 抓取  →  ② LLM 筛选摘要  →  ③ 生成卡片 HTML  →  ④ 发布 GitHub Pages  →  ⑤ 推送企业微信群
```

## 快速开始

### 第一步：安装依赖

```powershell
pip install feedparser requests openai
```

### 第二步：配置

创建或编辑 `config.json`：

```json
{
  "openai_api_key": "你的 API Key",
  "openai_api_base": "https://api.minimaxi.chat/v1",
  "ai_model": "MiniMax-Text-01",
  "github_token": "ghp_xxx",
  "github_user": "你的 GitHub 用户名",
  "github_repo": "ai-daily",
  "wecom_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=626a0387-1734-46e8-9895-5bf60a525ca1"
}
```

> 也支持通过环境变量配置：`OPENAI_API_KEY`、`OPENAI_API_BASE`、`AI_MODEL`、`GITHUB_TOKEN`、`GITHUB_USER`、`GITHUB_REPO`、`WECOM_WEBHOOK`

### 第三步：一键运行

```powershell
cd C:\Users\mi\.workbuddy\skills\ai-daily
python scripts/run.py
```

## 新闻来源（11 个 RSS 源）

| 媒体 | 地址 |
|------|------|
| TechCrunch AI | techcrunch.com |
| The Verge AI | theverge.com |
| VentureBeat AI | venturebeat.com |
| MIT Tech Review | technologyreview.com |
| Wired AI | wired.com |
| Ars Technica | arstechnica.com |
| InfoQ | infoq.com |
| ZDNet AI | zdnet.com |
| Hacker News | news.ycombinator.com |
| Towards Data Science | towardsdatascience.com |
| AI Papers (arXiv) | arxiv.org/cs.AI |

## 输出内容

### HTML 卡片页面特性

- 🌙 **暗色主题**：深色背景，护眼舒适
- 🏷️ **分类标签**：研究突破 / 融资并购 / 产品发布 / 行业动态 / 政策监管 / 活动会议
- 🔍 **实时过滤**：点击分类标签即时筛选
- ✨ **入场动画**：卡片依次淡入，高亮排名
- 📱 **响应式**：完美适配桌面 / 平板 / 手机

### 企业微信群推送效果

```
🤖 AI 日报｜2026-04-14 周二
━━━━━━━━━━━━━━━

🚀 今日头条
重大突破！GPT-5 正式发布，支持百万 Token 上下文...
▶ 阅读原文

📰 今日要闻
> 🔬 谷歌新论文：Scaling Law 失效？[来源: arXiv]...
> 💰 Anthropic 完成 30 亿美元 C 轮融资...
> 🛠 Phi-3 Mini 开源：3.8B 参数超越 GPT-3.5...

━━━━━━━━━━━━━━━
📖 查看完整 AI 日报 →
👉 https://yourname.github.io/ai-daily/
```

## 文件结构

```
ai-daily/
├── config.json              ← API 凭证配置（你的密钥）
├── SKILL.md                 ← 本文档
├── scripts/
│   ├── run.py               ← 🚀 一键运行入口
│   ├── fetch_news.py        ← 步骤①：RSS 抓取
│   ├── summarize.py         ← 步骤②：LLM 筛选摘要
│   ├── generate_html.py     ← 步骤③：生成 HTML
│   ├── publish_github.py    ← 步骤④：GitHub Pages
│   └── notify_wecom.py       ← 步骤⑤：企业微信推送
└── index.html               ← 生成的日报页面
```

## FAQ

**Q: 企微 Webhook 怎么获取？**
> 企业微信群 → 右上角「···」→「添加群机器人」→「新建机器人」→ 复制 Webhook 地址

**Q: GitHub Pages 没权限？**
> 确保 GitHub Token 有 `repo` 和 `pages:write` 权限；在仓库 Settings → Pages → Source 选 `gh-pages` 分支

**Q: 没有 API Key 怎么办？**
> `config.json` 中不填 `openai_api_key`，脚本会尝试读取环境变量 `OPENAI_API_KEY`

**Q: 想指定 LLM 模型？**
> 设置 `AI_MODEL` 环境变量或 `config.json` 中的 `ai_model` 字段

## 设置每日自动运行（Windows 任务计划）

```powershell
# 每天早上 8:30 自动运行
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\mi\.workbuddy\skills\ai-daily\scripts\run.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"
Register-ScheduledTask -TaskName "AI-Daily" -Trigger $trigger -Action $action -Description "AI 日报自动推送"
```

或者在 WorkBuddy 中创建自动化任务（`automation.toml`），每天定时触发。
