import os
import re
import json
import markdown
import time
from github import Github
from datetime import datetime, timedelta
from marko.ext.gfm import gfm as marko

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
            # 创建简化的issue对象
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
                "labels": [{"name": label.name} for label in issue.labels],
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
                    "labels": [type('CachedLabel', (), {"name": label["name"]}) for label in item["labels"]],
                    "pull_request": item["pull_request"]
                })()
                issues.append(issue)
            return [i for i in issues if not i.pull_request]
        return []

def fetch_issues(repo):
    """保持原有接口，但使用缓存版本"""
    return fetch_issues_with_cache(repo)

def load_template(template_name):
    """加載模板文件"""
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
    
    # 按創建時間排序每個分類下的文章
    for label in label_dict:
        label_dict[label] = sorted(label_dict[label], key=lambda x: x.created_at, reverse=True)
    
    # 加載基礎模板
    template = load_template("base.html")
    
    # 生成標籤HTML
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        tags_html.append(f'<span class="tag" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')">{label}</span> ')
    
    # 生成最近文章HTML
    sorted_issues = sorted(issues, key=lambda x: x.created_at, reverse=True)
    recent_html = []
    for i in sorted_issues[:MAX_RECENT]:
        recent_html.append(f'<li><a href="{i.html_url}" target="_blank">{i.title}</a></li>')
    
    # 生成分類HTML
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        # 可見文章
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]
        
        # 生成文章列表
        articles_html = []
        for issue in visible_items:
            articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
        
        # 生成隱藏文章
        hidden_articles_html = []
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
        
        # 生成HTML
        html_text = generate_index_html(issues)
        
        # 創建目錄並保存
        os.makedirs("site", exist_ok=True)
        output_path = "site/index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"HTML已生成: {output_path}")
        
        # 複製靜態文件
        os.makedirs("site/static", exist_ok=True)
        if os.path.exists("static/style.css"):
            import shutil
            shutil.copy("static/style.css", "site/static/style.css")
            print("已复制: static/style.css")
        if os.path.exists("static/script.js"):
            shutil.copy("static/script.js", "site/static/script.js")
            print("已复制: static/script.js")
        
        print("网站生成完成！")
        print("打开 site/index.html 查看效果")
        
    except Exception as e:
        print(f"运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
