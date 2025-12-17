import os
import re
import json
import time
import hashlib
import markdown
from github import Github
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import shutil

# ========== 配置 ==========
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"

# 默认配置
DEFAULT_CONFIG = {
    "max_recent": 5,
    "max_per_category": 5,
    "cache_duration": 3600,  # 缓存1小时
    "articles_dir": "articles",
    "max_workers": 3,  # 并行生成文章的最大线程数
    "exclude_labels": ["spam", "duplicate"],  # 排除的标签
    "include_only": [],  # 如果指定，只包含这些标签
    "rate_limit_delay": 0.05,  # API请求延迟
    "max_issues": 200,  # 最大获取文章数
    "cache_body_max_length": 5000,  # 缓存中body的最大长度
}

# 缓存配置
CACHE_FILE = "github_cache.json"
CONFIG_FILE = "config.yaml"

# ========== 工具函数 ==========
def timeit(func):
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"⏱️  {func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper

def load_config():
    """加载配置文件"""
    config = DEFAULT_CONFIG.copy()
    
    # 尝试加载YAML配置
    if os.path.exists(CONFIG_FILE):
        try:
            import yaml
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
        except ImportError:
            print("⚠️  未安装pyyaml，跳过YAML配置加载")
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
    
    # 环境变量覆盖
    if os.getenv("MAX_RECENT"):
        config["max_recent"] = int(os.getenv("MAX_RECENT"))
    if os.getenv("MAX_WORKERS"):
        config["max_workers"] = int(os.getenv("MAX_WORKERS"))
    
    return config

# 全局配置
CONFIG = load_config()

# ========== GitHub 连接 ==========
def login():
    if not GITHUB_TOKEN:
        print("❌ 错误: 请设置 G_TT 环境变量")
        print("💡 使用方法: export G_TT='你的github_token'")
        exit(1)
    
    try:
        g = Github(GITHUB_TOKEN, per_page=30)  # 设置每页数量
        # 测试连接
        user = g.get_user()
        print(f"✅ 已连接到 GitHub: {user.login}")
        return g
    except Exception as e:
        print(f"❌ GitHub连接失败: {e}")
        exit(1)

def get_repo(g):
    try:
        repo = g.get_repo(REPO_NAME)
        print(f"✅ 已获取仓库: {repo.full_name}")
        return repo
    except Exception as e:
        print(f"❌ 获取仓库失败: {e}")
        exit(1)

# ========== 缓存管理 ==========
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
                if datetime.now() - cache_time < timedelta(seconds=CONFIG["cache_duration"]):
                    print(f"📦 使用缓存数据: {key}")
                    return data["data"]
    except Exception as e:
        print(f"⚠️  读取缓存失败: {e}")
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
        
        print(f"💾 已缓存: {key} ({len(data)} 条记录)")
    except Exception as e:
        print(f"⚠️  保存缓存失败: {e}")

