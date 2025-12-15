import os
import re
import json
import time
from github import Github
from datetime import datetime, timedelta
import hashlib

# ================= 配置 =================
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
MAX_RECENT = 5
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600
# ========================================

def login():
    if not GITHUB_TOKEN:
        print("❌ 错误: 请设置 G_TT 环境变量")
        exit(1)
    try:
        return Github(GITHUB_TOKEN)
    except Exception as e:
        print(f"❌ GitHub登录失败: {e}")
        exit(1)

def get_repo(g):
    try:
        return g.get_repo(REPO_NAME)
    except Exception as e:
        print(f"❌ 无法找到仓库 {REPO_NAME}: {e}")
        exit(1)

def get_cached_data(key):
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if key in cache:
                data = cache[key]
                # 解析时间，如果失败则使用很久以前的时间
                cache_time = datetime.fromisoformat(data["timestamp"].replace("Z", ""))
                if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
                    print(f"✅ 使用缓存数据: {key}")
                    return data["data"]
    except Exception as e:
        print(f"⚠️ 读取缓存失败 (将重新获取): {e}")
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
        print(f"✅ 已缓存: {key}")
    except Exception as e:
        print(f"⚠️ 保存缓存失败: {e}")

def fetch_issues_with_cache(repo):
    cache_key = f"issues_{repo.full_name}_open"
    cached = get_cached_data(cache_key)
    
    if cached is not None:
        print(f"📦 从缓存加载 {len(cached)} 篇文章")
        issues = []
        for item in cached:
            # 简化对象模拟，只保留必要的字段
            issue = type('Issue', (), {})()
            issue.number = item.get("number", 0)
            issue.title = item.get("title", "无标题")
            issue.html_url = item.get("html_url", "#")
            issue.body = item.get("body", "")
            issue.created_at = datetime.fromisoformat(item.get("created_at", datetime.now().isoformat()))
            issue.labels = [type('Label', (), {'name': lbl.get('name', '未知')}) for lbl in item.get("labels", [])]
            issue.pull_request = item.get("pull_request", None)
            issues.append(issue)
        # 过滤PR
        return [i for i in issues if not i.pull_request]

    print("🌐 从GitHub API获取文章数据...")
    try:
        all_issues = []
        # 使用分页获取，防止数据量大时报错
        for issue in repo.get_issues(state="open", per_page=100):
            all_issues.append(issue)
            time.sleep(0.1) # 避免请求过快
        
        # 过滤掉PR
        valid_issues = [i for i in all_issues if not i.pull_request]
        print(f"✅ 成功获取 {len(valid_issues)} 篇文章")

        # 准备缓存数据
        cache_data = []
        for issue in valid_issues:
            # 确保时间字段安全
            created_at_str = None
            if issue.created_at:
                try:
                    created_at_str = issue.created_at.isoformat()
                except:
                    created_at_str = datetime.now().isoformat()
            
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "html_url": issue.html_url,
                "body": issue.body or "",
                "created_at": created_at_str,
                "labels": [{"name": label.name} for label in issue.labels],
                "pull_request": issue.pull_request is not None
            }
            cache_data.append(issue_data)
        
        save_to_cache(cache_key, cache_data)
        return valid_issues
        
    except Exception as e:
        print(f"❌ 获取文章失败: {e}")
        return []

