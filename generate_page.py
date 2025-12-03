import os
import markdown
from github import Github
from datetime import datetime

# 設置 token
token = os.getenv("G_TT")
repo_name = "Gitblog"

g = Github(token)
repo = g.get_repo(f"myogg/{repo_name}")

# 分類及文章列表
labels = repo.get_labels()
label_dict = {}
for label in labels:
    issues = repo.get_issues(labels=[label], state="open", sort="created", direction="desc", per_page=5)
    label_dict[label.name] = [(i.title, i.html_url) for i in issues]

# 最近文章（全局前5條）
all_issues = repo.get_issues(state="open", sort="created", direction="desc", per_page=5)
recent_articles = [(i.title, i.html_url) for i in all_issues]

# 讀取 README.md
with open("README.md", "r", encoding="utf-8") as f:
    md_text = f.read()

html_text = markdown.markdown(md_text, output_format="html5")

page_title = "My GitBlog"
year = datetime.now().year

footer_html = f'<footer style="margin-top:2rem; text-align:center; color:#888; font-size:0.9rem;">© {year} MyOGG. All rights reserved.</footer>'

# 側邊欄 HTML
sidebar_html = '<aside class="sidebar"><h3>分類</h3><ul>'
for label, articles in label_dict.items():
    sidebar_html += f'<li>{label}<ul>'
    for title, url in articles:
        sidebar_html += f'<li><a href="{url}">{title}</a></li>'
    sidebar_html += '</ul></li>'
sidebar_html += '</ul><h3>最近文章</h3><ul>'
for title, url in recent_articles:
    sidebar_html += f'<li><a href="{url}">{title}</a></li>'
sidebar_html += '</ul></aside>'

# 完整 HTML
html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
body {{ display:flex; flex-direction:row; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; line-height:1.6; }}
.markdown-body {{ max-width:900px; width:70%; padding:2rem; margin:2rem; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }}
.sidebar {{ width:25%; padding:1rem; background:#f9f9f9; border-left:1px solid #ddd; border-radius:0 8px 8px 0; }}
h1,h2,h3 {{ color:#2c3e50; }}
a {{ color:#0366d6; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.header-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }}
h1.page-title {{ text-align:center; margin-top:0; margin-bottom:2rem; }}
footer {{ margin-top:2rem; text-align:center; color:#888; font-size:0.9rem; }}
@media (max-width:900px) {{
    body {{ flex-direction:column; }}
    .markdown-body {{ width:95%; margin:1rem auto; }}
    .sidebar {{ width:95%; margin:0 auto; border-left:none; border-radius:8px 8px 0 0; }}
}}
@media (prefers-color-scheme: dark) {{
    body {{ background:#121212; color:#e0e0e0; }}
    .markdown-body {{ background:#1e1e1e; color:#e0e0e0; }}
    .sidebar {{ background:#1e1e1e; }}
    a {{ color:#58a6ff; }}
    .header-line {{ background: linear-gradient(90deg,#ff8c00,#ff2d95,#00e0ff); }}
}}
</style>
</head>
<body>
<div class="markdown-body">
<div class="header-line"></div>
<h1 class="page-title">{page_title}</h1>
{html_text}
{footer_html}
</div>
{sidebar_html}
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_page)
