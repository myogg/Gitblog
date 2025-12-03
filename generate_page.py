import requests
import os
from datetime import datetime
from collections import defaultdict

REPO = "myogg/Gitblog"
TOKEN = os.getenv("G_TT")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def fetch_issues():
    url = f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def group_by_label(issues):
    grouped = defaultdict(list)
    for issue in issues:
        if "pull_request" in issue:
            continue
        labels = issue.get("labels", [])
        if labels:
            for lb in labels:
                grouped[lb["name"]].append(issue)
        else:
            grouped["未分類"].append(issue)
    return grouped

def build_html(grouped):
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MyOGG Blog</title>
<style>
body { font-family: Arial, sans-serif; margin:0; padding:0; background:#f5f5f5; }
.container { max-width:900px; margin:auto; background:white; padding:20px; }

.tag-header { font-size:22px; margin-top:40px; padding-bottom:6px;
              border-bottom:3px solid #ff6a00; font-weight:bold; }

.issue { padding:10px 0; }
.issue a { text-decoration:none; color:#0366d6; font-size:18px; }

.more-btn {
    margin-top:10px; cursor:pointer; color:#ff6a00; font-weight:bold;
}
.hidden { display:none; }

footer {
    margin-top:50px; padding:15px; text-align:center;
    color:#888; font-size:14px;
    border-top:2px solid #ddd;
}
</style>

<script>
function toggleMore(id){
  var x = document.getElementById(id);
  if(x.classList.contains('hidden')){
     x.classList.remove('hidden');
  } else {
     x.classList.add('hidden');
  }
}
</script>

</head>
<body>
<div class="container">
<h1 style="text-align:center; margin-top:20px;">MyOGG Blog</h1>
"""

    for tag, items in grouped.items():
        html += f'<div class="tag-header">{tag}</div>\n'
        for i, issue in enumerate(items):
            if i < 5:
                html += f'<div class="issue"><a href="{issue["html_url"]}" target="_blank">· {issue["title"]}</a></div>\n'

        if len(items) > 5:
            html += f'<div id="more-{tag}" class="hidden">'
            for issue in items[5:]:
                html += f'<div class="issue"><a href="{issue["html_url"]}" target="_blank">· {issue["title"]}</a></div>\n'
            html += "</div>"
            html += f'<div class="more-btn" onclick="toggleMore(\'more-{tag}\')">顯示更多…</div>'

    year = datetime.now().year
    html += f"""
<footer>© {year} MyOGG. All rights reserved.</footer>
</div>
</body>
</html>
"""
    return html

def main():
    issues = fetch_issues()
    grouped = group_by_label(issues)
    html = build_html(grouped)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
