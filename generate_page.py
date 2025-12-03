import os
import re
import markdown
from github import Github
from datetime import datetime
from marko.ext.gfm import gfm as marko

GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"

MAX_RECENT = 5
MAX_PER_CATEGORY = 5

def login():
    return Github(GITHUB_TOKEN)

def get_repo(g):
    return g.get_repo(REPO_NAME)

def fetch_issues(repo):
    return [i for i in repo.get_issues(state="open") if not i.pull_request]

def load_template(template_name):
    """加載模板文件"""
    template_path = os.path.join("templates", template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_index_html(issues):
    """生成首頁HTML"""
    
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
        recent_html.append(f'<li><a href="{i.html_url}">{i.title}</a></li>')
    
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
            articles_html.append(f'<li><a href="{issue.html_url}">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
        
        # 生成隱藏文章
        hidden_articles_html = []
        if hidden_items:
            category_id = safe_label + "-hidden"
            for issue in hidden_items:
                hidden_articles_html.append(f'<li><a href="{issue.html_url}">{issue.title}</a> <span class="article-date">({issue.created_at.strftime("%Y-%m-%d")})</span></li>')
            
            show_more_btn = f'''
            <div id="hidden-{category_id}" class="hidden-articles">
                <ul class="article-list">{''.join(hidden_articles_html)}</ul>
            </div>
            <button class="show-more-btn" onclick="toggleMore('{category_id}')" id="btn-{category_id}">
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
    g = login()
    repo = get_repo(g)
    issues = fetch_issues(repo)
    
    # 生成HTML
    html_text = generate_index_html(issues)
    
    # 創建目錄並保存
    os.makedirs("site", exist_ok=True)
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html_text)
    
    # 複製靜態文件
    os.makedirs("site/static", exist_ok=True)
    if os.path.exists("static/style.css"):
        import shutil
        shutil.copy("static/style.css", "site/static/style.css")
    if os.path.exists("static/script.js"):
        import shutil
        shutil.copy("static/script.js", "site/static/script.js")
    
    print("網站已生成在 site/ 目錄")

if __name__ == "__main__":
    main()
