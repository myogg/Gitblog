import os
import re
import json
import time
import hashlib
import markdown
from github import Github
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"

MAX_RECENT = 5
MAX_PER_CATEGORY = 5

# 缓存配置
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600  # 缓存1小时（3600秒）

# 文章目录
ARTICLES_DIR = "articles"

def login():
    if not GITHUB_TOKEN:
        print("错误: 请设置 G_TT 环境变量")
        print("使用方法: export G_TT='你的github_token'")
        exit(1)
    return Github(GITHUB_TOKEN)

def get_repo(g):
    return g.get_repo(REPO_NAME)

def get_cached_data(key):
    """从缓存读取数据"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            
            if key in cache:
                data = cache[key]
                cache_time = datetime.fromisoformat(data["timestamp"])
                
                # 检查缓存是否过期
                if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
                    print(f"使用缓存数据: {key}")
                    return data["data"]
    except Exception as e:
        print(f"读取缓存失败: {e}")
    return None

def save_to_cache(key, data):
    """保存数据到缓存"""
    try:
        cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        
        cache[key] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        print(f"已缓存: {key}")
    except Exception as e:
        print(f"保存缓存失败: {e}")

def fetch_issues_with_cache(repo):
    """带缓存的获取issues函数"""
    cache_key = f"issues_{repo.full_name}_open"
    
    # 尝试从缓存读取
    cached = get_cached_data(cache_key)
    if cached is not None:
        print(f"从缓存加载 {len(cached)} 篇文章")
        # 将缓存的字典数据转换回对象
        issues = []
        for item in cached:
            # 创建简化的issue对象
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
        return issues
    
    # 从GitHub API获取
    print("从GitHub API获取文章数据...")
    try:
        all_issues = []
        # 分批获取，避免单次请求太大
        for issue in repo.get_issues(state="open"):
            all_issues.append(issue)
            time.sleep(0.1)  # 每个请求间隔0.1秒，避免速率限制
        
        print(f"成功获取 {len(all_issues)} 篇文章")
        
        # 过滤掉PR
        issues = [i for i in all_issues if not i.pull_request]

        # 准备缓存数据
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
        
        # 保存到缓存
        save_to_cache(cache_key, cache_data)
        
        return issues
        
    except Exception as e:
        print(f"获取文章失败: {e}")
        # 如果API失败，尝试使用过期的缓存
        cached = get_cached_data(cache_key)
        if cached:
            print("API失败，尝试使用过期的缓存数据...")
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

def fetch_issues(repo):
    """保持原有接口，但使用缓存版本"""
    return fetch_issues_with_cache(repo)

def load_template(template_name):
    """加载模板文件"""
    template_path = os.path.join("templates", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告: 模板文件 {template_name} 不存在，使用默认模板")
        # 返回一个简单的默认模板
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MyGitBlog</title>
</head>
<body>
    <h1>Blog Content</h1>
    {{CONTENT}}
</body>
</html>"""

