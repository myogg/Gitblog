import os
import re
import markdown
from github import Github
from datetime import datetime
from marko.ext.gfm import gfm as marko

GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
BACKUP_DIR = "BACKUP"

MAX_RECENT = 5

def login():
    return Github(GITHUB_TOKEN)

def get_repo(g):
    return g.get_repo(REPO_NAME)

def _valid_xml_char_ordinal(c):
    codepoint = ord(c)
    return (0x20 <= codepoint <= 0xD7FF or c in "\t\n\r" or
            0xE000 <= codepoint <= 0xFFFD or 0x10000 <= codepoint <= 0x10FFFF)

def fetch_issues(repo):
    return [i for i in repo.get_issues(state="open") if not i.pull_request]

def generate_index_html(issues):
    # 按標簽分類
    label_dict = {}
    for issue in issues:
        for label in issue.labels:
            label_dict.setdefault(label.name, []).append(issue)

    # HTML頭部
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mYogg'Blog</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
<style>
body { display:flex; justify-content:center; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif; line-height:1.6; }
.markdown-body { max-width:900px; width:95%; padding:2rem; margin:2rem auto; background:white; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-radius:8px; }
h1,h2,h3 { color:#2c3e50; }
a { color:#0366d6; text-decoration:none; }
a:hover { text-decoration:underline; }
.header-line { height:4px; width:100%; border-radius:2px; background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff); margin-bottom:1rem; }
h1.page-title { text-align:center; margin-top:0; margin-bottom:2rem; }
footer { margin-top:2rem; text-align:center; color:#888; font-size:0.9rem; }
.sidebar { background:#fafafa; padding:1rem; border-radius:6px; margin-bottom:2rem; }
.sidebar h3 { margin-top:0; }
.tag { display:inline-block; margin:2px 4px; padding:2px 6px; border-radius:4px; background:#ff6a00; color:white; font-size:0.85rem; }
@media (max-width:600px) { .markdown-body { padding:1rem; font-size:16px; } }
</style>
</head>
<body>
<div class="markdown-body">
<div class="header-line"></div>
<h1 class="page-title">mYogg'Blog</h1>
""")

    # 側邊欄
    html_parts.append('<div class="sidebar">')
    html_parts.append('<h3>標簽</h3>')
    for label in sorted(label_dict.keys()):
        html_parts.append(f'<span class="tag">{label}</span> ')
    html_parts.append('<h3>最近文章</h3><ul>')
    sorted_issues = sorted(issues, key=lambda x: x.created_at, reverse=True)
    for i in sorted_issues[:MAX_RECENT]:
        html_parts.append(f'<li><a href="{i.html_url}">{i.title}</a></li>')
    html_parts.append('</ul></div>')

    # 正文分類展示
    for label, items in label_dict.items():
        html_parts.append(f'<h2>{label}</h2><ul>')
        for idx, issue in enumerate(items):
            safe_body = "".join(c for c in (issue.body or "") if _valid_xml_char_ordinal(c))
            if idx < MAX_RECENT:
                html_parts.append(f'<li><a href="{issue.html_url}">{issue.title}</a></li>')
            else:
                html_parts.append(f'''
<details>
<summary>{issue.title}</summary>
<p>{markdown.markdown(safe_body)}</p>
</details>
''')
        html_parts.append('</ul>')

    year = datetime.now().year
    html_parts.append(f'<footer>© {year} MyOGG. All rights reserved.</footer>')
    html_parts.append('</div></body></html>')
    return "\n".join(html_parts)

def main():
    g = login()
    repo = get_repo(g)
    issues = fetch_issues(repo)

    # 生成 index.html
    html_text = generate_index_html(issues)
    os.makedirs("site", exist_ok=True)
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html_text)
    print("index.html generated in site/")

if __name__ == "__main__":
    main()