def generate_index_html(issues):
    """生成HTML内容"""
    if not issues:
        print("⚠️ 警告: 没有获取到文章数据")
        return "<html><body><h1>暂时没有文章</h1></body></html>"

    # --- 1. 标签颜色生成 (GitHub风格) ---
    def get_label_color_class(label_name):
        colors = [
            ('purple', '#e0e0ff', '#6363ff'),
            ('green', '#d0f0d0', '#2da12d'),
            ('yellow', '#fff5d7', '#fbca04'),
            ('red', '#ffd9d9', '#cb2431'),
            ('gray', '#f0f0f0', '#555555'),
            ('blue', '#d0e8ff', '#005cc5'),
            ('orange', '#ffe5d0', '#f19600'),
        ]
        hash_val = int(hashlib.md5(label_name.encode('utf-8')).hexdigest(), 16)
        color = colors[hash_val % len(colors)]
        return {'bg': color, 'text': color}[[source_group_web_1]]

    # --- 2. 排序逻辑 (Pinned置顶 + 时间倒序) ---
    def sort_issues(issue_list):
        def sort_key(issue):
            # 安全检查：防止标签为空
            has_pinned = False
            if issue.labels:
                has_pinned = any(getattr(label, 'name', '').lower() == "pinned" for label in issue.labels)
            # 安全处理时间
            timestamp = 0
            try:
                if issue.created_at:
                    timestamp = issue.created_at.timestamp()
            except:
                timestamp = 0
            return (0 if has_pinned else 1, -timestamp)
        return sorted(issue_list, key=sort_key)

    # --- 3. 数据分类 ---
    label_dict = {}
    for issue in issues:
        if issue.labels:
            for label in issue.labels:
                label_name = getattr(label, 'name', '未分类')
                label_dict.setdefault(label_name, []).append(issue)

    # 排序每个分类
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])

    # --- 4. 生成HTML组件 ---
    # 标签云
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        color_info = get_label_color_class(label)
        tag_style = f"background-color: {color_info['bg']}; color: {color_info['text']}; border: 1px solid {color_info['text']}; border-radius: 3px; padding: 2px 8px; margin: 4px; cursor: pointer; display: inline-block; font-size: 14px;"
        tags_html.append(f'<span style="{tag_style}" data-label="{safe_label}">{label}</span>')

    # 最近文章 (取所有文章合并排序)
    all_sorted_issues = []
    for items in label_dict.values():
        all_sorted_issues.extend(items)
    all_sorted_issues = sort_issues(list(set(all_sorted_issues)))

    recent_html = []
    for i in all_sorted_issues[:MAX_RECENT]:
        pin_icon = " 🔖" if any(getattr(lbl, 'name', '').lower() == "pinned" for lbl in i.labels) else ""
        date_str = "未知日期"
        try:
            if i.created_at:
                date_str = i.created_at.strftime("%Y-%m-%d")
        except:
            pass
        recent_html.append(f'<li><a href="{i.html_url}" target="_blank">{i.title}</a> <span style="color:#888; margin-left:8px;">({date_str}){pin_icon}</span></li>')

    # 分类文章
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        visible_items = items[:MAX_PER_CATEGORY]
        
        articles_html = []
        for issue in visible_items:
            pin_mark = " 🔖" if any(getattr(lbl, 'name', '').lower() == "pinned" for lbl in i.labels) else ""
            date_str = "未知日期"
            try:
                if issue.created_at:
                    date_str = issue.created_at.strftime("%Y-%m-%d")
            except:
                pass
            articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span style="color:#888; margin-left:8px;">({date_str}){pin_mark}</span></li>')
        
        category_html = f'''
        <div class="category-section" data-label="{safe_label}">
            <h2>{label} <small>({len(items)}篇文章)</small></h2>
            <ul>{''.join(articles_html)}</ul>
        </div>'''
        categories_html.append(category_html)

    # --- 5. 组合最终HTML ---
    final_html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Gitblog - 文章列表</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .article-date {{ color: #666; font-size: 0.9em; margin-left: 8px; }}
            .tag {{ margin: 4px; }}
            h1, h2 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>🚀 我的博客</h1>
        <div id="tags">{''.join(tags_html)}</div>
        
        <h2>📅 最近文章</h2>
        <ul>{''.join(recent_html)}</ul>
        
        <h2>📦 分类文章</h2>
        {''.join(categories_html)}
        
        <footer style="margin-top: 50px; color: #888; font-size: 0.9em; text-align: center;">
            <p>最后生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </body>
    </html>
    """
    return final_html_content

def main():
    print("🚀 开始生成HTML页面...")
    
    if not GITHUB_TOKEN:
        print("❌ 错误: 请先设置 G_TT 环境变量")
        return

    try:
        g = login()
        repo = get_repo(g)
        print(f"🔗 连接仓库: {repo.full_name}")

        issues = fetch_issues_with_cache(repo)
        print(f"📝 处理 {len(issues)} 篇文章")

        if not issues:
            print("⚠️ 没有找到文章，将生成空页面")

        # --- 生成文件 ---
        html_content = generate_index_html(issues)
        
        # 直接生成 index.html (根据你的日志需求)
        output_path = "index.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ {output_path} 已成功生成!")

    except Exception as e:
        print(f"❌ 执行出错: {e}")
        # 即使出错，也尽量生成一个错误提示页面
        error_html = f"<html><body><h1>生成失败</h1><p>{e}</p></body></html>"
        with open("index.html", "w") as f:
            f.write(error_html)
        exit(1) # 确保非零退出码让CI/CD知道出错了

if __name__ == "__main__":
    main()
