import os
import re
import json
import time
import random
from github import Github
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"

MAX_RECENT = 5
MAX_PER_CATEGORY = 5

# 缓存配置
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600

def login():
    if not GITHUB_TOKEN:
        print("错误: 请设置 G_TT 环境变量")
        exit(1)
    return Github(GITHUB_TOKEN)

def get_repo(g):
    return g.get_repo(REPO_NAME)

def get_cached_data(key):
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if key in cache:
                data = cache[key]
                cache_time = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
                    print(f"使用缓存数据: {key}")
                    return data["data"]
    except Exception as e:
        print(f"读取缓存失败: {e}")
    return None

def save_to_cache(key, data):
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
    cache_key = f"issues_{repo.full_name}_open"
    cached = get_cached_data(cache_key)
    if cached is not None:
        print(f"从缓存加载 {len(cached)} 篇文章")
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
    {{TAGS}}
    {{RECENT_ARTICLES}}
    {{CATEGORIES}}
</body>
</html>"""

def generate_index_html(issues):
    if not issues:
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # 1. 分离 Pinned 文章
    pinned_issues = [issue for issue in issues if any(label.name.lower() == "pinned" for label in issue.labels)]
    # 剩余的普通文章
    normal_issues = [issue for issue in issues if not any(label.name.lower() == "pinned" for label in issue.labels)]

    # 2. 按标签分类 (只对普通文章分类，避免置顶重复)
    label_dict = {}
    for issue in normal_issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)

    # 排序函数
    def sort_issues(issue_list):
        def sort_key(issue):
            return -issue.created_at.timestamp()
        return sorted(issue_list, key=sort_key)

    # 对每个分类排序
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])

    template = load_template("base.html")
    
    # --- 修改点 1: 生成多彩标签 ---
    # 使用随机颜色生成器模拟 GitHub 的多彩标签
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        # --- 生成随机颜色 (模拟 GitHub 标签颜色) ---
        # GitHub 颜色通常比较鲜艳，这里生成 RGB 值
        r = random.randint(100, 255)
        g = random.randint(100, 255)
        b = random.randint(100, 255)
        bg_color = f"rgb({r}, {g}, {b})"
        # 文字颜色根据背景亮度自动选择黑色或白色
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "white" if brightness < 128 else "black"
        
        # --- 将颜色直接写入 style ---
        style = f"background-color: {bg_color}; color: {text_color}; padding: 5px 10px; margin: 5px; border-radius: 5px; cursor: pointer; display: inline-block;"
        tags_html.append(f'<span class="tag" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')" style="{style}">{label}</span> ')
    
    # --- 修改点 2: 生成 Pinned 独立区块 ---
    pinned_html = ""
    if pinned_issues:
        pinned_articles = []
        for issue in pinned_issues:
            pinned_articles.append(f'<li style="margin: 10px 0; padding: 10px; background: #fffdd0; border-left: 4px solid gold;"><strong>📌 置顶</strong> <a href="{issue.html_url}" target="_blank" style="font-size: 1.1em;">{issue.title}</a> <span style="color: #666; font-size: 0.9em;">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
        pinned_html = f'''
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #eee; border-radius: 8px; background: #f9f9f9;">
            <h3 style="color: #333; border-bottom: 2px solid #333; padding-bottom: 5px;">🌟 置顶推荐</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                {''.join(pinned_articles)}
            </ul>
        </div>
        '''

    # --- 生成最近文章 (只取普通文章，避免置顶重复) ---
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    all_sorted_issues = sort_issues(list(set(all_sorted_issues)))
    
    recent_html = []
    for i in all_sorted_issues[:MAX_RECENT]:
        recent_html.append(f'<li><a href="{i.html_url}" target="_blank">{i.title}</a> <span class="article-date">({i.created_at.strftime("%Y-%m-%d")})</span></li>')

    # --- 生成分类 HTML ---
    categories_html = []
    for label, items in sorted(label_dict.items()):
        if not items:
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
            <div id="hidden-{category_id}" class="hidden-articles" style="display: none;">
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

    # --- 核心修改：强制将置顶区块插入到标签之后 ---
    # 1. 先填充标签
    final_html = template.replace("{{TAGS}}", "".join(tags_html))
    
    # 2. 在 {{TAGS}} 替换后的内容后面，直接插入置顶区块
    # 这样确保置顶区块一定在标签的下一个位置
    if "{{RECENT_ARTICLES}}" in final_html:
        # 将置顶区块插入到最近文章之前
        final_html = final_html.replace("{{RECENT_ARTICLES}}", pinned_html + "{{RECENT_ARTICLES}}")
    
    # 3. 填充剩下的内容
    final_html = final_html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    final_html = final_html.replace("{{CATEGORIES}}", "".join(categories_html))
    final_html = final_html.replace("{{YEAR}}", str(datetime.now().year))
    
    return final_html

def main():
    if not GITHUB_TOKEN:
        print("错误: 请先设置 G_TT 环境变量")
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
        
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ {output_path} 已生成")
        
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
            print("⚠️ 警告: 未找到 style.css 文件")

        for js_source in js_sources:
            if os.path.exists(js_source):
                import shutil
                shutil.copy(js_source, "static/script.js")
                print(f"✅ JS文件已复制: {js_source} → static/script.js")
                js_found = True
                break
        
        if not js_found:
            print("⚠️ 警告: 未找到 script.js 文件")

        print("🎉 博客生成任务完成！")

    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()
