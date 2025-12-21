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
REPO_NAME = "myogg/Gitblog" 
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600 
ARTICLES_DIR = "articles"

# 初始化 Jinja2 模板引擎
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    """根據背景色亮度決定文字顏色"""
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

def fetch_issues(repo):
    """獲取並緩存 Issues"""
    # ... (緩存邏輯保持不變，同您上傳的代碼) ...
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    return all_issues

def sort_issues(issue_list):
    def sort_key(issue):
        is_pinned = any(l.name.lower() == "pinned" for l in issue.labels)
        return (0 if is_pinned else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

def generate_article_page(issue):
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
    label_dict = {}    
    label_info = {}    
    articles_by_year = {} 
    
    # 1. 處理置頂文章
    pinned_issues = sort_issues([i for i in issues if any(l.name.lower() == "pinned" for l in i.labels)])
    pinned_ids = {i.number for i in pinned_issues}

    # 2. 處理最近文章 (排除置頂)
    all_sorted_issues = sort_issues(list(issues))
    recent_issues = [i for i in all_sorted_issues if i.number not in pinned_ids][:5]
    
    for issue in issues:
        year = issue.created_at.strftime('%Y')
        articles_by_year.setdefault(year, []).append(issue)
        for label in issue.labels:
            if label.name.lower() == "pinned": continue
            label_dict.setdefault(label.name, []).append(issue)
            if label.name not in label_info:
                label_info[label.name] = {
                    "color": label.color,
                    "text_color": get_text_color(label.color),
                    "safe_name": re.sub(r'[^a-zA-Z0-9]', '-', label.name).lower()
                }

    for label in label_dict: label_dict[label] = sort_issues(label_dict[label])
    sorted_years = sorted(articles_by_year.keys(), reverse=True)

    # --- 生成頁面 ---
    for issue in issues:
        generate_article_page(issue)

    # 1. 生成主頁
    index_template = env.get_template('base.html')
    index_html = index_template.render(
        pinned_issues=pinned_issues, 
        recent_issues=recent_issues,  # 必須傳入這個
        label_dict=label_dict, 
        label_info=label_info, 
        MAX_PER_CATEGORY=MAX_PER_CATEGORY, 
        YEAR=datetime.now().year
    )
    with open("index.html", "w", encoding="utf-8") as f: f.write(index_html)

    # 2. 生成歸檔頁
    try:
        archive_template = env.get_template('archives.html')
        archive_html = archive_template.render(
            sorted_years=sorted_years, articles_by_year=articles_by_year,
            label_dict=label_dict, label_info=label_info, YEAR=datetime.now().year
        )
        with open("archives.html", "w", encoding="utf-8") as f: f.write(archive_html)
    except: pass

    # 3. 生成關於頁
    try:
        about_template = env.get_template('about.html')
        about_html = about_template.render(YEAR=datetime.now().year)
        with open("about.html", "w", encoding="utf-8") as f: f.write(about_html)
    except: pass

    # 複製靜態資源
    os.makedirs("static", exist_ok=True)
    for f in ["style.css", "script.js"]:
        src = os.path.join("templates", f)
        if os.path.exists(src): shutil.copy(src, f"static/{f}")

    print("🎉 任務完成！")

if __name__ == "__main__":
    main()