def load_article_template():
    """加载文章详情页模板"""
    template_path = os.path.join("templates", "article.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # 默认文章模板
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{TITLE}} - mYogg'Blog</title>
    <link rel="stylesheet" href="../static/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
    <style>
        .article-header {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e1e4e8;
        }
        .article-title {
            margin-bottom: 0.5rem;
        }
        .article-meta {
            color: #586069;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .article-labels {
            margin-top: 1rem;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 1rem;
            color: #0366d6;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .original-link {
            margin-top: 2rem;
            padding: 1rem;
            background: #f6f8fa;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }
        .markdown-body {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
    </style>
</head>
<body>
    <div class="markdown-body">
        <a href="../index.html" class="back-link">← 返回博客首页</a>
        
        <div class="article-header">
            <h1 class="article-title">{{TITLE}}</h1>
            <div class="article-meta">
                发布于: {{DATE}} | 文章ID: #{{NUMBER}}
            </div>
            <div class="article-labels">
                {{LABELS}}
            </div>
        </div>
        
        <div class="article-content">
            {{CONTENT}}
        </div>
        
        <div class="original-link">
            <strong>📝 原文链接:</strong>
            <a href="{{ORIGINAL_URL}}" target="_blank" rel="noopener">{{ORIGINAL_URL}}</a>
            <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #586069;">
                本文内容来自GitHub Issues，点击上方链接查看原文和讨论。
            </p>
        </div>
    </div>
</body>
</html>"""

def get_label_color(label_name, label_color):
    """根据GitHub标签颜色生成对应的CSS类名"""
    if not label_color:
        # 如果没有颜色信息，回退到原来的hash方法
        hash_num = int(hashlib.md5(label_name.encode()).hexdigest()[:8], 16)
        color_classes = [
            "gh-label-1", "gh-label-2", "gh-label-3", "gh-label-4", 
            "gh-label-5", "gh-label-6", "gh-label-7", "gh-label-8",
            "gh-label-9", "gh-label-10"
        ]
        return color_classes[hash_num % len(color_classes)]
    
    # 将GitHub的hex颜色映射到你的CSS类名
    color_mapping = {
        '#7057ff': 'gh-label-1',
        '#008672': 'gh-label-2', 
        '#b60205': 'gh-label-3',
        '#0e8a16': 'gh-label-4',
        '#ff9f1c': 'gh-label-5',
        '#d93f0b': 'gh-label-6',
        '#f9d0c4': 'gh-label-7',
        '#1d76db': 'gh-label-8',
        '#5319e7': 'gh-label-9',
        '#fbca04': 'gh-label-10',
        # GitHub默认颜色映射
        '#d73a4a': 'gh-label-3',    # GitHub红 -> gh-label-3
        '#0075ca': 'gh-label-8',    # GitHub蓝 -> gh-label-8
        '#cfd3d7': 'gh-label-7',    # GitHub灰 -> gh-label-7
        '#a2eeef': 'gh-label-4',    # GitHub青 -> gh-label-4
        '#d876e3': 'gh-label-1',    # GitHub紫 -> gh-label-1
        '#ffffff': 'gh-label-7',    # 白色 -> gh-label-7
    }
    
    # 标准化颜色值（GitHub可能返回不带#的颜色）
    if not label_color.startswith('#'):
        normalized_color = '#' + label_color.lower()
    else:
        normalized_color = label_color.lower()
    
    # 查找匹配的颜色，如果没有匹配则使用默认
    return color_mapping.get(normalized_color, 'gh-label-1')

def sort_issues(issue_list):
    """自定义排序函数：先按 Pinned 标签，再按时间"""
    def sort_key(issue):
        has_pinned_tag = any(label.name.lower() == "pinned" for label in issue.labels)
        return (0 if has_pinned_tag else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

def generate_article_page(issue):
    """生成单篇文章页面"""
    # 创建文章目录
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    
    # 加载文章模板
    template = load_article_template()
    
    # 转换Markdown为HTML
    html_content = markdown.markdown(issue.body or "暂无内容", extensions=['extra', 'codehilite', 'tables'])
    
    # 生成标签HTML - 使用GitHub实际颜色
    labels_html = []
    for label in issue.labels:
        if label.name.lower() != "pinned":
            color_class = get_label_color(label.name, label.color)
            labels_html.append(f'<span class="tag {color_class}">{label.name}</span> ')
    
    # 填充模板
    html = template.replace("{{TITLE}}", issue.title)
    html = html.replace("{{NUMBER}}", str(issue.number))
    html = html.replace("{{DATE}}", issue.created_at.strftime("%Y-%m-%d"))
    html = html.replace("{{CONTENT}}", html_content)
    html = html.replace("{{ORIGINAL_URL}}", issue.html_url)
    html = html.replace("{{LABELS}}", "".join(labels_html))
    
    # 生成文件名（使用文章ID）
    filename = f"article-{issue.number}.html"
    filepath = os.path.join(ARTICLES_DIR, filename)
    
    # 保存文章
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filename

def generate_index_html(issues):
    """生成首頁HTML"""
    
    if not issues:
        print("警告: 没有获取到文章数据")
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # 按標簽分類
    label_dict = {}
    # 同时收集所有标签的颜色信息
    label_colors = {}  # 存储每个标签的颜色
    
    for issue in issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)
            # 存储标签颜色（取第一个出现的颜色）
            if label.name not in label_colors:
                label_colors[label.name] = label.color
    
    # 对每个分类下的文章进行排序
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])
    
    # 获取所有置顶文章
    pinned_issues = []
    for issue in issues:
        if any(label.name.lower() == "pinned" for label in issue.labels):
            pinned_issues.append(issue)
    
    # 去重并排序置顶文章
    pinned_issues = sort_issues(list(set(pinned_issues)))

    # 加载基础模板
    template = load_template("base.html")
    
    # 生成標籤HTML - 使用GitHub实际颜色
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        # 使用标签的实际颜色
        label_color = label_colors.get(label)
        color_class = get_label_color(label, label_color)
        tags_html.append(f'<span class="tag {color_class}" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')">{label}</span> ')
    
    # 1. 生成置顶文章HTML区块 - 使用与分类一致的样式
    pinned_html = []
    if pinned_issues:
        # 生成文章列表
        articles_html = []
        for issue in pinned_issues:
            # 生成文章页面并获取链接
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
            </li>''')
        
        # 包裹在与分类一致的容器中
        pinned_html.append(f'''
        <div class="category-section">
            <h2>置顶文章 <small>({len(pinned_issues)}篇文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
        </div>
        ''')
    
    # 2. 生成最近文章HTML - 显示5篇，排除已显示在置顶的文章
    recent_html = []
    
    # 获取所有文章并排序（排除置顶文章中已显示的）
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    
    # 去重并排序
    all_sorted_issues = sort_issues(list(set(all_sorted_issues)))
    
    # 过滤掉已经在置顶文章中显示的
    pinned_issue_ids = [issue.number for issue in pinned_issues]
    recent_candidates = [issue for issue in all_sorted_issues if issue.number not in pinned_issue_ids]
    
    # 只取前5篇
    recent_issues = recent_candidates[:5]
    
    if recent_issues:
        articles_html = []
        for issue in recent_issues:
            # 生成文章页面并获取链接
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
            </li>''')
        
        recent_html.append(f'''
        <div class="category-section">
            <h2>最近文章 <small>(5篇最新文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
        </div>
        ''')
    
    # 3. 生成分類HTML
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]
        
        articles_html = []
        for issue in visible_items:
            # 生成文章页面并获取链接
            article_filename = generate_article_page(issue)
            article_url = f"{ARTICLES_DIR}/{article_filename}"
            
            pin_mark = " 🔖" if any(lbl.name.lower() == "pinned" for lbl in issue.labels) else ""
            articles_html.append(f'''
            <li>
                <a href="{article_url}">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")}){pin_mark}</span>
            </li>''')
        
        hidden_articles_html = []
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                # 生成文章页面并获取链接
                article_filename = generate_article_page(issue)
                article_url = f"{ARTICLES_DIR}/{article_filename}"
                
                hidden_articles_html.append(f'''
                <li>
                    <a href="{article_url}">{issue.title}</a>
                    <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                </li>''')
            
            show_more_btn = f'''
            <div id="hidden-{category_id}" class="hidden-articles">
                <ul class="article-list">{''.join(hidden_articles_html)}</ul>
            </div>
            <button class="show-more-btn" onclick="toggleMore(\'{category_id}\')" id="btn-{category_id}">
                顯示更多 ({len(hidden_items)}篇)
            </button>
            '''
        else:
            show_more_btn = ""
        
        category_html = f'''
        <div class="category-section" data-label="{safe_label}">
            <h2>{label} <small>({len(items)}篇文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
            {show_more_btn}
        </div>
        '''
        categories_html.append(category_html)
    
    # 填充模板
    html = template.replace("{{TAGS}}", "".join(tags_html))
    html = html.replace("{{PINNED_ARTICLES}}", "".join(pinned_html))
    html = html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    html = html.replace("{{CATEGORIES}}", "".join(categories_html))
    html = html.replace("{{YEAR}}", str(datetime.now().year))
    
    return html

def main():
    # 检查token
    if not GITHUB_TOKEN:
        print("错误: 请先设置 G_TT 环境变量")
        print("运行: export G_TT='你的github_token'")
        return
    
    try:
        g = login()
        repo = get_repo(g)
        print(f"连接仓库: {repo.full_name}")
        
        issues = fetch_issues(repo)
        print(f"处理 {len(issues)} 篇文章")
        
        if not issues:
            print("没有找到文章，请检查仓库是否有open的issues")
            return
        
        # 生成文章页面和首页
        html_text = generate_index_html(issues)
        
        # 生成首页
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ {output_path} 已生成")
        
        # 处理静态文件
        os.makedirs("static", exist_ok=True)
        
        # 复制CSS文件
        css_sources = ["templates/style.css", "static/style.css", "style.css"]
        js_sources = ["templates/script.js", "static/script.js", "script.js"]
        
        css_found = False
        js_found = False
        
        for css_source in css_sources:
            if os.path.exists(css_source):
                import shutil
                shutil.copy(css_source, "static/style.css")
                print(f"✅ CSS文件已复制: {css_source} → static/style.css")
                css_found = True
                break
        
        if not css_found:
            print("⚠️ 警告: 未找到 style.css 文件，页面可能无法正常显示样式。")

        for js_source in js_sources:
            if os.path.exists(js_source):
                import shutil
                shutil.copy(js_source, "static/script.js")
                print(f"✅ JS文件已复制: {js_source} → static/script.js")
                js_found = True
                break
        
        if not js_found:
            print("⚠️ 警告: 未找到 script.js 文件，交互功能可能失效。")

        print(f"🎉 博客生成任务完成！共生成 {len(issues)} 篇文章")
        print("📁 文章目录: articles/")
        print("🏠 首页: index.html")

    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")

# --- 程序入口 ---
if __name__ == "__main__":
    main()