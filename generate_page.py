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

html_body = ""

labels = sorted(repo.get_labels(), key=lambda l: l.name)
for label in labels:
    issues = [i for i in repo.get_issues(labels=[label]) if not i.pull_request]
    if not issues:
        continue
    html_body += f"<h2>{label.name}</h2>\n<ul>"
    visible = issues[:MAX_ISSUES_VISIBLE]
    hidden = issues[MAX_ISSUES_VISIBLE:]

    # 顯示最新 5 篇
    for issue in visible:
        html_body += f"<li><a href='{issue.html_url}'>{issue.title}</a> ({issue.created_at.date()})</li>"

    # 隱藏文章折疊
    if hidden:
        html_body += f"<li><details><summary>顯示更多...</summary><ul>"
        for issue in hidden:
            html_body += f"<li><a href='{issue.html_url}'>{issue.title}</a> ({issue.created_at.date()})</li>"
        html_body += "</ul></details></li>"

    html_body += "</ul>\n"

# 頁面標題與彩條
page_title = "My GitBlog"
year = datetime.now().year
footer_html = f"<footer style='margin-top:2rem;text-align:center;color:#888;font-size:0.9rem;'>© {year} MyOGG. All rights reserved.</footer>"

html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
  body {{ display:flex; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; }}
  .markdown-body {{ max-width:900px; width:95%; padding:2rem; margin:2rem auto; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }}
  h1,h2,h3 {{ color:#2c3e50; }}
  a {{ color:#0366d6; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .header-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }}
  h1.page-title {{ text-align:center; margin-top:0; margin-bottom:2rem; }}
  footer {{ margin-top:2rem; text-align:center; color:#888; font-size:0.9rem; }}
  details summary {{ cursor:pointer; font-weight:bold; color:#0366d6; }}
  details[open] summary {{ color:#d23669; }}
  @media (max-width:600px) {{ .markdown-body {{ padding:1rem; font-size:16px; }} }}
</style>
</head>
<body>
<div class="markdown-body">
  <div class="header-line"></div>
  <h1 class="page-title">{page_title}</h1>
  {html_body}
  {footer_html}
</div>
</body>
</html>
"""

with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_page)
