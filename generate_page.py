import os
import re
import json
import markdown
import shutil
from github import Github
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# --- 配置區 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog" # 確保這是你的倉庫路徑
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600 
ARTICLES_DIR = "articles"

# 初始化 Jinja2 模板引擎
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    """根據背景色亮度決定文字顏色（黑或白），保證標籤可讀性"""
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except: return "#000000"

def login():
    if not GITHUB_TOKEN:
        print("Error: G_TT token not found.")
        exit(1)
    return Github(GITHUB_TOKEN)

# --- 緩存系統 ---
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
            # 模擬 GitHub Issue 對象
            issue = type('CachedIssue', (), {
                "number": item["number"], "title": item["title"], "body": item["body"],
                "created_at": datetime.fromisoformat(item["created_at"]),
                "labels": [type('CachedLabel', (), {"name": l["name"], "color": l["color"]}) for l in item["labels"]],
                "pull_request": False
            })()
            issues.append(issue)
        return issues
    
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    cache_data = [{"number": i.number, "title": i.title, "body": i.body, 
                   "created_at": i.created_at.isoformat(), 
                   "labels": [{"name": l.name, "color": l.color} for l in i.labels]} for i in all_issues]
    save_to_cache(cache_key, cache_data)
    return all_issues

def sort_issues(issue_list):
    """排序邏輯：置頂優先，其次按時間倒序"""
    def sort_key(issue):
        is_pinned = any(l.name.lower() == "pinned" for l in issue.labels)
        return (0 if is_pinned else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

def generate_article_page(issue):
    """生成單篇文章頁面"""
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    template = env.get_template('article.html')
    html_content = markdown.markdown(issue.body or "暫無內容", extensions=['extra', 'codehilite', 'tables'])
    labels_data = [{"name": l.name, "color": l.color, "text_color": get_text_color(l.color)} 
                   for l in issue.labels if l.name.lower() != "pinned"]
    output = template.render(issue=issue, content=html_content, labels_data=labels_data, YEAR=datetime.now().year)
    with open(os.path.join(ARTICLES_DIR, f"article-{issue.number}.html"), "w", encoding="utf-8") as f:
        f.write(output)

def main():
    g = login()
    repo = g.get_repo(REPO_NAME)
    issues = fetch_issues(repo)
    
    # --- 數據整理 ---
    label_dict = {}    # 標籤對應的文章列表
    label_info = {}    # 標籤的顏色與屬性
    articles_by_year = {} # 歸檔數據：按年份分組
    
    # 提取置頂文章
    pinned_issues = sort_issues([i for i in issues if any(l.name.lower() == "pinned" for l in i.labels)])
    
    for issue in issues:
        # 歸檔分組
        year = issue.created_at.strftime('%Y')
        articles_by_year.setdefault(year, []).append(issue)
        
        # 標籤分組
        for label in issue.labels:
            if label.name.lower() == "pinned": continue
            label_dict.setdefault(label.name, []).append(issue)
            if label.name not in label_info:
                label_info[label.name] = {
                    "color": label.color,
                    "text_color": get_text_color(label.color),
                    "safe_name": re.sub(r'[^a-zA-Z0-9]', '-', label.name).lower()
                }

    # 排序各個列表
    for label in label_dict: label_dict[label] = sort_issues(label_dict[label])
    sorted_years = sorted(articles_by_year.keys(), reverse=True)
    for year in sorted_years: articles_by_year[year] = sort_issues(articles_by_year[year])

    # --- 生成單篇文章 ---
    for issue in issues:
        generate_article_page(issue)

    # --- 生成主頁 (index.html) ---
    index_template = env.get_template('base.html')
    index_html = index_template.render(
        pinned_issues=pinned_issues, label_dict=label_dict, 
        label_info=label_info, MAX_PER_CATEGORY=MAX_PER_CATEGORY, YEAR=datetime.now().year
    )
    with open("index.html", "w", encoding="utf-8") as f: f.write(index_html)

    # --- 生成歸檔頁 (archives.html) ---
    # 提示：你需要在 templates 目錄下創建 archives.html 模板
    try:
        archive_template = env.get_template('archives.html')
        archive_html = archive_template.render(
            sorted_years=sorted_years, articles_by_year=articles_by_year,
            label_dict=label_dict, label_info=label_info, YEAR=datetime.now().year
        )
        with open("archives.html", "w", encoding="utf-8") as f: f.write(archive_html)
    except:
        print("Warning: archives.html template not found, skipping archive page generation.")

    # --- 處理靜態資源 ---
    os.makedirs("static", exist_ok=True)
    for src in ["templates/style.css", "style.css"]:
        if os.path.exists(src):
            shutil.copy(src, "static/style.css")
            break
    
    print("🎉 博客與歸檔頁生成完成！")

if __name__ == "__main__":
    main()
