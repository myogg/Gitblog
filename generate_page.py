import os
import re
import argparse
from datetime import datetime
from github import Github
import markdown
from marko.ext.gfm import gfm as marko

# --------------------------
# Argument parsing
# --------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--token", required=True)
parser.add_argument("--repo", required=True)
parser.add_argument("--output", default="site")
args = parser.parse_args()

g = Github(args.token)
repo = g.get_repo(args.repo)
me = g.get_user().login

# --------------------------
# Generate index.html
# --------------------------
# 標籤列表
labels = [l.name for l in repo.get_labels()]
# 最近文章
issues = sorted([i for i in repo.get_issues() if not i.pull_request],
                key=lambda x: x.created_at, reverse=True)
recent_issues = issues[:5]

# 讀 README.md
with open("README.md", "r", encoding="utf-8") as f:
    md_text = f.read()
html_content = markdown.markdown(md_text, output_format="html5")

# 側邊欄 HTML
sidebar_html = "<aside style='padding:1rem; border-left:1px solid #ccc;'>"
sidebar_html += "<h3>分類</h3><ul>"
for l in labels:
    sidebar_html += f"<li>{l}</li>"
sidebar_html += "</ul><h3>最近文章</h3><ul>"
for i in recent_issues:
    sidebar_html += f"<li><a href='{i.html_url}'>{i.title}</a></li>"
sidebar_html += "</ul></aside>"

# 彩條和頁面標題
page_title = "My GitBlog"
year = datetime.now().year
footer_html = f'<footer style="margin-top:2rem; text-align:center; color:#888; font-size:0.9rem;">© {year} MyOGG. All rights reserved.</footer>'
header_line = '<div style="height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem;"></div>'

# 組裝完整 HTML
html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
body {{ display:flex; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; line-height:1.6; }}
.markdown-body {{ max-width:900px; width:95%; padding:2rem; margin:2rem auto; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }}
h1,h2,h3 {{ color:#2c3e50; }}
a {{ color:#0366d6; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.header-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }}
h1.page-title {{ text-align:center; margin-top:0; margin-bottom:2rem; }}
footer {{ margin-top:2rem; text-align:center; color:#888; font-size:0.9rem; }}
@media (max-width:600px) {{ 
  body {{ flex-direction:column; }}
  .markdown-body {{ width:95%; padding:1rem; font-size:16px; }}
  aside {{ order:2; margin-top:2rem; }}
}}
@media (prefers-color-scheme: dark) {{
  body {{ background:#121212; color:#e0e0e0; }}
  .markdown-body {{ background:#1e1e1e; color:#e0e0e0; }}
  a {{ color:#58a6ff; }}
  .header-line {{ background: linear-gradient(90deg,#ff8c00,#ff2d95,#00e0ff); }}
}}
</style>
</head>
<body>
<div class="markdown-body">
{header_line}
<h1 class="page-title">{page_title}</h1>
{html_content}
{footer_html}
</div>
{sidebar_html}
</body>
</html>
"""

# 保存到 output 目錄
os.makedirs(args.output, exist_ok=True)
with open(os.path.join(args.output, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_page)
print("Page generated at:", os.path.join(args.output, "index.html"))
