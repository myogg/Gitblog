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
CACHE_DURATION = 3600  # 缓存1小时

def login():
    if not GITHUB_TOKEN:
        print("错误: 请设置 G_TT 环境变量")
        exit(1)
    # 忽略认证方式的弃用警告，保证功能可用
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
        # 失败后尝试读取旧缓存
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

def fetch_labels_color(repo):
    """获取仓库标签的真实颜色"""
    color_map = {}
    try:
        # 尝试从缓存加载
        cached = get_cached_data("repo_labels_color")
        if cached:
            return cached
            
        # 从API获取
        for label in repo.get_labels():
            # GitHub返回的是不带#的6位字符串，如 'd73a4a'
            color_map[label.name] = label.color 
            
        save_to_cache("repo_labels_color", color_map)
    except Exception as e:
        print(f"获取标签颜色失败: {e}")
    return color_map

def generate_index_html(issues, repo):
    """生成首页HTML"""
    if not issues:
        return "<html><body><h1>暂时没有文章</h1></body></html>"
    
    # --- 1. 获取标签颜色映射 ---
    label_colors = fetch_labels_color(repo)
    
    # --- 2. 分离 Pinned 文章 ---
    pinned_issues = []
    normal_issues = []
    for issue in issues:
        # 修复点：遍历 labels 列表，判断是否有名为 "pinned" 的标签 (忽略大小写)
        has_pinned_tag = any(label.name.lower() == "pinned" for label in issue.labels)
        if has_pinned_tag:
            pinned_issues.append(issue)
        else:
            normal_issues.append(issue)

    # --- 3. 按标签分类 (仅针对普通文章) ---
    label_dict = {}
    for issue in normal_issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)

    # 排序函数
    def sort_by_date(issue_list):
        return sorted(issue_list, key=lambda x: x.created_at, reverse=True)

    for label in label_dict:
        label_dict[label] = sort_by_date(label_dict[label])

    # --- 4. 生成顶部标签 HTML (使用真实彩色) ---
    all_labels = sorted(label_dict.keys())
    tags_html = []
    
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        # 获取颜色代码
        hex_color = label_colors.get(label, "ededed") # 默认浅灰
        bg_color = f"#{hex_color}"
        
        # 计算文字颜色
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = "white" if brightness < 128 else "black"
        except:
            text_color = "black"

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
        tags_html.append(f'<span class="tag" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')" style="{style}">{label}</span> ')

    # --- 5. 生成 Pinned 独立区块 ---
    pinned_html = ""
    if pinned_issues:
        sorted_pinned = sort_by_date(pinned_issues)
        pinned_items = []
        for issue in sorted_pinned:
            # 修复点：获取文章的第一个标签颜色作为边框色
            border_color = "#0088ff" # 默认蓝色
            if issue.labels: 
                # 取第一个标签的颜色
                first_label_name = issue.labels.name 
                first_color = label_colors.get(first_label_name, "0088ff")
                border_color = f"#{first_color}"
                
            pinned_items.append(
                f'<li style="padding: 10px; margin: 5px 0; background: #f8f9fa; border-left: 3px solid {border_color}; list-style: none;">'
                f'<a href="{issue.html_url}" target="_blank" style="font-weight: bold; color: #333;">{issue.title}</a> '
                f'<span style="color: #888; font-size: 0.9em;">({issue.created_at.strftime("%m-%d")})</span>'
                f'</li>'
            )
        pinned_html = f"""
        <div style="margin: 15px 0;">
            <h3 style="color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px;">📌 置顶内容</h3>
            <ul style="padding-left: 0; list-style: none;">{''.join(pinned_items)}</ul>
        </div>
        """

    # --- 6. 生成最近文章 (仅普通文章) ---
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    all_sorted_issues = sort_by_date(list(set(all_sorted_issues)))
    
    recent_html = []
    for i in all_sorted_issues[:MAX_RECENT]:
        recent_html.append(
            f'<li style="padding: 8px 0; border-bottom: 1px dashed #eee; list-style: none;">'
            f'<a href="{i.html_url}" target="_blank">{i.title}</a> '
            f'<span style="color: #999; font-size: 0.9em;">({i.created_at.strftime("%Y-%m-%d")})</span>'
            f'</li>'
        )

    # --- 7. 生成分类 HTML ---
    categories_html = []
    for label, items in sorted(label_dict.items()):
        if not items:
            continue
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]
        
        articles_html = []
        for issue in visible_items:
            articles_html.append(
                f'<li style="padding: 5px 0; list-style: none;">'
                f'<a href="{issue.html_url}" target="_blank">{issue.title}</a> '
                f'<span style="color: #999; font-size: 0.9em;">({issue.created_at.strftime("%m-%d")})</span>'
                f'</li>'
            )
        
        hidden_html = ""
        btn_html = ""
        if hidden_items:
            cat_id = safe_label + "_more"
            hidden_list = "".join([
                f'<li style="padding: 5px 0; list-style: none;"><a href="{i.html_url}" target="_blank">{i.title}</a> '
                f'<span style="color: #999; font-size: 0.9em;">({i.created_at.strftime("%m-%d")})</span></li>'
                for i in hidden_items
            ])
            hidden_html = f'<div id="{cat_id}" style="display: none;">{hidden_list}</div>'
            btn_html = f'<button onclick="toggle(\'{cat_id}\')" style="margin: 10px 0; padding: 5px 10px;">显示全部</button>'

        categories_html.append(f"""
        <div class="category" style="margin: 20px 0;">
            <h3 style="color: #333;">{label} ({len(items)}篇)</h3>
            <ul style="padding-left: 20px;">{''.join(articles_html)}</ul>
            {hidden_html}
            {btn_html}
        </div>
        """)

    # --- 8. 组合最终 HTML ---
    try:
        template = load_template("base.html")
    except:
        # 如果没有模板，构建一个简单的结构
        template = "<html><head><meta charset='UTF-8'></head><body>{{TAGS}}<div>{{PINNED_SECTION}}</div><h2>最近文章</h2><ul>{{RECENT_ARTICLES}}</ul>{{CATEGORIES}}</body></html>"

    html = template.replace("{{TAGS}}", "".join(tags_html))
    
    # 处理置顶区块占位符
    if "{{PINNED_SECTION}}" in html:
        html = html.replace("{{PINNED_SECTION}}", pinned_html)
    else:
        # 如果没有占位符，插入到最近文章之前
        html = html.replace("{{RECENT_ARTICLES}}", pinned_html + "{{RECENT_ARTICLES}}", 1)
    
    html = html.replace("{{RECENT_ARTICLES}}", "".join(recent_html))
    html = html.replace("{{CATEGORIES}}", "".join(categories_html))
    html = html.replace("{{YEAR}}", str(datetime.now().year))
    
    return html

def load_template(template_name):
    template_path = os.path.join("templates", template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    if not GITHUB_TOKEN:
        print("错误: 请先设置 G_TT 环境变量")
        return
    
    try:
        g = login()
        repo = get_repo(g)
        print(f"连接仓库: {repo.full_name}")
        
        issues = fetch_issues_with_cache(repo)
        print(f"处理 {len(issues)} 篇文章")
        
        if not issues:
            print("没有找到文章")
            return
        
        # 生成 HTML
        html_text = generate_index_html(issues, repo)
        
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"✅ {output_path} 已生成")
        
        # 处理静态文件
        os.makedirs("static", exist_ok=True)
        css_src = "templates/style.css"
        css_dst = "static/style.css"
        if os.path.exists(css_src):
            import shutil
            shutil.copy(css_src, css_dst)
            print("✅ CSS文件已更新")
        
        print("🚀 博客构建完成")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