def get_cache_timestamp(key):
    """获取缓存的时间戳"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if key in cache:
                return datetime.fromisoformat(cache[key]["timestamp"])
    except:
        pass
    return None

# ========== Issue 数据处理 ==========
def prepare_issues_for_cache(issues):
    """准备缓存数据，只存储必要字段"""
    cache_data = []
    for issue in issues:
        # 只存储必要的字段，减少缓存大小
        body = issue.body or ""
        issue_data = {
            "number": issue.number,
            "title": issue.title,
            "html_url": issue.html_url,
            "body": body[:CONFIG["cache_body_max_length"]],  # 限制body长度
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if hasattr(issue, 'updated_at') and issue.updated_at else None,
            "labels": [{"name": label.name, "color": label.color} for label in issue.labels],
            "pull_request": issue.pull_request is not None,
            "comments": issue.comments if hasattr(issue, 'comments') else 0,
        }
        cache_data.append(issue_data)
    return cache_data

def convert_cached_to_issues(cached_data):
    """将缓存数据转换为issue对象列表"""
    issues = []
    for item in cached_data:
        # 创建简化的issue对象
        issue = type('CachedIssue', (), {
            "number": item["number"],
            "title": item["title"],
            "html_url": item["html_url"],
            "body": item.get("body", ""),
            "created_at": datetime.fromisoformat(item["created_at"]) if item.get("created_at") else datetime.now(),
            "labels": [type('CachedLabel', (), {
                "name": label["name"], 
                "color": label.get("color", "ededed")
            }) for label in item.get("labels", [])],
            "pull_request": item.get("pull_request", False)
        })()
        if not issue.pull_request:
            issues.append(issue)
    return issues

@timeit
def fetch_issues_from_github(repo):
    """从GitHub API获取issues"""
    print("🌐 从GitHub API获取文章数据...")
    try:
        issues = []
        page = 1
        per_page = 30
        
        while True:
            try:
                page_issues = list(repo.get_issues(
                    state="open", 
                    sort="created", 
                    direction="desc",
                    per_page=per_page,
                    page=page
                ))
                
                if not page_issues:
                    break
                    
                # 过滤掉PR
                for issue in page_issues:
                    if not issue.pull_request:
                        # 排除配置中指定的标签
                        should_exclude = False
                        if CONFIG["exclude_labels"]:
                            for label in issue.labels:
                                if label.name.lower() in [l.lower() for l in CONFIG["exclude_labels"]]:
                                    should_exclude = True
                                    break
                        
                        # 包含指定标签（如果配置了）
                        if CONFIG["include_only"]:
                            has_included = False
                            for label in issue.labels:
                                if label.name in CONFIG["include_only"]:
                                    has_included = True
                                    break
                            if not has_included:
                                should_exclude = True
                        
                        if not should_exclude:
                            issues.append(issue)
                
                print(f"📄 已获取第 {page} 页，累计 {len(issues)} 篇文章")
                
                time.sleep(CONFIG["rate_limit_delay"])  # 避免速率限制
                page += 1
                
                # 限制最大文章数
                if len(issues) >= CONFIG["max_issues"]:
                    print(f"⚠️  已达到最大文章数限制: {CONFIG['max_issues']}")
                    break
                    
            except Exception as e:
                print(f"⚠️  获取第 {page} 页失败: {e}")
                break
        
        print(f"✅ 成功获取 {len(issues)} 篇文章")
        return issues
        
    except Exception as e:
        print(f"❌ 获取文章失败: {e}")
        raise

@timeit
def fetch_issues_with_cache(repo, force_refresh=False):
    """带缓存的获取issues函数"""
    cache_key = f"issues_{repo.full_name}_open"
    
    # 强制刷新
    if force_refresh:
        print("🔄 强制刷新文章数据...")
        issues = fetch_issues_from_github(repo)
        if issues:
            cache_data = prepare_issues_for_cache(issues)
            save_to_cache(cache_key, cache_data)
        return issues
    
    # 检查缓存新鲜度
    cache_timestamp = get_cache_timestamp(cache_key)
    if cache_timestamp:
        cache_age = (datetime.now() - cache_timestamp).seconds
        if cache_age < CONFIG["cache_duration"]:
            print(f"📦 缓存新鲜度: {cache_age // 60}分{cache_age % 60}秒前")
    
    # 尝试从缓存读取
    cached = get_cached_data(cache_key)
    if cached is not None:
        print(f"📦 从缓存加载 {len(cached)} 篇文章")
        return convert_cached_to_issues(cached)
    
    # 从GitHub API获取
    issues = fetch_issues_from_github(repo)
    
    if issues:
        # 保存到缓存
        cache_data = prepare_issues_for_cache(issues)
        save_to_cache(cache_key, cache_data)
    
    return issues

# ========== 模板加载 ==========
def load_template(template_name):
    """加载模板文件"""
    template_path = os.path.join("templates", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️  模板文件 {template_name} 不存在，使用默认模板")
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

# ========== 标签处理 ==========
def get_label_color(label_name):
    """根据标签名生成一个稳定的颜色类名（优化版）"""
    # 预定义GitHub风格颜色
    colors = [
        ("#7057ff", "white"),  # 紫色
        ("#008672", "white"),  # 绿色
        ("#b60205", "white"),  # 红色
        ("#0e8a16", "white"),  # 深绿
        ("#ff9f1c", "black"),  # 橙色
        ("#d93f0b", "white"),  # 深橙
        ("#f9d0c4", "black"),  # 浅橙
        ("#1d76db", "white"),  # 蓝色
        ("#5319e7", "white"),  # 深紫
        ("#fbca04", "black"),  # 黄色
        ("#006b75", "white"),  # 青色
        ("#bfdadc", "black"),  # 浅蓝
        ("#fef2c0", "black"),  # 浅黄
        ("#c2e0c6", "black"),  # 浅绿
        ("#bfd4f2", "black"),  # 浅蓝
        ("#d4c5f9", "black"),  # 浅紫
    ]
    
    # 简单但均匀的hash
    hash_val = sum(ord(c) * (i + 1) for i, c in enumerate(label_name))
    return colors[hash_val % len(colors)]

def sort_issues(issue_list):
    """自定义排序函数：先按 Pinned 标签，再按时间"""
    def sort_key(issue):
        has_pinned_tag = any(label.name.lower() == "pinned" for label in issue.labels)
        return (0 if has_pinned_tag else 1, -issue.created_at.timestamp())
    return sorted(issue_list, key=sort_key)

# ========== 文章生成 ==========
@timeit
def generate_article_page(issue):
    """生成单篇文章页面"""
    # 创建文章目录
    os.makedirs(CONFIG["articles_dir"], exist_ok=True)
    
    # 加载文章模板
    template = load_article_template()
    
    # 转换Markdown为HTML
    html_content = markdown.markdown(
        issue.body or "暂无内容", 
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # 生成标签HTML
    labels_html = []
    for label in issue.labels:
        if label.name.lower() != "pinned":
            bg_color, text_color = get_label_color(label.name)
            label_style = f"background-color: {bg_color}; color: {text_color};"
            labels_html.append(
                f'<span class="tag" style="{label_style}">{label.name}</span> '
            )
    
    # 填充模板
    replacements = {
        "{{TITLE}}": issue.title,
        "{{NUMBER}}": str(issue.number),
        "{{DATE}}": issue.created_at.strftime("%Y-%m-%d"),
        "{{CONTENT}}": html_content,
        "{{ORIGINAL_URL}}": issue.html_url,
        "{{LABELS}}": "".join(labels_html),
    }
    
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    
    # 生成文件名（使用文章ID）
    filename = f"article-{issue.number}.html"
    filepath = os.path.join(CONFIG["articles_dir"], filename)
    
    # 保存文章
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filename

@timeit
def generate_all_article_pages(issues):
    """并行生成所有文章页面"""
    print(f"🔄 开始生成 {len(issues)} 篇文章页面...")
    
    if CONFIG["max_workers"] <= 1:
        # 单线程模式
        results = []
        for i, issue in enumerate(issues, 1):
            try:
                filename = generate_article_page(issue)
                results.append((issue.number, filename))
                print(f"  进度: {i}/{len(issues)}", end="\r")
            except Exception as e:
                print(f"❌ 生成文章页面失败 (ID: {issue.number}): {e}")
        print()
    else:
        # 多线程模式
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            # 提交所有任务
            future_to_issue = {
                executor.submit(generate_article_page, issue): issue 
                for issue in issues
            }
            
            # 收集结果
            results = []
            completed = 0
            for future in as_completed(future_to_issue):
                issue = future_to_issue[future]
                try:
                    filename = future.result()
                    results.append((issue.number, filename))
                    completed += 1
                    print(f"  进度: {completed}/{len(issues)}", end="\r")
                except Exception as e:
                    print(f"❌ 生成文章页面失败 (ID: {issue.number}): {e}")
            print()
    
    print(f"✅ 已生成 {len(results)} 篇文章页面")
    return results

# ========== 首页生成 ==========
def generate_index_html(issues):
    """生成首頁HTML"""
    
    if not issues:
        print("⚠️  警告: 没有获取到文章数据")
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # 按標簽分類
    label_dict = {}
    for issue in issues:
        for label in issue.labels:
            label_name = label.name
            # 排除pinned标签（它会在单独的部分显示）
            if label_name.lower() != "pinned":
                label_dict.setdefault(label_name, []).append(issue)
    
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
    
    # 生成標籤HTML
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        bg_color, text_color = get_label_color(label)
        style = f"background-color: {bg_color}; color: {text_color};"
        tags_html.append(
            f'<span class="tag" style="{style}" data-label="{safe_label}" '
            f'onclick="filterByLabel(\'{safe_label}\')">{label}</span> '
        )
    
    # 1. 生成置顶文章HTML区块
    pinned_html = []
    if pinned_issues:
        articles_html = []
        for issue in pinned_issues:
            article_filename = f"article-{issue.number}.html"
            article_url = f"{CONFIG['articles_dir']}/{article_filename}"
            
            articles_html.append(f'''
            <li>
                <a href="{article_url}" target="_blank">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                <a href="{issue.html_url}" class="github-link" target="_blank" title="查看GitHub原文">🔗</a>
            </li>''')
        
        pinned_html.append(f'''
        <div class="category-section">
            <h2>📌 置顶文章 <small>({len(pinned_issues)}篇文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
        </div>
        ''')
    
    # 2. 生成最近文章HTML
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
    
    # 只取前N篇
    recent_issues = recent_candidates[:CONFIG["max_recent"]]
    
    if recent_issues:
        articles_html = []
        for issue in recent_issues:
            article_filename = f"article-{issue.number}.html"
            article_url = f"{CONFIG['articles_dir']}/{article_filename}"
            
            articles_html.append(f'''
            <li>
                <a href="{article_url}" target="_blank">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                <a href="{issue.html_url}" class="github-link" target="_blank" title="查看GitHub原文">🔗</a>
            </li>''')
        
        recent_html.append(f'''
        <div class="category-section">
            <h2>📄 最近文章 <small>({len(recent_issues)}篇最新文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
        </div>
        ''')
    
    # 3. 生成分類HTML
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:CONFIG["max_per_category"]]
        hidden_items = items[CONFIG["max_per_category"]:]
        
        articles_html = []
        for issue in visible_items:
            article_filename = f"article-{issue.number}.html"
            article_url = f"{CONFIG['articles_dir']}/{article_filename}"
            
            pin_mark = " 🔖" if any(lbl.name.lower() == "pinned" for lbl in issue.labels) else ""
            articles_html.append(f'''
            <li>
                <a href="{article_url}" target="_blank">{issue.title}</a>
                <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")}){pin_mark}</span>
                <a href="{issue.html_url}" class="github-link" target="_blank" title="查看GitHub原文">🔗</a>
            </li>''')
        
        hidden_articles_html = []
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                article_filename = f"article-{issue.number}.html"
                article_url = f"{CONFIG['articles_dir']}/{article_filename}"
                
                hidden_articles_html.append(f'''
                <li>
                    <a href="{article_url}" target="_blank">{issue.title}</a>
                    <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span>
                    <a href="{issue.html_url}" class="github-link" target="_blank" title="查看GitHub原文">🔗</a>
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
            <h2>🏷️ {label} <small>({len(items)}篇文章)</small></h2>
            <ul class="article-list">
                {''.join(articles_html)}
            </ul>
            {show_more_btn}
        </div>
        '''
        categories_html.append(category_html)
    
    # 填充模板
    replacements = {
        "{{TAGS}}": "".join(tags_html),
        "{{PINNED_ARTICLES}}": "".join(pinned_html),
        "{{RECENT_ARTICLES}}": "".join(recent_html),
        "{{CATEGORIES}}": "".join(categories_html),
        "{{YEAR}}": str(datetime.now().year),
    }
    
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    
    return html

# ========== 静态文件处理 ==========
def copy_static_files():
    """复制静态文件"""
    os.makedirs("static", exist_ok=True)
    
    # 优先顺序
    css_sources = ["templates/style.css", "static/style.css", "style.css"]
    js_sources = ["templates/script.js", "static/script.js", "script.js"]
    
    # 复制CSS
    css_copied = False
    for css_source in css_sources:
        if os.path.exists(css_source):
            shutil.copy2(css_source, "static/style.css")
            print(f"✅ CSS文件已复制: {css_source} → static/style.css")
            css_copied = True
            break
    
    if not css_copied:
        print("⚠️  警告: 未找到 style.css 文件，创建默认CSS")
        create_default_css()
    
    # 复制JS
    js_copied = False
    for js_source in js_sources:
        if os.path.exists(js_source):
            shutil.copy2(js_source, "static/script.js")
            print(f"✅ JS文件已复制: {js_source} → static/script.js")
            js_copied = True
            break
    
    if not js_copied:
        print("⚠️  警告: 未找到 script.js 文件，创建默认JS")
        create_default_js()

def create_default_css():
    """创建默认CSS文件"""
    default_css = """/* 基础样式 */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292e;
    background-color: #f6f8fa;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
}
"""
    with open("static/style.css", "w", encoding="utf-8") as f:
        f.write(default_css)

def create_default_js():
    """创建默认JS文件"""
    default_js = """// 默认JavaScript
