import os
import re
import json
import markdown
from github import Github
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# --- 配置 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600
ARTICLES_DIR = "articles"

# 初始化 Jinja2 (會去 templates 目錄找 base.html 和 article.html)
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    """根據背景色亮度計算文字顏色(黑/白)"""
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except: return "#000000"

# --- 保留你原本的登入和緩存邏輯 ---
def login():
    if not GITHUB_TOKEN: exit(1)
    return Github(GITHUB_TOKEN)

def get_repo(g): return g.get_repo(REPO_NAME)

def fetch_issues(repo):
    """獲取 Issues"""
    return [i for i in repo.get_issues(state="open") if not i.pull_request]

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
    repo = get_repo(g)
    issues = fetch_issues(repo) # 這裡可以換回你帶緩存的 fetch 函數
    
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

    for label in label_dict: label_dict[label] = sort_issues(label_dict[label])
    for issue in issues: generate_article_page(issue)

    # 渲染並保存首頁
    template = env.get_template('base.html')
    index_html = template.render(pinned_issues=pinned_issues, label_dict=label_dict, 
                                label_info=label_info, MAX_PER_CATEGORY=MAX_PER_CATEGORY, YEAR=datetime.now().year)
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(index_html)
    
    # 靜態文件處理
    os.makedirs("static", exist_ok=True)
    import shutil
    if os.path.exists("templates/style.css"):
        shutil.copy("templates/style.css", "static/style.css")
    
    print("🎉 博客生成完成！")

if __name__ == "__main__":
    main()
