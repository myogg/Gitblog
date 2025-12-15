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

def fetch_all_data_with_cache(repo):
    """同时获取 Issues 和 Labels 数据"""
    cache_key = f"full_data_{repo.full_name}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached.get("issues", []), cached.get("labels", {})

    print("从GitHub API获取数据 (Issues + Labels)...")
    try:
        # 1. 获取 Labels 颜色
        repo_labels = {}
        for lbl in repo.get_labels():
            # 存储标签名 -> 颜色代码 (如 'bug' -> 'd73a4a')
            repo_labels[lbl.name] = lbl.color

        # 2. 获取 Issues
        issues = []
        for issue in repo.get_issues(state="open"):
            if not issue.pull_request:
                issues.append(issue)
            time.sleep(0.05)

        # 准备缓存数据
        cache_data = {
            "issues": [
                {
                    "number": i.number,
                    "title": i.title,
                    "html_url": i.html_url,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "labels": [{"name": lbl.name} for lbl in i.labels],
                    "body": i.body
                } for i in issues
            ],
            "labels": repo_labels
        }

        save_to_cache(cache_key, cache_data)
        return issues, repo_labels

    except Exception as e:
        print(f"API获取失败: {e}")
        return [], {}

def load_template(template_name):
    template_path = os.path.join("templates", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告: 模板文件 {template_name} 不存在，使用默认模板")
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Blog</title></head>
        <body>
            <div>{{TAGS}}</div>
            <div>{{PINNED_SECTION}}</div>
            <h2>最近文章</h2>
            <ul>{{RECENT_ARTICLES}}</ul>
            <div>{{CATEGORIES}}</div>
        </body>
        </html>
        """

def generate_index_html(all_issues, repo_labels):
    """生成首页 HTML"""
    if not all_issues:
        return "<html><body><h1>暂无文章</h1></body></html>"

    # --- 逻辑 1: 分离 Pinned 文章 ---
    pinned_issues = []
    normal_issues = []
    
    for issue in all_issues:
        # 判断是否为置顶
        is_pinned = any(label.name.lower() == "pinned" for label in issue.labels)
        if is_pinned:
            pinned_issues.append(issue)
        else:
            normal_issues.append(issue)

    # --- 逻辑 2: 按标签分类 (只分类普通文章) ---
    label_dict = {}
    for issue in normal_issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)

    # 排序函数 (时间倒序)
    def sort_by_date(issue_list):
        return sorted(issue_list, key=lambda x: x.created_at, reverse=True)

    for label in label_dict:
        label_dict[label] = sort_by_date(label_dict[label])

    # --- 生成 1: 顶部标签 HTML (使用真实 GitHub 颜色) ---
    # 去重并排序
    all_label_names = sorted(set(label for label in repo_labels.keys() if label in label_dict) | {"Pinned"})
    
    tags_html = []
    for label_name in all_label_names:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label_name).lower()
        
        # 获取 GitHub 官方颜色，如果没有则默认为 'ededed' (灰色)
        color_code = repo_labels.get(label_name, "ededed")
        
        # GitHub 颜色格式通常是 6位小写，如 'd73a4a'
        bg_color = f"#{color_code}"
        
        # 简单的对比度判断：如果颜色太深，文字用白色，否则用黑色
        # 这里简单处理，以 '0'-'7' 开头认为是深色
        is_dark = color_code in '01234567'
        text_color = "white" if is_dark else "black"
        
        style = (
            f"background-color: {bg_color}; "
            f"color: {text_color}; "
            f"padding: 6px 12px; "
            f"margin: 4px; "
            f"border-radius: 6px; "
            f"cursor: pointer; "
            f"display: inline-block; "
            f"font-weight: 500;"
        )
        tags_html.append(f'<span class="tag" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')" style="{style}">{label_name}</span>')

    # --- 生成 2: Pinned 独立区块 ---
    pinned_html = ""
    if pinned_issues:
        pinned_items = []
        for issue in pinned_issues:
            # 尝试获取文章的第一个标签颜色作为边框色，或者默认蓝色
            border_color = "#0088ff"
            if issue.labels:
                first_label_color = repo_labels.get(issue.labels.name, "0088ff")
                border_color = f"#{first_label_color}"
                
            pinned_items.append(
                f'<li style="padding: 12px; margin: 10px 0; border-left: 4px solid {border_color}; '
                f'background: #f6f8fa; list-style: none;">'
                f'<span style="font-size: 0.8em; color: #666; margin-right: 10px;">[置顶]</span>'
                f'<a href="{issue.html_url}" target="_blank" style="font-size: 1.1em; font-weight: bold; text-decoration: none;">'
                f'{issue.title}'
                f'</a>'
                f'<span style="color: #666; margin-left: 10px;">({issue.created_at.strftime("%m-%d")})</span>'
                f'</li>'
            )
        pinned_html = f"""
        <div style="margin: 25px 0; padding: 0;">
            <h3 style="color: #333; margin-bottom: 15px; border-left: 3px solid #0088ff; padding-left: 10px;">📌 置顶精选</h3>
            <ul style="padding-left: 0; margin: 0;">
                {''.join(pinned_items)}
            </ul>
        </div>
        <hr style="border: 1px solid #eee; margin: 20px 0;">
        """

    # --- 生成 3: 最近文章 (只显示普通文章中的最近5篇) ---
    # 合并所有普通文章并排序
    all_normal_sorted = sort_by_date(normal_issues)
    recent_html = []
    for issue in all_normal_sorted[:MAX_RECENT]:
        recent_html.append(
            f'<li style="padding: 8px 0; border-bottom: 1px dashed #eee;">'
            f'<a href="{issue.html_url}" target="_blank" style="text-decoration: none; color: #333;">{issue.title}</a> '
            f'<span style="color: #999; font-size: 0.9em;">({issue.created_at.strftime("%Y-%m-%d")})</span>'
            f'</li>'
        )

    # --- 生成 4: 分类文章 ---
    categories_html = []
    for label_name, issues_in_label in sorted(label_dict.items()):
        if not issues_in_label:
            continue
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label_name).lower()
        
        # 可见文章
        visible_issues = issues_in_label[:MAX_PER_CATEGORY]
        hidden_issues = issues_in_label[MAX_PER_CATEGORY:]
        
        # 文章列表 HTML
        articles_html = []
        for issue in visible_issues:
            articles_html.append(
                f'<li style="padding: 6px 0; border-bottom: 1px solid #f0f0f0;">'
                f'<a href="{issue.html_url}" target="_blank">{issue.title}</a> '
                f'<span style="color: #999; font-size: 0.8em;">({issue.created_at.strftime("%m-%d")})</span>'
                f'</li>'
            )
        
        # 隐藏文章按钮 (如果有的话)
        more_btn_html = ""
        if hidden_issues:
            cat_id = f"cat_{safe_label}"
            hidden_html = "".join([
                f'<li style="padding: 6px 0;">'
                f'<a href="{i.html_url}" target="_blank">{i.title}</a> '
                f'<span style="color: #999; font-size: 0.8em;">({i.created_at.strftime("%m-%d")})</span>'
                f'</li>' for i in hidden_issues
            ])
            more_btn_html = f"""
            <div id="{cat_id}_extra" style="display: none;">{hidden_html}</div>
            <button onclick="toggle('{cat_id}')" style="margin: 10px 0; padding: 5px 10px; background: #f0f0f0;">
                显示全部 {len(issues_in_label)} 篇
            </button>
            """

        cat_html = f"""
        <div class="category" data-label="{safe_label}" style="margin: 30px 0; padding: 0;">
            <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 5px;">
                {label_name} 
                <span style="color: #999; font-size: 0.9em;">({len(issues_in_label)}篇文章)</span>
            </h2>
            <ul style="padding-left: 20px;">
                {''.join(articles_html)}
            </ul>
            {more_btn_html}
        </div>
        """
        categories_html.append(cat_html)

    # --- 组合最终 HTML ---
    template = load_template("base.html")
    
    # 1. 先填入标签
    html = template.replace("{{TAGS}}", "".join(tags_html))
    # 2. 在标签后直接插入置顶区块 (这是关键，确保位置在标签下方)
    #    如果模板有 {{PINNED_SECTION}} 则替换，否则插入到 {{RECENT_ARTICLES}} 前面
    if "{{PINNED_SECTION}}" in html:
        html = html.replace("{{PINNED_SECTION}}", pinned_html)
    else:
        # 强制插入到最近文章占位符之前
        html = html.replace("{{RECENT_ARTICLES}}", pinned_html + "{{RECENT_ARTICLES}}", 1)
    
    # 3. 填入最近文章和分类
    html = html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    html = html.replace("{{CATEGORIES}}", "".join(categories_html))
    html = html.replace("{{YEAR}}", str(datetime.now().year))
    
    return html

def main():
    if not GITHUB_TOKEN:
        print("错误: 请先设置 G_TT 环境变量")
        return
    
    try:
        g = login()
        repo = get_repo(g)
        print(f"连接仓库: {repo.full_name}")
        
        # 获取数据 (文章 + 标签颜色)
        issues, labels_color_map = fetch_all_data_with_cache(repo)
        print(f"处理 {len(issues)} 篇文章")
        
        if not issues:
            print("没有找到文章")
            return
        
        # 生成 HTML
        html_text = generate_index_html(issues, labels_color_map)
        
        # 写入文件
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ {output_path} 生成成功！")
        
        # 处理静态资源
        os.makedirs("static", exist_ok=True)
        css_src = "templates/style.css"
        css_dst = "static/style.css"
        if os.path.exists(css_src):
            import shutil
            shutil.copy(css_src, css_dst)
            print("✅ 样式文件已更新")
        
        print("🚀 博客构建完成")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
