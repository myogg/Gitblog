# -*- coding: utf-8 -*-
import argparse
import os
import re

import markdown
from feedgen.feed import FeedGenerator
from github import Github
from lxml.etree import CDATA
from marko.ext.gfm import gfm as marko

BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5
TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
ABOUT_LABELS = ["About"]
THINGS_LABELS = ["Things"]
IGNORE_LABELS = (
    FRIENDS_LABELS
    + TOP_ISSUES_LABELS
    + TODO_ISSUES_LABELS
    + ABOUT_LABELS
    + THINGS_LABELS
)

FRIENDS_TABLE_HEAD = "| Name | Link | Desc | \n | ---- | ---- | ---- |\n"
FRIENDS_TABLE_TEMPLATE = "| {name} | {link} | {desc} |\n"
FRIENDS_INFO_DICT = {
    "名字": "",
    "链接": "",
    "描述": "",
}

MD_HEAD = """# {repo_name} 的博客

* 用文字记录我的胡思乱想与生活的瞬间，我疯狂的想法与可能为之的行动。  
* 记录在这个时代下的焦虑、迷茫、挣扎与希望。
* [About me](https://github.com/myogg/myogg)

### 提醒自己：
#### 1.放弃向他人证明自己，放弃向自己证明自己。专注忘我地去做你应该做的事情，心无旁骛地去解决问题。当你脚踏实地的走自己的路时，那种拼命想要证明什么的冲动就会越来越少。你也会因此变得轻松、自由。

——查理·芒格

"""

def get_me(user):
    return user.get_user().login


def is_me(issue, me):
    return issue.user.login == me


def is_hearted_by_me(comment, me):
    reactions = list(comment.get_reactions())
    for r in reactions:
        if r.content == "heart" and r.user.login == me:
            return True
    return False


def _make_friend_table_string(s):
    info_dict = FRIENDS_INFO_DICT.copy()
    try:
        string_list = s.splitlines()
        # drop empty line
        string_list = [l for l in string_list if l and not l.isspace()]
        for l in string_list:
            string_info_list = re.split("：", l)
            if len(string_info_list) < 2:
                continue
            info_dict[string_info_list[0]] = string_info_list[1]
        return FRIENDS_TABLE_TEMPLATE.format(
            name=info_dict["名字"], link=info_dict["链接"], desc=info_dict["描述"]
        )
    except Exception as e:
        print(str(e))
        return


# help to covert xml vaild string
def _valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF
        or codepoint in (0x9, 0xA, 0xD)
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def format_time(time):
    return str(time)[:10]


def login(token):
    return Github(token)


def get_repo(user: Github, repo: str):
    return user.get_repo(repo)


def parse_TODO(issue):
    body = issue.body.splitlines()
    todo_undone = [l for l in body if l.startswith("- [ ] ")]
    todo_done = [l for l in body if l.startswith("- [x] ")]
    # just add info all done
    if not todo_undone:
        return f"[{issue.title}]({issue.html_url}) all done", []
    return (
        f"[{issue.title}]({issue.html_url})--{len(todo_undone)} jobs to do--{len(todo_done)} jobs done",
        todo_done + todo_undone,
    )


def get_top_issues(repo):
    return repo.get_issues(labels=TOP_ISSUES_LABELS)


def get_todo_issues(repo):
    return repo.get_issues(labels=TODO_ISSUES_LABELS)


def get_repo_labels(repo):
    return [l for l in repo.get_labels()]


def get_issues_from_label(repo, label):
    return repo.get_issues(labels=(label,))


def add_issue_info(issue, md):
    time = format_time(issue.created_at)
    md.write(f"- [{issue.title}]({issue.html_url})--{time}\n")


def add_md_todo(repo, md, me):
    todo_issues = list(get_todo_issues(repo))
    if not TODO_ISSUES_LABELS or not todo_issues:
        return
    with open(md, "a+", encoding="utf-8") as md_file:
        md_file.write("## TODO\n")
        for issue in todo_issues:
            if is_me(issue, me):
                todo_title, todo_list = parse_TODO(issue)
                md_file.write("TODO list from " + todo_title + "\n")
                for t in todo_list:
                    md_file.write(t + "\n")
                # new line
                md_file.write("\n")


def add_md_top(repo, md, me):
    top_issues = list(get_top_issues(repo))
    if not TOP_ISSUES_LABELS or not top_issues:
        return
    with open(md, "a+", encoding="utf-8") as md_file:
        md_file.write("## 置顶文章\n")
        for issue in top_issues:
            if is_me(issue, me):
                add_issue_info(issue, md_file)


def add_md_firends(repo, md, me):
    s = FRIENDS_TABLE_HEAD
    friends_issues = list(repo.get_issues(labels=FRIENDS_LABELS))
    if not FRIENDS_LABELS or not friends_issues:
        return
    friends_issue_number = friends_issues[0].number
    for issue in friends_issues:
        for comment in issue.get_comments():
            if is_hearted_by_me(comment, me):
                try:
                    s += _make_friend_table_string(comment.body or "")
                except Exception as e:
                    print(str(e))
                    pass
    s = markdown.markdown(s, output_format="html", extensions=["extra"])
    with open(md, "a+", encoding="utf-8") as md_file:
        md_file.write(
            f"## [友情链接](https://github.com/{str(me)}/gitblog/issues/{friends_issue_number})\n"
        )
        md_file.write("<details><summary>显示</summary>\n")
        md_file.write(s)
        md_file.write("</details>\n")
        md_file.write("\n\n")


def add_md_recent(repo, md, me, limit=5):
    count = 0
    with open(md, "a+", encoding="utf-8") as md_file:
        # one the issue that only one issue and delete (pyGitHub raise an exception)
        try:
            md_file.write("## 最近更新\n")
            for issue in repo.get_issues(sort="created", direction="desc"):
                if is_me(issue, me):
                    add_issue_info(issue, md_file)
                    count += 1
                    if count >= limit:
                        break
        except Exception as e:
            print(str(e))


def add_md_header(md, repo_name):
    with open(md, "w", encoding="utf-8") as md_file:
        md_file.write(MD_HEAD.format(repo_name=repo_name))
        md_file.write("\n")


def add_md_label(repo, md, me):
    labels = get_repo_labels(repo)

    # sort lables by description info if it exists, otherwise sort by name,
    # for example, we can let the description start with a number (1#Java, 2#Docker, 3#K8s, etc.)
    labels = sorted(
        labels,
        key=lambda x: (
            x.description is None,
            x.description == "",
            x.description,
            x.name,
        ),
    )

    with open(md, "a+", encoding="utf-8") as md_file:
        for label in labels:
            # we don't need add top label again
            if label.name in IGNORE_LABELS:
                continue

            issues = get_issues_from_label(repo, label)
            issues = list(sorted(issues, key=lambda x: x.created_at, reverse=True))
            if len(issues) != 0:
                md_file.write("## " + label.name + "\n\n")
            i = 0
            for issue in issues:
                if not issue:
                    continue
                if is_me(issue, me):
                    if i == ANCHOR_