console.log('GitBlog 已加载');
"""
    with open("static/script.js", "w", encoding="utf-8") as f:
        f.write(default_js)

# ========== 主程序 ==========
@timeit
def main():
    """主函数"""
    print("🚀 开始生成博客...")
    print("=" * 50)
    
    # 显示配置
    print("📋 当前配置:")
    print(f"  - 最大最近文章数: {CONFIG['max_recent']}")
    print(f"  - 每分类最大文章数: {CONFIG['max_per_category']}")
    print(f"  - 缓存时间: {CONFIG['cache_duration']}秒")
    print(f"  - 并行工作数: {CONFIG['max_workers']}")
    print(f"  - 排除标签: {CONFIG['exclude_labels']}")
    print("=" * 50)
    
    # 检查token
    if not GITHUB_TOKEN:
        print("❌ 错误: 请先设置 G_TT 环境变量")
        print("💡 运行: export G_TT='你的github_token'")
        return
    
    try:
        # 1. 连接GitHub
        g = login()
        repo = get_repo(g)
        
        # 2. 获取文章数据
        issues = fetch_issues_with_cache(repo)
        print(f"📊 处理 {len(issues)} 篇文章")
        
        if not issues:
            print("⚠️  没有找到文章，请检查仓库是否有open的issues")
            return
        
        # 3. 生成所有文章页面
        article_results = generate_all_article_pages(issues)
        
        # 4. 生成首页
        print("🔄 生成首页...")
        html_text = generate_index_html(issues)
        
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ 首页已生成: {output_path}")
        
        # 5. 处理静态文件
        copy_static_files()
        
        # 6. 完成
        print("=" * 50)
        print("🎉 博客生成任务完成！")
        print(f"📁 文章目录: {CONFIG['articles_dir']}/")
        print(f"📄 总文章数: {len(article_results)}")
        print(f"🏠 首页: index.html")
        print(f"🎨 样式文件: static/style.css")
        print(f"⚡ 脚本文件: static/script.js")
        print("=" * 50)
        
        # 显示统计信息
        label_dict = {}
        for issue in issues:
            for label in issue.labels:
                if label.name.lower() != "pinned":
                    label_dict[label.name] = label_dict.get(label.name, 0) + 1
        
        if label_dict:
            print("📊 标签统计:")
            for label, count in sorted(label_dict.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {label}: {count}篇")
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

# ========== 程序入口 ==========
if __name__ == "__main__":
    main()