import os
import re
import json
import markdown
import shutil
from github import Github
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# --- 配置 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600
ARTICLES_DIR = "articles"

env = Environment(loader=FileSystemLoader("templates"))

# ---------- 工具函数 ----------

def get_text_color(hex_color):
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except Exception:
        return "#000000"

def login():
    if not GITHUB_TOKEN:
        print("❌ G_TT token not found")
        exit(1)
    return Github(GITHUB_TOKEN)

# ---------- 数据获取 ----------

def fetch_issues(repo):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if datetime.now() - datetime.fromisoformat(cache["timestamp"]) < timedelta(seconds=CACHE_DURATION):
                    print("✓ 使用缓存 Issues")
                    issues = []
                    for i in cache["issues"]:
                        issue = type("Issue", (), {
                            "number": i["number"],
                            "title": i["title"],
                            "body": i["body"],
                            "created_at": datetime.fromisoformat(i["created_at"]),
                            "labels": [type("Label", (), l)() for l in i["labels"]],
                        })()
                        issues.append(issue)
                    return issues
        except Exception:
            pass

    print("→ 从 GitHub 拉取 Issues")
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "issues": [{
                "number": i.number,
                "title": i.title,
                "body": i.body,
                "created_at": i.created_at.isoformat(),
                "labels": [{"name": l.name, "color": l.color} for l in i.labels]
            } for i in all_issues]
        }, f, ensure_ascii=False, indent=2)

    return all_issues

def sort_by_time(issues):
    return sorted(issues, key=lambda i: i.created_at, reverse=True)

# ---------- 搜索索引 ----------

def generate_search_index(issues):
    data = []
    for i in issues:
        content = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", i.body or "")).strip()
        data.append({
            "id": i.number,
            "title": i.title,
            "content": content[:500],
            "date": i.created_at.strftime("%Y-%m-%d"),
            "url": f"articles/article-{i.number}.html",
            "tags": [l.name for l in i.labels if l.name.lower() != "pinned"]
        })

    os.makedirs("static", exist_ok=True)
    with open("static/search-index.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✓ 搜索索引生成完成")

# ---------- 文章页 ----------

def generate_article_page(issue):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    template = env.get_template("article.html")

    html = markdown.markdown(
        issue.body or "",
        extensions=["extra", "fenced_code", "tables", "codehilite"]
    )

    labels_data = [{
        "name": l.name,
        "color": l.color,
        "text_color": get_text_color(l.color),
        "safe_name": re.sub(r"[^a-zA-Z0-9]", "-", l.name).lower()
    } for l in issue.labels if l.name.lower() != "pinned"]

    output = template.render(
        issue=issue,
        content=html,
        labels_data=labels_data,
        YEAR=datetime.now().year
    )

    with open(f"{ARTICLES_DIR}/article-{issue.number}.html", "w", encoding="utf-8") as f:
        f.write(output)

# ---------- 主流程 ----------

def main():
    print("🚀 生成 GitBlog")

    g = login()
    repo = g.get_repo(REPO_NAME)

    issues = sort_by_time(fetch_issues(repo))
    print(f"✓ 共 {len(issues)} 篇文章")

    generate_search_index(issues)

    print("→ 生成文章页")
    for i in issues:
        generate_article_page(i)

    print("→ 生成首页（时间流）")
    index = env.get_template("base.html").render(
        issues=issues,
        YEAR=datetime.now().year
    )
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index)

    for page in ["archives", "search", "about"]:
        path = f"templates/{page}.html"
        if os.path.exists(path):
            html = env.get_template(f"{page}.html").render(YEAR=datetime.now().year)
            with open(f"{page}.html", "w", encoding="utf-8") as f:
                f.write(html)

    os.makedirs("static", exist_ok=True)
    for f in ["style.css", "script.js"]:
        src = f"templates/{f}"
        if os.path.exists(src):
            shutil.copy(src, f"static/{f}")

    print("🎉 完成")

if __name__ == "__main__":
    main()
