"""
publish_github.py — 创建/更新 ai-daily 仓库，推送到 gh-pages，启用 GitHub Pages
同时保存历史日报 JSON 到 history/ 目录，生成并上传每日封面图
"""
import os, json, base64, requests, time
from datetime import datetime

GITHUB_API = "https://api.github.com"

def load_config():
    base = os.path.dirname(os.path.dirname(__file__))
    for fname in ["config.json", "config.example.json"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return {}

def get(cfg, *keys, default=""):
    for k in keys:
        if isinstance(cfg, dict):
            cfg = cfg.get(k, default)
        else:
            return default
    return cfg if cfg else default

def github_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }

def ensure_repo(token, user, repo):
    h = github_headers(token)
    r = requests.get(f"{GITHUB_API}/repos/{user}/{repo}", headers=h, timeout=15)
    if r.status_code == 200:
        print(f"  ✓ 仓库 {user}/{repo} 已存在")
        return True
    if r.status_code == 404:
        print(f"  → 仓库不存在，正在创建 {user}/{repo} ...")
        r = requests.post(
            f"{GITHUB_API}/user/repos", headers=h,
            json={
                "name": repo, "description": "🤖 AI Daily — 每日 AI 资讯精选与中文摘要",
                "homepage": f"https://{user}.github.io/{repo}/",
                "private": False, "has_issues": True, "has_wiki": False, "auto_init": True
            }, timeout=15
        )
        if r.status_code in (200, 201):
            print(f"  ✓ 仓库创建成功")
            time.sleep(2)
            return True
        else:
            print(f"  ✗ 仓库创建失败: {r.status_code} {r.text}")
            return False
    print(f"  ✗ 无法访问仓库: {r.status_code} {r.text}")
    return False

def enable_pages(token, user, repo):
    h = github_headers(token)
    r = requests.get(f"{GITHUB_API}/repos/{user}/{repo}/pages", headers=h, timeout=15)
    if r.status_code == 200:
        status = r.json().get("status", "")
        if status in ("built", "building"):
            print(f"  ✓ GitHub Pages 已启用 ({status})")
            return True

    r = requests.post(
        f"{GITHUB_API}/repos/{user}/{repo}/pages", headers=h,
        json={"build_type": "deployment", "source": {"branch": "gh-pages", "path": "/"}},
        timeout=15
    )
    if r.status_code in (200, 201, 204):
        print(f"  ✓ GitHub Pages 启用成功（等待 30 秒生效）")
        time.sleep(30)
        return True
    if r.status_code == 409:
        print(f"  ✓ GitHub Pages 可能已配置，跳过")
        return True
    print(f"  ⚠ GitHub Pages 启用: {r.status_code} {r.text[:100]}")
    return True

def _upload_file(api_base, h, path, content_b64, message, branch="gh-pages"):
    """通用文件上传/更新方法"""
    payload = {"message": message, "content": content_b64, "branch": branch}
    try:
        r = requests.get(f"{api_base}/contents/{path}", headers=h, params={"ref": branch}, timeout=15)
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
    except Exception:
        pass
    r = requests.put(f"{api_base}/contents/{path}", headers=h, json=payload, timeout=30)
    return r

def _save_history(articles, user, repo, h, api_base):
    """保存历史日报 JSON + 更新索引（索引放根目录 history_index.json）"""
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = f"history/{today}.json"
    index_file = "history_index.json"          # 根目录，HTML 直接 fetch

    # 1. 存当天日报
    article_data = json.dumps({"date": today, "articles": articles}, ensure_ascii=False, indent=2)
    content_b64 = base64.b64encode(article_data.encode("utf-8")).decode("ascii")
    r = _upload_file(api_base, h, history_file, content_b64,
                     f"📰 AI 日报存档 {today}")
    if r.status_code in (200, 201):
        print(f"  ✓ 历史日报已存档: {history_file}")
    else:
        print(f"  ⚠ 历史存档失败: {r.status_code} {r.text[:100]}")

    # 2. 读现有索引，合并所有历史日期
    dates = []
    try:
        # 先尝试根目录
        r_idx = requests.get(f"{api_base}/contents/{index_file}",
                             headers=h, params={"ref": "gh-pages"}, timeout=15)
        if r_idx.status_code == 200:
            raw = base64.b64decode(r_idx.json()["content"]).decode("utf-8")
            dates = json.loads(raw).get("dates", [])
        else:
            # 兼容旧版：尝试读 history/history_index.json，把里面的 dates 迁移过来
            r_old = requests.get(f"{api_base}/contents/history/history_index.json",
                                 headers=h, params={"ref": "gh-pages"}, timeout=15)
            if r_old.status_code == 200:
                raw = base64.b64decode(r_old.json()["content"]).decode("utf-8")
                dates = json.loads(raw).get("dates", [])
                print("  → 已从旧路径迁移历史索引")
    except Exception as e:
        print(f"  ⚠ 读取历史索引异常: {e}")

    # 3. 自动扫描 history/ 目录，补全所有已有的日期（防止遗漏）
    try:
        r_dir = requests.get(f"{api_base}/contents/history",
                             headers=h, params={"ref": "gh-pages"}, timeout=15)
        if r_dir.status_code == 200:
            for item in r_dir.json():
                name = item.get("name", "")
                if name.endswith(".json") and name != "history_index.json":
                    d = name.replace(".json", "")
                    if d not in dates:
                        dates.append(d)
    except Exception as e:
        print(f"  ⚠ 扫描历史目录异常: {e}")

    # 4. 确保今天在列表里，按日期倒序排列
    if today not in dates:
        dates.append(today)
    dates = sorted(set(dates), reverse=True)

    # 5. 写回根目录 history_index.json
    index_data = json.dumps({"updated": datetime.now().isoformat(), "dates": dates},
                            ensure_ascii=False, indent=2)
    r = _upload_file(api_base, h, index_file,
                     base64.b64encode(index_data.encode("utf-8")).decode("ascii"),
                     "更新历史索引")
    if r.status_code in (200, 201):
        print(f"  ✓ 历史索引已更新，共 {len(dates)} 天存档: {dates}")

