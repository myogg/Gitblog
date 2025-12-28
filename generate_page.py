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
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600
ARTICLES_DIR = "articles"

# 初始化 Jinja2
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except Exception:
        return "#000000"

def login():
    if not GITHUB_TOKEN:
        print("❌ 未检测到 G_TT Token")
        exit(1)
    return Github(GITHUB_TOKEN)

def fetch_issues(repo):
    """获取并缓存 Issues"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                ts = datetime.fromisoformat(cache['timestamp'])
                if datetime.now() - ts < timedelta(seconds=CACHE_DURATION):
                    print("✓ 使用缓存 Issues")
                    issues = []
                    for item in cache['issues']:
                        issue = type('Issue', (), {
                            'number': item['number'],
                            'title': item['title'],
                            'body': item['body'],
                            'created_at': datetime.fromisoformat(item['created_at']),
                            'labels': [
                                type('Label', (), {'name': l['name'], 'color': l['color']})()
                                for l in item['labels']
                            ]
                        })()
                        issues.append(issue)
                    return issues
        except Exception as e:
            print(f"⚠️ 缓存读取失败: {e}")

    print("⏳ 从 GitHub 拉取 Issues...")
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]

    cache = {
        'timestamp': datetime.now().isoformat(),
        'issues': [{
            'number': i.number,
            'title': i.title,
            'body': i.body,
            'created_at': i.created_at.isoformat(),
            'labels': [{'name': l.name, 'color': l.color} for l in i.labels]
        } for i in all_issues]
    }

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print("✓ Issues 已缓存")
    return all_issues

def sort_issues(issues):
    """时间流排序（唯一主轴）"""
    return sorted(issues, key=lambda i: i.created_at, reverse=True)

def generate_search_index(issues):
    search_data = []
    for issue in issues:
        clean = re.sub(r'<[^>]+>', '', issue.body or "")
        clean = re.sub(r'\s+', ' ', clean).strip()
        search_data.append({
            'id': issue.number,
            'title': issue.title,
            'content': clean[:500],
            'date': issue.created_at.strftime('%Y-%m-%d'),
            'url': f'articles/article-{issue.number}.html',
            'tags': [l.name for l in issue.labels if l.name.lower() != 'pinned']
        })

    os.makedirs("static", exist_ok=True)
    with open("static/search-index.json", 'w', encoding='utf-8') as f:
        json.dump(search_data, f, ensure_ascii=False, indent=2)

    print("✓ 搜索索引已生成")

def generate_article_page(issue, giscus_config):
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    template = env.get_template('article.html')

    html_content = markdown.markdown(
        issue.body or "暂无内容",
        extensions=['extra', 'codehilite', 'tables', 'fenced_code']
    )

    labels_data = [{
        'name': l.name,
        'color': l.color,
        'text_color': get_text_color(l.color),
        'safe_name': re.sub(r'[^a-zA-Z0-9]', '-', l.name).lower()
    } for l in issue.labels if l.name.lower() != 'pinned']

    output = template.render(
        issue=issue,
        content=html_content,
        labels_data=labels_data,
        YEAR=datetime.now().year,
        giscus_config=giscus_config
    )

    path = os.path.join(ARTICLES_DIR, f"article-{issue.number}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✓ 生成文章 #{issue.number}")

def main():
    print("🚀 生成 GitBlog（时间流首页）")

    g = login()
    repo = g.get_repo(REPO_NAME)
    issues = fetch_issues(repo)

    if not issues:
        print("❌ 未找到 Issues")
        return

    # --- 首页唯一数据源 ---
    all_issues_sorted = sort_issues(list(issues))
    print(f"✓ 首页文章数: {len(all_issues_sorted)}")

    # --- 标签信息（用于 UI） ---
    label_info = {}
    articles_by_year = {}

    for issue in issues:
        year = issue.created_at.strftime('%Y')
        articles_by_year.setdefault(year, []).append(issue)
        for l in issue.labels:
            if l.name.lower() == 'pinned':
                continue
            if l.name not in label_info:
                label_info[l.name] = {
                    'color': l.color,
                    'text_color': get_text_color(l.color),
                    'safe_name': re.sub(r'[^a-zA-Z0-9]', '-', l.name).lower()
                }

    generate_search_index(issues)

    giscus_config = {
        'repo': 'myogg/Gitblog',
        'repo_id': os.getenv('GISCUS_REPO_ID', ''),
        'category': 'Announcements',
        'category_id': os.getenv('GISCUS_CATEGORY_ID', ''),
        'theme': 'light',
        'lang': 'zh-CN'
    }

    print("📝 生成文章页...")
    for issue in issues:
        generate_article_page(issue, giscus_config)

    print("🏠 生成首页...")
    index_template = env.get_template('base.html')
    index_html = index_template.render(
        issues=all_issues_sorted,
        label_info=label_info,
        YEAR=datetime.now().year
    )
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print("📁 复制静态资源...")
    os.makedirs("static", exist_ok=True)
    for f in ["style.css", "script.js"]:
        src = os.path.join("templates", f)
        if os.path.exists(src):
            shutil.copy(src, f"static/{f}")

    print("\n🎉 完成：时间流首页已生成")

if __name__ == "__main__":
    main()
