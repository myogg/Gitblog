import os
import re
import argparse
from datetime import datetime
from github import Github
import markdown

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

# --------------------------
# Prepare data
# --------------------------
# 標籤列表
labels = [l.name for l in repo.get_labels()]
# 最近文章
issues = sorted([i for i in repo.get_issues() if not i.pull_request],
                key=lambda x: x.created_at, reverse=True)
recent_issues = issues[:5]

# README 轉 HTML
with open("README.md", "r", encoding="utf-8") as f:
    md_text = f.read()
html_content = markdown.markdown(md_text, output_format="html5")

# --------------------------
# Generate label sections with fold
# --------------------------
label_html = ""
for label in labels:
    # 標籤文章
    labeled_issues = [i for i in issues if label in [l.name for l in i.labels]]
    label_html += f"<h3>{label}</h3><ul>"
    for i, issue in enumerate(labeled_issues):
        if i < 5:
            label_html += f"<li><a href='{issue.html_url}'>{issue.title}</a></li>"
        else:
            break
    if len(labeled_issues) > 5:
        label_html += f"<li><details><summary>更多...</summary>"
        for issue in labeled_issues[5:]:
            label_html += f"<li><a href='{issue.html_url}'>{issue.title}</a></li>"
        label_html += "</details></li>"
    label_html += "</ul>"

# --------------------------
# Sidebar
# --------------------------
import random

def random_color():
    return f"#{random.randint(0,0xFFFFFF):06x}"

sidebar_html = "<aside style='padding:1rem; border-left:1px solid #ccc;'>"
sidebar_html += "<h3>標籤</h3><div style='display:flex; flex-wrap:wrap; gap:0.3rem;'>"
for l in labels:
    sidebar_html += f"<span style='background:{random_color()}; color:white; padding:0.2rem 0.5rem; border-radius:5px; font-size:0.9rem;'>{l}</span>"
sidebar_html += "</div>"

sidebar_html += "<h3>最近文章</h3><ul>"
for i in recent_issues:
    sidebar_html += f"<li><a href='{i.html_url}'>{i.title}</a></li>"
sidebar_html += "</ul></aside>"

# --------------------------
# Page HTML
# --------------------------
page_title = "My GitBlog"
year = datetime.now().year
footer_html = f'<footer style="margin-top:2rem; text-align:center; color:#888; font-size:0.9rem;">© {year} MyOGG. All rights reserved.</footer>'
header_line = '<div style="height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem;"></div>'

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
aside {{ min-width:200px; padding:1rem; margin-left:2rem; }}
details {{ margin-left:1rem; }}
@media (max-width:900px) {{ 
  body {{ flex-direction:column; align-items:center; }}
  aside {{ margin-left:0; width:95%; margin-top:2rem; }}
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
{label_html}
{footer_html}
</div>
{sidebar_html}
</body>
</html>
"""

# Save
os.makedirs(args.output, exist_ok=True)
with open(os.path.join(args.output, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_page)
print("Page generated at:", os.path.join(args.output, "index.html"))
