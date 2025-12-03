import os
import markdown
from github import Github
from datetime import datetime

# 輸出目錄
SITE_DIR = "site"
os.makedirs(SITE_DIR, exist_ok=True)

# 使用 PAT
token = os.getenv("GITHUB_TOKEN")
g = Github(token)

# 讀取倉庫
repo_name = os.getenv("GITHUB_REPOSITORY")  # e.g. myogg/Gitblog
repo = g.get_repo(repo_name)

MAX_ISSUES_VISIBLE = 5

# 側邊欄標籤列表
labels = sorted(repo.get_labels(), key=lambda l: l.name)
sidebar_html = "<h3>分類</h3>\n<ul>"
for label in labels:
    sidebar_html += f"<li><a href='#{label.name}'>{label.name}</a></li>"
sidebar_html += "</ul>"

# 文章列表
content_html = ""
for label in labels:
    issues = [i for i in repo.get_issues(labels=[label]) if not i.pull_request]
    if not issues:
        continue
    content_html += f"<h2 id='{label.name}'>{label.name}</h2>\n<ul>"
    visible = issues[:MAX_ISSUES_VISIBLE]
    hidden = issues[MAX_ISSUES_VISIBLE:]

    for issue in visible:
        content_html += f"<li><a href='{issue.html_url}'>{issue.title}</a> ({issue.created_at.date()})</li>"

    if hidden:
        content_html += "<li><details><summary>顯示更多...</summary><ul>"
        for issue in hidden:
            content_html += f"<li><a href='{issue.html_url}'>{issue.title}</a> ({issue.created_at.date()})</li>"
        content_html += "</ul></details></li>"

    content_html += "</ul>\n"

# 頁面標題與彩條
page_title = "My GitBlog"
year = datetime.now().year
footer_html = f"""
<div class="footer-line"></div>
<footer style='margin-top:2rem;text-align:center;color:#888;font-size:0.9rem;'>
© {year} MyOGG. All rights reserved.
</footer>
"""

# 完整 HTML
html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
body {{ display:flex; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; }}
.container {{ display:flex; max-width:1200px; margin:2rem auto; }}
.sidebar {{ width:200px; margin-right:2rem; position:sticky; top:1rem; }}
.content {{ flex:1; }}
.markdown-body {{ background:white; padding:2rem; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }}
h1,h2,h3 {{ color:#2c3e50; }}
a {{ color:#0366d6; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.header-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }}
.footer-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#00d4ff,#ee0979,#ff6a00); margin-top:2rem; }}
h1.page-title {{ text-align:center; margin-top:0; margin-bottom:2rem; }}
details summary {{ cursor:pointer; font-weight:bold; color:#0366d6; }}
details[open] summary {{ color:#d23669; }}
@media (max-width:768px) {{
  .container {{ flex-direction:column; }}
  .sidebar {{ width:100%; margin-bottom:1rem; position:static; }}
}}
</style>
</head>
<body>
<div class="container">
  <aside class="sidebar">
    {sidebar_html}
  </aside>
  <main class="content markdown-body">
    <div class="header-line"></div>
    <h1 class="page-title">{page_title}</h1>
    {content_html}
    {footer_html}
  </main>
</div>
</body>
</html>
"""

with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_page)
