import os
from github import Github
import markdown
from jinja2 import Environment, FileSystemLoader

OUTPUT = "site"
POST_DIR = os.path.join(OUTPUT, "posts")
TEMPLATE_DIR = "templates"

def ensure_dirs():
    os.makedirs(OUTPUT, exist_ok=True)
    os.makedirs(POST_DIR, exist_ok=True)

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = "myogg/gitblog"
    g = Github(token)
    repo = g.get_repo(repo_name)

    ensure_dirs()

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    posts = []

    for issue in repo.get_issues(state="all"):
        if issue.pull_request:
            continue

        html_body = markdown.markdown(issue.body or "")

        filename = f"{issue.number}.html"

        post_data = {
            "title": issue.title,
            "body": html_body,
            "labels": [l.name for l in issue.labels],
            "created": issue.created_at.strftime("%Y-%m-%d"),
            "url": issue.html_url,
            "filename": filename,
            "excerpt": (issue.body or "")[:120].replace("\n", " "),
        }

        posts.append(post_data)

        # render single post
        tpl = env.get_template("post.html")
        output = tpl.render(**post_data)

        with open(os.path.join(POST_DIR, filename), "w", encoding="utf-8") as f:
            f.write(output)

    # render index page
    tpl = env.get_template("index.html")
    html = tpl.render(posts=sorted(posts, key=lambda x: x["created"], reverse=True))
    with open(os.path.join(OUTPUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print("生成博客完成！")

if __name__ == "__main__":
    main()
