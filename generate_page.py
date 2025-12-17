import os
import re
import json
import time
import hashlib
import markdown
from github import Github
from datetime import datetime, timedelta

# 配置常量
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
ARTICLES_DIR = "articles"
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600
MAX_RECENT = 5
MAX_PER_CATEGORY = 5

def login():
    """GitHub登录"""
    if not GITHUB_TOKEN:
        print("错误: 请设置 G_TT 环境变量")
        exit(1)
    return Github(GITHUB_TOKEN)

def get_repo(g):
    """获取仓库"""
    return g.get_repo(REPO_NAME)

def cache_get(key):
    """获取缓存"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if key in cache:
                data = cache[key]
                cache_time = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
                    return data["data"]
    except Exception:
        pass
    return None

def cache_set(key, data):
    """设置缓存"""
    try:
        cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        cache[key] = {"timestamp": datetime.now().isoformat(), "data": data}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存缓存失败: {e}")

def fetch_issues(repo):
    """获取issues（带缓存）"""
    cache_key = f"issues_{repo.full_name}_open"
    cached = cache_get(cache_key)
    
    if cached:
        print(f"从缓存加载 {len(cached)} 篇文章")
        issues = []
        for item in cached:
            issue = type('CachedIssue', (), {
                "number": item["number"],
                "title": item["title"],
                "html_url": item["html_url"],
                "body": item["body"],
                "created_at": datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                "labels": [type('CachedLabel', (), {"name": label["name"], "color": label.get("color", "ededed")}) for label in item["labels"]],
                "pull_request": item["pull_request"]
            })()
            issues.append(issue)
        return [i for i in issues if not i.pull_request]
    
    print("从GitHub API获取文章数据...")
    try:
        all_issues = []
        for issue in repo.get_issues(state="open"):
            all_issues.append(issue)
            time.sleep(0.1)
        
        issues = [i for i in all_issues if not i.pull_request]
        print(f"成功获取 {len(issues)} 篇文章")
        
        cache_data = []
        for issue in issues:
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "html_url": issue.html_url,
                "body": issue.body,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "labels": [{"name": label.name, "color": label.color} for label in issue.labels],
                "pull_request": issue.pull_request is not None
            }
            cache_data.append(issue_data)
        
        cache_set(cache_key, cache_data)
        return issues
    except Exception as e:
        print(f"获取文章失败: {e}")
        cached = cache_get(cache_key)
        if cached:
            print("API失败，使用过期的缓存数据...")
            issues = []
            for item in cached:
                issue = type('CachedIssue', (), {
                    "number": item["number"],
                    "title": item["title"],
                    "html_url": item["html_url"],
                    "body": item["body"],
                    "created_at": datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                    "labels": [type('CachedLabel', (), {"name": label["name"], "color": label.get("color", "ededed")}) for label in item["labels"]],
                    "pull_request": item["pull_request"]
                })()
                issues.append(issue)
            return [i for i in issues if not i.pull_request]
        return []

def load_template(name):
    """加载模板"""
    path = os.path.join("templates", name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        if name == "article.html":
            return """<!DOCTYPE html><html><head><title>{{TITLE}}</title></head><body>
                <a href="../index.html">← 返回</a><h1>{{TITLE}}</h1>
                <div>{{CONTENT}}</div><p>原文: <a href="{{ORIGINAL_URL}}">{{ORIGINAL_URL}}</a></p>
                </body></html>"""
        return """<!DOCTYPE html><html><body>{{CONTENT}}</body></html>"""

def get_label_color(label_name):
    """获取标签颜色类"""
    hash_num = int(hashlib.md5(label_name.encode()).hexdigest()[:8], 16)
    colors = ["gh-label-1", "gh-label-2", "gh-label-3", "gh-label-4", "gh-label-5"]
    return colors[hash_num % len(colors)]

def sort_issues(issue_list):
    """排序文章：先置顶，再按时间"""
    def sort_key(issue):
        has_pinned = any(label.name.lower() == "pinned" for label in issue.labels)
        return (0 if has_pinned else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

def generate_article_page(issue):
    """生成单篇文章页面"""
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    template = load_template("article.html")
    
    html_content = markdown.markdown(issue.body or "暂无内容", extensions=['extra', 'codehilite', 'tables'])
    
    labels_html = []
    for label in issue.labels:
        if label.name.lower() != "pinned":
            color_class = get_label_color(label.name)
            labels_html.append(f'<span class="tag {color_class}">{label.name}</span> ')
    
    html = template.replace("{{TITLE}}", issue.title)
    html = html.replace("{{NUMBER}}", str(issue.number))
    html = html.replace("{{DATE}}", issue.created_at.strftime("%Y-%m-%d"))
    html = html.replace("{{CONTENT}}", html_content)
    html = html.replace("{{ORIGINAL_URL}}", issue.html_url)
    html = html.replace("{{LABELS}}", "".join(labels_html))
    
    filename = f"article-{issue.number}.html"
    filepath = os.path.join(ARTICLES_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filename

def generate_index_html(issues):
    """生成首页"""
    if not issues:
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # 按标签分类
    label_dict = {}
    for issue in issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)
    
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])
    
    # 获取置顶文章
    pinned_issues = []
    for issue in issues:
        if any(label.name.lower() == "pinned" for label in issue.labels):
            pinned_issues.append(issue)
    pinned_issues = sort_issues(list(set(pinned_issues)))
    
    # 获取最近文章（排除置顶）
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    all_sorted_issues = sort_issues(list(set(all_sorted_issues)))
    pinned_ids = [issue.number for issue in pinned_issues]
    recent_issues = [issue for issue in all_sorted_issues if issue.number not in pinned_ids][:MAX_RECENT]
    
    template = load_template("base.html")
    
    # 生成标签HTML
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        color_class = get_label_color(label)
        tags_html.append(f'<span class="tag {color_class}" data-label="{safe_label}">{label}</span> ')
    
    # 生成置顶文章
    pinned_html = []
    if pinned_issues:
        articles_html = []
        for issue in pinned_issues:
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                <a href="{issue.html_url}" class="github-link">🔗</a>
            </li>''')
        
        pinned_html.append(f'''
        <div class="category-section">
            <h2>置顶文章 ({len(pinned_issues)}篇)</h2>
            <ul class="article-list">{''.join(articles_html)}</ul>
        </div>''')
    
    # 生成最近文章
    recent_html = []
    if recent_issues:
        articles_html = []
        for issue in recent_issues:
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                <a href="{issue.html_url}" class="github-link">🔗</a>
            </li>''')
        
        recent_html.append(f'''
        <div class="category-section">
            <h2>最近文章 (5篇最新文章)</h2>
            <ul class="article-list">{''.join(articles_html)}</ul>
        </div>''')
    
    # 生成分类
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]
        
        articles_html = []
        for issue in visible_items:
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            pin_mark = " 🔖" if any(lbl.name.lower() == "pinned" for lbl in issue.labels) else ""
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")}){pin_mark}</span>
                <a href="{issue.html_url}" class="github-link">🔗</a>
            </li>''')
        
        hidden_html = []
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                article_filename = generate_article_page(issue)
                article_url = f"{ARTICLES_DIR}/{article_filename}"
                hidden_html.append(f'''
                <li>
                    <a href="{article_url}">{issue.title}</a>
                    <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                    <a href="{issue.html_url}" class="github-link">🔗</a>
                </li>''')
            
            show_more = f'''
            <div id="hidden-{category_id}" class="hidden-articles">
                <ul class="article-list">{''.join(hidden_html)}</ul>
            </div>
            <button class="show-more-btn" id="btn-{category_id}">
                顯示更多 ({len(hidden_items)}篇)
            </button>'''
        else:
            show_more = ""
        
        categories_html.append(f'''
        <div class="category-section" data-label="{safe_label}">
            <h2>{label} ({len(items)}篇)</h2>
            <ul class="article-list">{''.join(articles_html)}</ul>
            {show_more}
        </div>''')
    
    # 填充模板
    html = template.replace("{{TAGS}}", "".join(tags_html))
    html = html.replace("{{PINNED_ARTICLES}}", "".join(pinned_html))
    html = html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    html = html.replace("{{CATEGORIES}}", "".join(categories_html))
    html = html.replace("{{YEAR}}", str(datetime.now().year))
    
    return html

def copy_static_files():
    """复制静态文件"""
    os.makedirs("static", exist_ok=True)
    
    css_sources = ["templates/style.css", "static/style.css", "style.css"]
    js_sources = ["templates/script.js", "static/script.js", "script.js"]
    
    for css_source in css_sources:
        if os.path.exists(css_source):
            import shutil
            shutil.copy(css_source, "static/style.css")
            print(f"✅ CSS文件已复制: {css_source}")
            break
    
    for js_source in js_sources:
        if os.path.exists(js_source):
            import shutil
            shutil.copy(js_source, "static/script.js")
            print(f"✅ JS文件已复制: {js_source}")
            break

def main():
    if not GITHUB_TOKEN:
        print("请先设置 G_TT 环境变量")
        return
    
    try:
        g = login()
        repo = get_repo(g)
        print(f"连接仓库: {repo.full_name}")
        
        issues = fetch_issues(repo)
        print(f"处理 {len(issues)} 篇文章")
        
        if not issues:
            print("没有找到文章")
            return
        
        html_text = generate_index_html(issues)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ index.html 已生成")
        
        copy_static_files()
        
        print(f"🎉 博客生成完成！共 {len(issues)} 篇文章")
        print("📁 文章目录: articles/")
        print("🏠 首页: index.html")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
