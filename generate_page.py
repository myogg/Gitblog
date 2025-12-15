import os
import re
import json
import time
from github import Github
from datetime import datetime, timedelta
import hashlib

# --- 你的配置保持不变 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
MAX_RECENT = 5
MAX_PER_CATEGORY = 5

CACHE_FILE = "github_cache.json"
CACHE_DURATION = 3600

# ... (login, get_repo, cache functions 不变) ...

def fetch_issues_with_cache(repo):
    # ... (保持你之前的缓存逻辑不变) ...
    pass

def generate_index_html(issues):
    """生成首頁HTML (修改版)"""
    
    if not issues:
        return "<html><body><h1>暂时没有文章</h1></body></html>"

    # --- 新增：生成 GitHub 风格的颜色类 ---
    def get_label_color_class(label_name):
        # GitHub 使用哈希来为标签分配颜色，这里我们模拟几种常见的
        colors = [
            ('purple', '#e0e0ff', '#6363ff'),   # 浅紫 / 紫
            ('green', '#d0f0d0', '#2da12d'),   # 浅绿 / 绿
            ('yellow', '#fff5d7', '#fbca04'),  # 浅黄 / 黄
            ('red', '#ffd9d9', '#cb2431'),     # 浅红 / 红
            ('gray', '#f0f0f0', '#555555'),    # 浅灰 / 灰
            ('blue', '#d0e8ff', '#005cc5'),    # 浅蓝 / 蓝
            ('orange', '#ffe5d0', '#f19600'),  # 浅橙 / 橙
        ]
        # 使用标签名的哈希值来确保同一个标签每次颜色一致
        hash_val = int(hashlib.md5(label_name.encode('utf-8')).hexdigest(), 16)
        color = colors[hash_val % len(colors)]
        return {
            'name': color,
            'bg': color,
            'text': color
        }

    # --- 核心排序逻辑优化 ---
    def sort_issues(issue_list):
        """自定义排序：1. Pinned置顶 2. 时间倒序 (最新的在前)"""
        def sort_key(issue):
            # 检查是否有 Pinned 标签 (不区分大小写)
            has_pinned = any(label.name.lower() == "pinned" for label in issue.labels)
            # 时间倒序：使用负时间戳让新的时间排在前面
            return (0 if has_pinned else 1, -issue.created_at.timestamp())
        return sorted(issue_list, key=sort_key)

    # 按标签分类
    label_dict = {}
    for issue in issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)

    # 对每个分类下的文章进行排序 (应用置顶逻辑)
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])

    # --- 生成 HTML 内容 ---

    # 1. 生成标签云 HTML (带颜色样式)
    all_labels = sorted(label_dict.keys())
    tags_html = []
    for label in all_labels:
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        color_info = get_label_color_class(label)
        
        # 这里使用内联样式模拟 GitHub 标签外观
        tag_style = f"background-color: {color_info['bg']}; color: {color_info['text']}; border: 1px solid {color_info['text']}; border-radius: 3px; padding: 2px 8px; margin: 4px; cursor: pointer; display: inline-block; font-size: 14px;"
        tags_html.append(f'<span style="{tag_style}" data-label="{safe_label}" onclick="filterByLabel(\'{safe_label}\')">{label}</span>')

    # 2. 生成最近文章 HTML
    # 将所有文章合并去重并排序 (同样应用置顶逻辑)
    all_sorted_issues = sort_issues(list(set([issue for sublist in label_dict.values() for issue in sublist])))
    
    recent_html = []
    for i in all_sorted_issues[:MAX_RECENT]:
        pin_icon = " 🔖" if any(lbl.name.lower() == "pinned" for lbl in i.labels) else ""
        recent_html.append(f'<li><a href="{i.html_url}" target="_blank">{i.title}</a> <span class="article-date">({i.created_at.strftime("%Y-%m-%d")}){pin_icon}</span></li>')

    # 3. 生成分类 HTML
    categories_html = []
    for label, items in sorted(label_dict.items()):
        safe_label = re.sub(r'[^a-zA-Z0-9]', '-', label).lower()
        
        visible_items = items[:MAX_PER_CATEGORY]
        hidden_items = items[MAX_PER_CATEGORY:]

        articles_html = []
        for issue in visible_items:
            pin_mark = " 🔖" if any(lbl.name.lower() == "pinned" for lbl in issue.labels) else ""
            articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")}){pin_mark}</span></li>')

        hidden_articles_html = []
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                hidden_articles_html.append(f'<li><a href="{issue.html_url}" target="_blank">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
            
            show_more_btn = f'''
            <div id="hidden-{category_id}" class="hidden-articles" style="display: none;">
                <ul class="article-list">{''.join(hidden_articles_html)}</ul>
            </div>
            <button class="show-more-btn" onclick="toggleMore(\'{category_id}\')" id="btn-{category_id}" style="margin: 10px 0; padding: 5px 10px;">
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

    # --- 组合最终 HTML ---
    # 由于我们直接生成了带样式的标签，这里直接拼接
    # 如果你有 base.html 模板，这里会去替换 {{TAGS}} 等占位符
    # 为了演示，这里构建一个简单的结构
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MyGitBlog</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial; padding: 20px; }}
            .article-date {{ color: #888; font-size: 0.9em; margin-left: 8px; }}
            ul {{ list-style-type: none; padding-left: 0; }}
        </style>
    </head>
    <body>
        <h1>我的博客</h1>
        <div id="tags">{''.join(tags_html)}</div>
        
        <h2>最近文章</h2>
        <ul>{''.join(recent_html)}</ul>
        
        <h2>分类</h2>
        {''.join(categories_html)}
        
        <script>
            // 这里可以保留你原来的 filterByLabel 和 toggleMore 函数
        </script>
    </body>
    </html>
    """
    
    return full_html

def main():
    # ... (保持不变) ...
    pass

if __name__ == "__main__":
    main()
