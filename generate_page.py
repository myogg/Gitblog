import os
import re
import json
import markdown
import shutil
from github import Github
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# --- 配置 (保持與你原來一致) ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600  # 緩存1小時
ARTICLES_DIR = "articles"

# 初始化 Jinja2
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    """計算標籤文字顏色：深色背景配白字，淺色背景配黑字"""
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except: return "#000000"

def login():
    if not GITHUB_TOKEN:
        print("錯誤: 未找到 G_TT Token")
        exit(1)
    return Github(GITHUB_TOKEN)

# --- 緩存邏輯 (保留你原本的高效設計) ---
def get_cached_data(key):
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if key in cache:
                data = cache[key]
                if datetime.now() - datetime.fromisoformat(data["timestamp"]) < timedelta(seconds=CACHE_DURATION):
                    return data["data"]
    except: pass
    return None

def save_to_cache(key, data):
    try:
        cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f: cache = json.load(f)
        cache[key] = {"timestamp": datetime.now().isoformat(), "data": data}
        with open(CACHE_FILE, "w", encoding="utf-8") as f: json.dump(cache, f, ensure_ascii=False, indent=2)
    except: pass

def fetch_issues(repo):
    cache_key = f"issues_{repo.full_name}"
    cached = get_cached_data(cache_key)
    if cached:
        issues = []
        for item in cached:
            issue = type('CachedIssue', (), {
                "number": item["number"], "title": item["title"], "html_url": item["html_url"],
                "body": item["body"], "created_at": datetime.fromisoformat(item["created_at"]),
                "labels": [type('CachedLabel', (), {"name": l["name"], "color": l["color"]}) for l in item["labels"]],
                "pull_request": False
            })()
            issues.append(issue)
        return issues
    
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    cache_data = [{"number": i.number, "title": i.title, "html_url": i.html_url, "body": i.body, 
                   "created_at": i.created_at.isoformat(), "labels": [{"name": l.name, "color": l.color} for l in i.labels]} for i in all_issues]
    save_to_cache(cache_key, cache_data)
    return all_issues

def sort_issues(issue_list):
    def sort_key(issue):
        is_pinned = any(l.name.lower() == "pinned" for l in issue.labels)
        return (0 if is_pinned else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

# --- 生成文章分頁 ---
def generate_article_page(issue):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    template = env.get_template('article.html')
    html_content = markdown.markdown(issue.body or "暫無內容", extensions=['extra', 'codehilite', 'tables'])
    
    labels_data = [{"name": l.name, "color": l.color, "text_color": get_text_color(l.color)} 
                   for l in issue.labels if l.name.lower() != "pinned"]

    output = template.render(issue=issue, content=html_content, labels_data=labels_data, YEAR=datetime.now().year)
    with open(os.path.join(ARTICLES_DIR, f"article-{issue.number}.html"), "w", encoding="utf-8") as f:
        f.write(output)

# --- 生成首頁 ---
def main():
    g = login()
    repo = g.get_repo(REPO_NAME)
    issues = fetch_issues(repo)
    
    label_dict = {}
    label_info = {}
    pinned_issues = sort_issues([i for i in issues if any(l.name.lower() == "pinned" for l in i.labels)])
    
    for issue in issues:
        for label in issue.labels:
            if label.name.lower() == "pinned": continue
            label_dict.setdefault(label.name, []).append(issue)
            if label.name not in label_info:
                label_info[label.name] = {
                    "color": label.color,
                    "text_color": get_text_color(label.color),
                    "safe_name": re.sub(r'[^a-zA-Z0-9]', '-', label.name).lower()
                }

    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])
    
    for issue in issues:
        generate_article_page(issue)

    # 渲染首頁並傳遞 label_dict 給標籤雲使用
    template = env.get_template('base.html')
    index_html = template.render(
        pinned_issues=pinned_issues,
        label_dict=label_dict,
        label_info=label_info,
        MAX_PER_CATEGORY=MAX_PER_CATEGORY,
        YEAR=datetime.now().year
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # 複製靜態文件
    os.makedirs("static", exist_ok=True)
    for src in ["templates/style.css", "style.css"]:
        if os.path.exists(src):
            shutil.copy(src, "static/style.css")
            break
            
    print("🎉 博客生成完成，標籤雲已就緒！")

if __name__ == "__main__":
    main()