def _generate_and_upload_cover(articles, config, api_base, h, user, repo):
    """
    生成每日 AI 封面图并上传到 GitHub，返回图片 URL。
    使用 Pollinations.ai 免费图片 API（无需 key），基于当日头条生成不同图片。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    # 根据当日头条生成图片主题词
    headline = articles[0] if articles else {}
    category = headline.get("category", "AI")
    title = headline.get("title", "AI News")[:40]

    # 构造 Pollinations 图片 URL（每天关键词不同，图片自动变化）
    import urllib.parse
    prompt_map = {
        "研究突破": "futuristic AI research lab, neural network visualization, glowing blue circuits",
        "产品发布": "sleek AI product launch, holographic interface, modern tech design",
        "融资并购": "fintech AI, digital economy, global network connections",
        "政策监管": "AI governance, digital law, balanced scales with circuit boards",
        "行业动态": "AI industry trends, data visualization, dynamic infographic",
    }
    base_prompt = prompt_map.get(category, "artificial intelligence daily news, futuristic technology")
    full_prompt = f"{base_prompt}, date {today}, cinematic, 4k, dark theme, purple glow"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = int(today.replace("-", "")) % 10000  # 每天不同的 seed

    cover_url_remote = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1200&height=600&nologo=true"

    print(f"  → 正在下载封面图（{category}）...")
    try:
        img_resp = requests.get(cover_url_remote, timeout=30)
        if img_resp.status_code == 200 and len(img_resp.content) > 1000:
            img_b64 = base64.b64encode(img_resp.content).decode("ascii")
            cover_path = f"assets/cover-{today}.png"
            r = _upload_file(api_base, h, cover_path, img_b64, f"🖼️ 封面图 {today}")
            if r.status_code in (200, 201):
                cover_gh_url = f"https://{user}.github.io/{repo}/{cover_path}"
                print(f"  ✓ 封面图已上传: {cover_gh_url}")
                return cover_gh_url
            else:
                print(f"  ⚠ 封面图上传失败: {r.status_code}")
        else:
            print(f"  ⚠ 封面图下载失败，状态码: {img_resp.status_code}")
    except Exception as e:
        print(f"  ⚠ 封面图生成/上传异常: {e}")

    # fallback：返回默认封面
    return f"https://{user}.github.io/{repo}/assets/cover.png"


def publish(html_path=None, articles=None):
    config = load_config()
    token = os.environ.get("GITHUB_TOKEN") or get(config, "github", "token", default="") or \
            get(config, "llm", "api_key", default="")
    user  = os.environ.get("GITHUB_USER") or get(config, "github", "user", default="")
    repo  = os.environ.get("GITHUB_REPO") or get(config, "github", "repo", default="ai-daily")

    if not token:
        print("⚠ 未配置 GitHub Token，跳过发布")
        return "", ""
    if not user:
        print("⚠ 未配置 GitHub 用户名，跳过发布")
        return "", ""

    if html_path is None:
        base = os.path.dirname(os.path.dirname(__file__))
        html_path = os.path.join(base, "index.html")

    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    h = github_headers(token)
    api_base = f"{GITHUB_API}/repos/{user}/{repo}"

    print(f"  → 用户: {user}, 仓库: {repo}")
    print(f"  → Token 前缀: {token[:8]}...")

    if not ensure_repo(token, user, repo):
        return "", ""

    print(f"  → 请求仓库信息: {api_base}")
    repo_r = requests.get(f"{api_base}", headers=h, timeout=15)
    default_branch = "main"
    if repo_r.status_code == 200:
        default_branch = repo_r.json().get("default_branch", "main")
    print(f"  → 默认分支: {default_branch}")

    branch_r = requests.get(f"{api_base}/branches/{default_branch}", headers=h, timeout=15)
    if branch_r.status_code == 200:
        sha = branch_r.json()["commit"]["sha"]
        print(f"  ✓ 获取默认分支 SHA 成功")
    else:
        ref_r = requests.get(f"{api_base}/git/refs/heads/{default_branch}", headers=h, timeout=15)
        if ref_r.status_code == 200:
            sha = ref_r.json()["object"]["sha"]
            print(f"  ✓ 通过 refs 获取 SHA 成功")
        else:
            print(f"  → 空仓库，创建初始文件...")
            blob_r = requests.post(f"{api_base}/git/blobs", headers=h,
                                   json={"content": "# ai-daily\n", "encoding": "utf-8"}, timeout=15)
            blob_sha = blob_r.json().get("sha", "") if blob_r.status_code == 201 else ""
            tree_payload = [{"path": "README.md", "mode": "100644", "type": "blob", "sha": blob_sha}] if blob_sha else []
            tree_r = requests.post(f"{api_base}/git/trees", headers=h, json={"tree": tree_payload}, timeout=15)
            tree_sha = tree_r.json().get("sha", "") if tree_r.status_code == 201 else ""
            commit_r = requests.post(f"{api_base}/git/commits", headers=h,
                                     json={"message": "Initial commit", "tree": tree_sha} if tree_sha else {"message": "Initial commit"},
                                     timeout=15)
            sha = commit_r.json().get("sha", "") if commit_r.status_code in (200, 201) else ""
            if not sha:
                print(f"✗ 无法创建初始 commit")
                return "", ""
            requests.post(f"{api_base}/git/refs", headers=h,
                           json={"ref": f"refs/heads/{default_branch}", "sha": sha}, timeout=15)
            print(f"  ✓ 已创建 {default_branch} 分支")

    # 确保 gh-pages 分支存在
    branch_check = requests.get(f"{api_base}/branches/gh-pages", headers=h, timeout=15)
    if branch_check.status_code == 200:
        print(f"  ✓ gh-pages 分支已存在")
    else:
        print(f"  → 创建 gh-pages 分支...")
        ref_r = requests.post(f"{api_base}/git/refs", headers=h,
                               json={"ref": "refs/heads/gh-pages", "sha": sha}, timeout=15)
        if ref_r.status_code in (200, 201):
            print(f"  ✓ gh-pages 分支创建成功")
        else:
            print(f"  ✗ 分支创建失败: {ref_r.status_code}")
            return "", ""

    # 推送 index.html + article.html
    commit_msg = f"🤖 AI 日报 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # index.html
    content_b64 = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
    payload_json = {"message": commit_msg, "content": content_b64, "branch": "gh-pages"}
    existing = requests.get(f"{api_base}/contents/index.html", headers=h, params={"ref": "gh-pages"}, timeout=15)
    if existing.status_code == 200:
        payload_json["sha"] = existing.json()["sha"]
        print(f"  → 获取现有文件 SHA 成功")

    file_r = requests.put(f"{api_base}/contents/index.html", headers=h, json=payload_json, timeout=30)
    if file_r.status_code in (200, 201):
        print(f"  ✓ index.html 已推送至 gh-pages")
    else:
        print(f"  ✗ index.html 推送失败: {file_r.status_code} {file_r.text[:100]}")
        return "", ""

    # article.html（详情页）
    article_path = os.path.join(os.path.dirname(html_path), "article.html")
    if os.path.exists(article_path):
        with open(article_path, encoding="utf-8") as f:
            article_content = f.read()
        art_payload = {
            "message": "📄 添加文章详情页",
            "content": base64.b64encode(article_content.encode("utf-8")).decode("ascii"),
            "branch": "gh-pages"
        }
        existing_art = requests.get(f"{api_base}/contents/article.html", headers=h, params={"ref": "gh-pages"}, timeout=15)
        if existing_art.status_code == 200:
            art_payload["sha"] = existing_art.json()["sha"]
        art_r = requests.put(f"{api_base}/contents/article.html", headers=h, json=art_payload, timeout=30)
        if art_r.status_code in (200, 201):
            print(f"  ✓ article.html 已推送至 gh-pages")
        else:
            print(f"  ⚠ article.html 推送失败: {art_r.status_code}")
    else:
        print(f"  ⚠ article.html 不存在，跳过")

    # 启用 Pages
    enable_pages(token, user, repo)

    # 生成并上传每日封面图
    cover_url = f"https://{user}.github.io/{repo}/assets/cover.png"  # 默认值
    if articles:
        cover_url = _generate_and_upload_cover(articles, {}, api_base, h, user, repo)

    # 保存历史日报
    if articles:
        _save_history(articles, user, repo, h, api_base)

    pages_url = f"https://{user}.github.io/{repo}/"
    print(f"\n✅ 已发布: {pages_url}")
    print(f"🖼️  封面图: {cover_url}")
    return pages_url, cover_url

if __name__ == "__main__":
    result = publish()
    if result[0]:
        print(f"访问地址: {result[0]}")
