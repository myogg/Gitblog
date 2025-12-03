import os
from github import Github
from datetime import datetime

# 配置
GITHUB_TOKEN = os.getenv("G_TT")
GITHUB_USER = "myogg"
REPO_NAME = "Gitblog"
MAX_RECENT = 5  # 側邊欄最近文章數量

# 登錄 GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(f"{GITHUB_USER}/{REPO_NAME}")

# 獲取標籤
labels = list(repo.get_labels())
labels = sorted(labels, key=lambda x: x.name.lower())

# 獲取最近文章（所有 issues 按時間排序）
all_issues = list(repo.get_issues(state="open"))
all_issues.sort(key=lambda x: x.created_at, reverse=True)
recent_issues = all_issues[:MAX_RECENT]

# 生成側邊欄 HTML
tags_html = "<div><h3>標籤</h3><ul style='list-style:none;padding:0;'>"
for label in labels:
    tags_html += f"<li style='display:inline-block;margin:0.2rem;'><span style='padding:0.3rem 0.6rem;background:#ff6a00;color:white;border-radius:4px;'>{label.name}</span></li>"
tags_html += "</ul></div>"

recent_html = "<div style='margin-top:1rem;'><h3>最近文章</h3><ul style='list-style:none;padding:0;'>"
for issue in recent_issues:
    recent_html += f"<li><a href='{issue.html_url}' style='text-decoration:none;color:#0366d6;'>{issue.title}</a></li>"
recent_html += "</ul></div>"

sidebar_html = f"<aside>{tags_html}{recent_html}</aside>"

# 主內容 HTML（簡單文章列表）
main_content = "<div><h1>文章列表</h1>"
for issue in all_issues:
    main_content += f"<h2><a href='{issue.html_url}'>{issue.title}</a></h2>"
main_content += "</div>"

# 頁尾
year = datetime.now().year
footer_html = f"""
<footer>
<div style="height:4px;width:100%;background: linear-gradient(90deg,#ff6a00,#ee0979,#00d4ff);"></div>
<p style="text-align:center;color:#888;font-size:0.9rem;">© {year} MyOGG. All rights reserved.</p>
</footer>
"""

# 組合完整頁面
html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My GitBlog</title>
<style>
body {{ display:flex; flex-direction:column; font-family:'Helvetica Neue',Arial,sans-serif; background:#f5f5f5; margin:0; }}
header {{ text-align:center; padding:1rem; }}
.container {{ display:flex; flex-wrap:wrap; max-width:1200px; margin:auto; }}
.main {{ flex:1 1 700px; padding:2rem; background:white; margin:1rem; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.1); }}
aside {{ flex:0 0 250px; padding:1rem; background:#fafafa; margin:1rem; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.05); }}
h1,h2,h3 {{ color:#2c3e50; }}
a {{ color:#0366d6; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
footer {{ margin-top:2rem; }}
@media (max-width:800px) {{
  .container {{ flex-direction:column; }}
  aside {{ order:2; }}
  .main {{ order:1; }}
}}
</style>
</head>
<body>
<header><h1>My GitBlog</h1></header>
<div class="container">
<div class="main">{main_content}</div>
{sidebar_html}
</div>
{footer_html}
</body>
</html>
"""

# 輸出文件
os.makedirs("site", exist_ok=True)
with open("site/index.html", "w", encoding="utf-8") as f:
    f.write(html_page)
print("index.html 已生成到 site/ 文件夾")
