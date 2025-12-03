import os
import re
import markdown
from datetime import datetime
from github import Github

# ================= 設置 =================
REPO_NAME = "Gitblog"
BACKUP_DIR = "BACKUP"
TODO_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
IGNORE_LABELS = TODO_LABELS + FRIENDS_LABELS
GITHUB_TOKEN = os.getenv("G_TT")  # 使用你的自定義 token
MAX_VISIBLE = 5  # 每個標籤顯示前五條文章

# ================= GitHub 登錄 =================
def login(token):
    return Github(token)

def get_repo(g, name):
    me = g.get_user().login
    return g.get_repo(f"{me}/{name}")

def is_me(issue, me):
    return issue.user.login == me

def generate_html_page(repo, me):
    md = f"# {repo.name}\n\n"

    # 按標籤分類
    labels = sorted(repo.get_labels(), key=lambda x: x.name)
    for label in labels:
        if label.name in IGNORE_LABELS:
            continue
        issues = [i for i in repo.get_issues(labels=(label,)) if is_me(i, me)]
        if not issues:
            continue

        md += f"## {label.name}\n"
        for i, issue in enumerate(issues):
            line = f"- [{issue.title}]({issue.html_url})\n"
            if i < MAX_VISIBLE:
                md += line
            else:
                md += f"<details><summary>更多文章...</summary>{line}</details>\n"
        md += "\n"

    # Markdown → HTML
    html_text = markdown.markdown(md, output_format="html5")
    year = datetime.now().year
    footer_html = f'<footer style="text-align:center; color:#888; margin-top:2rem;">© {year} MyOGG. All rights reserved.</footer>'

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{repo.name}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
body {{ display:flex; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; }}
.markdown-body {{ max-width:900px; width:95%; padding:2rem; margin:2rem auto; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }}
h1,h2,h3 {{ color:#2c3e50; }}
a {{ color:#0366d6; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.header-line {{ height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }}
h1.page-title {{ text-align:center; margin-top:0; margin-bottom:2rem; }}
@media (max-width:600px) {{ .markdown-body {{ padding:1rem; font-size:16px; }} }}
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
<div class="header-line"></div>
<h1 class="page-title">{repo.name}</h1>
{html_text}
{footer_html}
</div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_page)

def main():
    g = login(GITHUB_TOKEN)
    me = g.get_user().login
    repo = get_repo(g, REPO_NAME)
    generate_html_page(repo, me)

if __name__ == "__main__":
    main()
