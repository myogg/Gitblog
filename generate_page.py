import os
import re
import json
import time
from github import Github
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"

MAX_RECENT = 5
MAX_PER_CATEGORY = 5

# 缓存配置
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600  # 缓存1小时（3600秒）

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
            issue = type('CachedIssue', (), {
                "number": item["number"],
                "title": item["title"],
                "html_url": item["html_url"],
                "body": item["body"],
                "created_at": datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                "labels": [type('CachedLabel', (), {"name": label["name"]}) for label in item["labels"]],
                "pull_request": item["pull_request"]
            })()
            issues.append(issue)
        return issues
    
    # 从GitHub API获取
    print("从GitHub API获取文章数据...")
    try:
        all_issues = []
        for issue in repo.get_issues(state="open"):
            all_issues.append(issue)
            time.sleep(0.1) 
        
        print(f"成功获取 {len(all_issues)} 篇文章")
        issues = [i for i in all_issues if not i.pull_request]

        cache_data = []
        for issue in issues:
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "html_url": issue.html_url,
                "body": issue.body,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "labels": [{"name": label.name} for label in issue.labels],
                "pull_request": issue.pull_request is not None
            }
            cache_data.append(issue_data)
        
        save_to_cache(cache_key, cache_data)
        return issues
        
    except Exception as e:
        print(f"获取文章失败: {e}")
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
                    "labels": [type('CachedLabel', (), {"name": label["name"]}) for label in item["labels"]],
                    "pull_request": item["pull_request"]
                })()
                issues.append(issue)
            return [i for i in issues if not i.pull_request]
        return []

def fetch_issues(repo):
    return fetch_issues_with_cache(repo)

def load_template(template_name):
    """加載模板文件"""
    template_path = os.path.join("templates", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告: 模板文件 {template_name} 不存在，使用默认模板")
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MyGitBlog</title>
</head>
<body>
    <h1>Blog Content</h1>
    
</body>
</html>"""

def generate_index_html(issues):
    """生成首頁HTML"""
    
    if not issues:
        print("警告: 没有获取到文章数据")
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # 按標簽分類
    label_dict = {}
    for issue in issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)
    
    # --- 1. 分离 Pinned 文章 ---
    pinned_issues = []
    # 遍历所有文章，找出带有 Pinned 标签的
    for issue in issues:
        if any(label.name.lower() == "pinned" for label in issue.labels):
            pinned_issues.append(issue)
    
    # 从原分类中移除 Pinned 文章，避免重复显示 (可选，取决于您是否想在分类里也显示)
    # 这里为了清晰，我们在分类里不再显示，只在置顶区显示
    for label in label_dict:
        label_dict[label] = [issue for issue in label_dict[label] if not any(lbl.name.lower() == "pinned" for lbl in issue.labels)]

    # 排序逻辑保持不变
    def sort_issues(issue_list):
        def sort_key(issue):
            has_pinned_tag = any(label.name.lower() == "pinned" for label in issue.labels)
            return (0 if has_pinned_tag else 1, -issue.created_at.timestamp())
        return sorted(issue_list, key=sort_key)

    # 对每个分类排序
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])

    template = load_template("base.html")
    
    # --- 2. 生成顶部标签 HTML (改为 GitHub 多色风格) ---
    # 注意：这里去掉了之前的黑色内联样式，改为使用 class="github-tag"
    # 颜色映射逻辑通常在 CSS 里处理，或者这里可以简单随机/哈希，但为了不改其他地方，只改 class 名
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        # 移除了 style="background-color: #1a1a1a..." 
        # 改为使用符合 GitHub 风格的 class (具体颜色由 CSS 定义，或者 GitHub 风格的库处理)
        tags_html.append(f'<span class="github-tag tag" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')">{label}</span> ')
    
    # --- 3. 生成 Pinned 置顶区块 (新增的独立区块) ---
    pinned_html = ""
    if pinned_issues:
        pinned_articles = []
        for issue in pinned_issues:
            pinned_articles.append(f'<li class="pinned-item"><strong>[置顶]</strong> <a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
        pinned_html = f'''
        <div class="pinned-section">
            <h3>📌 置顶文章</h3>
            <ul class="article-list">
                {''.join(pinned_articles)}
            </ul>
        </div>
        <hr style="margin: 20px 0;"> <!-- 加个分割线 -->
        '''

    # --- 4. 生成最近文章 HTML (保持显示5篇，但排除置顶的?) ---
    # 这里逻辑保持不变，会自动包含置顶（如果在最近5篇里），或者您希望最近文章不包含置顶，可以过滤
    # 为了符合“最近”定义，这里不做特殊过滤，保持原逻辑
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    all_sorted_issues = sort_issues(list(set(all_sorted_issues)))
    
    recent_html = []
    for i in all_sorted_issues[:MAX_RECENT]:
        # 如果是置顶文章，这里也可以加个标记，或者不显示，看需求。这里保持简单，只显示标题。
        recent_html.append(f'<li><a href="{i.html_url}" target="_blank">{i.title}</a> <span class="article-date">({i.created_at.strftime("%Y-%m-%d")})</span></li>')

    # --- 5. 生成分类 HTML ---
    categories_html = []
    for label, items in sorted(label_dict.items()):
        if not items: # 跳过空分类
            continue
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]
        
        articles_html = []
        for issue in visible_items:
            articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
        
        hidden_articles_html = []
        show_more_btn = ""
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                hidden_articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
            
            show_more_btn = f'''
            <div id="hidden-{category_id}" class="hidden-articles">
                <ul class="article-list">{''.join(hidden_articles_html)}</ul>
            </div>
            <button class="show-more-btn" onclick="toggleMore(\'{category_id}\')" id="btn-{category_id}">
                顯示更多 ({len(hidden_items)}篇)
            </button>
            '''
        
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

    # --- 6. 填充模板 ---
    # 这里假设您的 base.html 模板中有 {{TAGS}}, {{PINNED_SECTION}}, {{RECENT_ARTICLES}}, {{CATEGORIES}} 这些占位符
    # 如果没有 {{PINNED_SECTION}}，您可能需要手动调整 HTML 结构，或者将 pinned_html 拼接到其他位置
    html = template.replace("{{TAGS}}", "".join(tags_html))
    
    # 将置顶区块插入到标签下方 (这是您要求的"标签下一个区块")
    # 如果模板没有预留位置，这里做一个简单的替换尝试
    if "{{PINNED_SECTION}}" in html:
        html = html.replace("{{PINNED_SECTION}}", pinned_html)
    else:
        # 如果没有占位符，就插在 {{RECENT_ARTICLES}} 前面或者 {{TAGS}} 后面
        # 这里选择插在 {{TAGS}} 后面
        html = html.replace("{{TAGS}}", "".join(tags_html) + pinned_html)

    html = html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    html = html.replace("{{CATEGORIES}}", "".join(categories_html))
    html = html.replace("{{YEAR}}", str(datetime.now().year))
    
    return html

def main():
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
        
        html_text = generate_index_html(issues)
        
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ {output_path} 已生成")
        
        # 处理静态文件
        os.makedirs("static", exist_ok=True)
        
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

        print("🎉 博客生成任务完成！请查看根目录下的 index.html")

    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()
