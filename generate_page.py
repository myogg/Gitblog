import os
import re
import json
import markdown
import shutil
from github import Github
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# --- 配置區 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/Gitblog"
MAX_PER_CATEGORY = 5
CACHE_FILE = "github_cache.json"
CACHE_DURATION = 21600  # 6小时
ARTICLES_DIR = "articles"

# 初始化 Jinja2 模板引擎
env = Environment(loader=FileSystemLoader('templates'))

def get_text_color(hex_color):
    """根據背景色亮度決定文字顏色"""
    try:
        # 确保hex_color是6位格式
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 128 else "#000000"
    except Exception:
        return "#000000"

def generate_safe_name(label_name, existing_names=None):
    """生成唯一的 safe_name"""
    if existing_names is None:
        existing_names = set()

    # 1. 将非字母数字字符替换为短横线
    safe = re.sub(r'[^a-zA-Z0-9]', '-', label_name).lower()
    # 2. 合并连续的短横线为一个
    safe = re.sub(r'-+', '-', safe)
    # 3. 去除首尾的短横线
    safe = safe.strip('-')

    # 4. 如果为空，使用默认值
    if not safe:
        safe = 'label'

    # 5. 确保唯一性：如果已存在，添加数字后缀
    original_safe = safe
    counter = 1
    while safe in existing_names:
        safe = f"{original_safe}-{counter}"
        counter += 1

    return safe

def extract_content_tags(body):
    """从文章内容中提取标签（不创建GitHub Label）

    支持两种格式：
    1. 简单格式: tags: Python, AI, 机器学习
    2. YAML frontmatter:
       ---
       tags: Python, AI, 机器学习
       ---

    返回: (标签列表, 清理后的内容)
    """
    if not body:
        return [], body

    tags = []
    cleaned_body = body

    # 方式1: 检查YAML frontmatter格式
    yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    yaml_match = re.match(yaml_pattern, body, re.DOTALL)

    if yaml_match:
        frontmatter = yaml_match.group(1)
        # 提取tags行
        tags_match = re.search(r'tags:\s*(.+)', frontmatter, re.IGNORECASE)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            # 分割标签（支持逗号或中文逗号分隔）
            tags = [t.strip() for t in re.split(r'[,，]\s*', tags_str) if t.strip()]
        # 移除frontmatter
        cleaned_body = re.sub(yaml_pattern, '', body, count=1)

    # 方式2: 检查简单格式（文章开头的tags: ...）
    else:
        simple_pattern = r'^tags:\s*(.+?)(?:\n|$)'
        simple_match = re.match(simple_pattern, body, re.IGNORECASE | re.MULTILINE)

        if simple_match:
            tags_str = simple_match.group(1).strip()
            # 分割标签
            tags = [t.strip() for t in re.split(r'[,，]\s*', tags_str) if t.strip()]
            # 移除tags行
            cleaned_body = re.sub(simple_pattern, '', body, count=1).lstrip()

    return tags, cleaned_body

def extract_summary(body):
    """提取手动设置的文章摘要（仅支持 <!-- more --> 分隔符）"""
    if not body:
        return None

    # 检查是否有手动摘要分隔符
    if "<!-- more -->" in body:
        summary = body.split("<!-- more -->")[0].strip()
        return summary if summary else None

    # 没有分隔符则不显示摘要
    return None

def add_lazy_loading_to_images(html_content):
    """为HTML内容中的图片添加懒加载功能"""
    if not html_content:
        return html_content

    # 匹配所有img标签
    img_pattern = r'<img\s+([^>]*?)src="([^"]+)"([^>]*?)>'

    def replace_img(match):
        before_src = match.group(1)
        src_url = match.group(2)
        after_src = match.group(3)

        # 检查是否已经有loading属性
        if 'loading=' in before_src or 'loading=' in after_src:
            return match.group(0)  # 已有loading属性，不修改

        # 添加loading="lazy"属性和lazyload类
        new_img = f'<img {before_src}src="{src_url}" loading="lazy" class="lazyload"{after_src}>'
        return new_img

    # 替换所有img标签
    result = re.sub(img_pattern, replace_img, html_content)
    return result

def find_prev_next_articles(current_issue, all_issues):
    """查找上一篇和下一篇文章（按时间排序）"""
    # 过滤掉pinned文章，按创建时间排序（最新的在前）
    sorted_issues = sorted(
        [i for i in all_issues if not any(l.name.lower() == "pinned" for l in i.labels)],
        key=lambda x: x.created_at,
        reverse=True
    )

    try:
        current_index = next(i for i, issue in enumerate(sorted_issues) if issue.number == current_issue.number)
    except StopIteration:
        return None, None

    # 上一篇 = 时间更早的 (索引+1)
    prev_article = sorted_issues[current_index + 1] if current_index + 1 < len(sorted_issues) else None
    # 下一篇 = 时间更晚的 (索引-1)
    next_article = sorted_issues[current_index - 1] if current_index - 1 >= 0 else None

    return prev_article, next_article

def find_related_articles(current_issue, all_issues, max_count=2):
    """基于标签相似度推荐相关文章"""
    current_labels = set(l.name for l in current_issue.labels if l.name.lower() != "pinned")

    if not current_labels:
        return []

    # 计算每篇文章的相似度分数
    related = []
    for issue in all_issues:
        if issue.number == current_issue.number:
            continue

        issue_labels = set(l.name for l in issue.labels if l.name.lower() != "pinned")

        # 计算标签交集数量作为相似度
        common_labels = current_labels & issue_labels
        if common_labels:
            score = len(common_labels)
            related.append((issue, score))

    # 按相似度排序（相同分数按时间倒序），取前max_count篇
    related.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
    return [issue for issue, score in related[:max_count]]

def login():
    if not GITHUB_TOKEN:
        print("Error: G_TT token not found.")
        exit(1)
    return Github(GITHUB_TOKEN)

def fetch_issues(repo):
    """獲取並緩存 Issues"""
    # 檢查緩存
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(seconds=CACHE_DURATION):
                    print("使用緩存數據...")
                    # 創建模擬Issue對象
                    issues = []
                    for item in cache_data['issues']:
                        # 創建動態對象
                        issue = type('Issue', (), {
                            'number': item['number'],
                            'title': item['title'],
                            'body': item['body'],
                            'created_at': datetime.fromisoformat(item['created_at']),
                            'labels': [type('Label', (), {
                                'name': l['name'],
                                'color': l['color']
                            })() for l in item['labels']]
                        })()
                        issues.append(issue)
                    return issues
        except Exception as e:
            print(f"緩存讀取失敗: {e}")

    print("從GitHub獲取最新數據...")
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]

    # 保存緩存
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'issues': [{
            'number': i.number,
            'title': i.title,
            'body': i.body,
            'created_at': i.created_at.isoformat(),
            'labels': [{'name': l.name, 'color': l.color} for l in i.labels]
        } for i in all_issues]
    }

    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 緩存已保存: {CACHE_FILE}")
    except Exception as e:
        print(f"緩存保存失敗: {e}")

    return all_issues

def sort_issues(issue_list):
    """按创建时间倒序排序（最新的在前）"""
    return sorted(issue_list, key=lambda x: x.created_at, reverse=True)

def generate_search_index(issues):
    """生成搜索索引"""
    search_data = []
    for issue in issues:
        # 提取内容标签
        content_tags, cleaned_body = extract_content_tags(issue.body)

        # 清理HTML标签，获取纯文本内容
        clean_content = re.sub(r'<[^>]+>', '', cleaned_body or "")
        # 去除多余空格和换行
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()

        # 合并GitHub标签和内容标签
        all_tags = [label.name for label in issue.labels if label.name.lower() != "pinned"] + content_tags

        search_data.append({
            'id': issue.number,
            'title': issue.title,
            'content': clean_content[:500],  # 截取前500字符
            'date': issue.created_at.strftime('%Y-%m-%d'),
            'url': f'articles/article-{issue.number}.html',
            'tags': all_tags
        })

    # 保存到static目录
    os.makedirs("static", exist_ok=True)
    output_path = os.path.join("static", "search-index.json")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 搜索索引已生成: {output_path}")
    except Exception as e:
        print(f"❌ 生成搜索索引失敗: {e}")

    return search_data

def generate_sitemap(issues):
    """生成 sitemap.xml"""
    try:
        base_url = "https://134688.xyz"

        # XML 头部
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

        # 主页
        xml_content.append('  <url>')
        xml_content.append(f'    <loc>{base_url}/</loc>')
        xml_content.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        xml_content.append('    <changefreq>daily</changefreq>')
        xml_content.append('    <priority>1.0</priority>')
        xml_content.append('  </url>')

        # 搜索页
        xml_content.append('  <url>')
        xml_content.append(f'    <loc>{base_url}/search.html</loc>')
        xml_content.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        xml_content.append('    <changefreq>weekly</changefreq>')
        xml_content.append('    <priority>0.8</priority>')
        xml_content.append('  </url>')

        # 关于页
        xml_content.append('  <url>')
        xml_content.append(f'    <loc>{base_url}/about.html</loc>')
        xml_content.append(f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        xml_content.append('    <changefreq>monthly</changefreq>')
        xml_content.append('    <priority>0.7</priority>')
        xml_content.append('  </url>')

        # 文章页面
        for issue in issues:
            xml_content.append('  <url>')
            xml_content.append(f'    <loc>{base_url}/articles/article-{issue.number}.html</loc>')
            xml_content.append(f'    <lastmod>{issue.created_at.strftime("%Y-%m-%d")}</lastmod>')
            xml_content.append('    <changefreq>monthly</changefreq>')
            xml_content.append('    <priority>0.9</priority>')
            xml_content.append('  </url>')

        xml_content.append('</urlset>')

        # 写入文件
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('\n'.join(xml_content))

        print(f"✓ Sitemap 已生成: sitemap.xml ({len(issues)} 篇文章)")

    except Exception as e:
        print(f"❌ 生成 Sitemap 失敗: {e}")

def generate_robots_txt():
    """生成 robots.txt"""
    try:
        robots_content = [
            "# robots.txt for 134688.xyz",
            "User-agent: *",
            "Allow: /",
            "",
            "# Sitemap location",
            "Sitemap: https://134688.xyz/sitemap.xml",
            "",
            "# Crawl-delay for polite crawling",
            "Crawl-delay: 1"
        ]

        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write('\n'.join(robots_content))

        print("✓ robots.txt 已生成")

    except Exception as e:
        print(f"❌ 生成 robots.txt 失敗: {e}")

def generate_article_page(issue, all_issues, giscus_config=None, label_info=None):
    """生成文章页面"""
    try:
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        template = env.get_template('article.html')

        # 先提取内容标签
        content_tags, cleaned_body = extract_content_tags(issue.body)

        # 转换Markdown为HTML（使用清理后的内容）
        html_content = markdown.markdown(
            cleaned_body or "暫無內容",
            extensions=['extra', 'codehilite', 'tables', 'fenced_code']
        )

        # 添加图片懒加载
        html_content = add_lazy_loading_to_images(html_content)

        # 处理GitHub标签
        existing_safe_names = set()
        labels_data = []
        for l in issue.labels:
            if l.name.lower() != "pinned":
                safe_name = generate_safe_name(l.name, existing_safe_names)
                existing_safe_names.add(safe_name)
                # 尝试从 label_info 获取 safe_name
                if label_info and l.name in label_info:
                    safe_name = label_info[l.name].get('safe_name', safe_name)
                labels_data.append({
                    "name": l.name,
                    "color": l.color,
                    "text_color": get_text_color(l.color),
                    "safe_name": safe_name
                })

        # 处理内容标签（从 label_info 获取 safe_name）
        content_tags_data = []
        for tag in content_tags:
            tag_data = {"name": tag}
            if label_info and tag in label_info:
                tag_data["safe_name"] = label_info[tag].get('safe_name')
            content_tags_data.append(tag_data)

        # 默认的Giscus配置
        default_giscus_config = {
            'repo': 'myogg/Gitblog',
            'repo_id': os.getenv('GISCUS_REPO_ID', ''),  # 从环境变量获取
            'category': 'General',
            'category_id': os.getenv('GISCUS_CATEGORY_ID', ''),
            'theme': 'light',
            'lang': 'zh-CN'
        }

        # 使用传入的配置或默认配置
        giscus_config = giscus_config or default_giscus_config

        # 检查Giscus配置
        if not giscus_config.get('repo_id'):
            print(f"⚠️ 文章 #{issue.number}: Giscus repo_id 未配置，评论系统将不可用")

        # 查找上下文和相关文章
        prev_article, next_article = find_prev_next_articles(issue, all_issues)
        related_articles = find_related_articles(issue, all_issues)

        # 渲染模板
        output = template.render(
            issue=issue,
            content=html_content,
            labels_data=labels_data,
            content_tags=content_tags_data,
            prev_article=prev_article,
            next_article=next_article,
            related_articles=related_articles,
            YEAR=datetime.now().year,
            giscus_config=giscus_config
        )

        # 写入文件
        output_file = os.path.join(ARTICLES_DIR, f"article-{issue.number}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"✓ 生成文章: {issue.title} (#{issue.number})")

    except Exception as e:
        print(f"❌ 生成文章 #{issue.number} 失败: {e}")

def main():
    print("開始生成GitBlog頁面...")
    print(f"倉庫: {REPO_NAME}")

    # 檢查模板目錄
    if not os.path.exists('templates'):
        print("❌ 錯誤: templates 目錄不存在")
        exit(1)

    required_templates = ['base.html', 'article.html']
    for template in required_templates:
        if not os.path.exists(f'templates/{template}'):
            print(f"❌ 錯誤: 缺少必要模板文件 {template}")
            exit(1)

    g = login()
    repo = g.get_repo(REPO_NAME)
    issues = fetch_issues(repo)

    if not issues:
        print("❌ 未找到任何issues")
        exit(1)

    print(f"找到 {len(issues)} 個issues")

    # 为所有文章添加摘要字段（必须在使用前添加）
    for issue in issues:
        issue.summary = extract_summary(issue.body)

    # --- 數據整理 ---
    label_dict = {}
    label_info = {}
    articles_by_year = {}

    # 收集所有唯一的标签并生成唯一的 safe_name，同时按年份分组
    existing_safe_names = set()
    for issue in issues:
        year = issue.created_at.strftime('%Y')
        articles_by_year.setdefault(year, []).append(issue)
        for label in issue.labels:
            if label.name.lower() == "pinned":
                continue
            label_dict.setdefault(label.name, []).append(issue)
            if label.name not in label_info:
                safe_name = generate_safe_name(label.name, existing_safe_names)
                existing_safe_names.add(safe_name)
                label_info[label.name] = {
                    "color": label.color,
                    "text_color": get_text_color(label.color),
                    "safe_name": safe_name
                }

    # 排序每个年份下的文章（按时间倒序）
    for year in articles_by_year:
        articles_by_year[year] = sort_issues(articles_by_year[year])

    # 排序每個標籤下的文章
    for label in label_dict:
        label_dict[label] = sort_issues(label_dict[label])

    sorted_years = sorted(articles_by_year.keys(), reverse=True)
    print(f"文章年份分佈: {', '.join(sorted_years)}")
    print(f"找到 {len(label_dict)} 個標籤")

    # --- 生成搜索索引 ---
    generate_search_index(issues)

    # --- 配置Giscus评论系统 ---
    giscus_config = {
        'repo': 'myogg/Gitblog',
        'repo_id': os.getenv('GISCUS_REPO_ID', ''),
        'category': 'Announcements',
        'category_id': os.getenv('GISCUS_CATEGORY_ID', ''),
        'theme': 'light',
        'lang': 'zh-CN'
    }

    # 檢查Giscus配置
    if not giscus_config['repo_id']:
        print("⚠️ 注意: Giscus repo_id 未配置，评论系统将不可用")
        print("  请访问 https://giscus.app 获取配置，并设置环境变量:")
        print("  GISCUS_REPO_ID=你的repo_id")
        print("  GISCUS_CATEGORY_ID=你的category_id")

    # --- 收集内容标签（在生成文章前） ---
    print("收集內容標籤...")
    content_tags_dict = {}  # {tag_name: [issue1, issue2, ...]}
    for issue in issues:
        content_tags, _ = extract_content_tags(issue.body)
        for tag in content_tags:
            if tag not in content_tags_dict:
                content_tags_dict[tag] = []
            content_tags_dict[tag].append(issue)

    # 为内容标签生成 safe_name（添加到 label_info 中）
    for tag in content_tags_dict:
        if tag not in label_info:  # 避免与GitHub标签重名
            safe_name = generate_safe_name(tag, existing_safe_names)
            existing_safe_names.add(safe_name)
            label_info[tag] = {
                "color": None,  # 内容标签没有颜色
                "text_color": None,
                "safe_name": safe_name
            }
        # 排序该标签下的文章
        content_tags_dict[tag] = sort_issues(content_tags_dict[tag])

    print(f"找到 {len(content_tags_dict)} 個內容標籤")

    # --- 生成文章頁面（传入 label_info） ---
    print("開始生成文章頁面...")
    for issue in issues:
        generate_article_page(issue, issues, giscus_config, label_info)

    # --- 生成标签页面 ---
    print("開始生成標籤頁面...")
    os.makedirs("tags", exist_ok=True)

    # 合并所有标签
    all_tags_dict = {**label_dict, **content_tags_dict}

    for tag_name, tag_articles in all_tags_dict.items():
        try:
            tag_template = env.get_template('tag.html')
            tag_info = label_info.get(tag_name, {})
            tag_html = tag_template.render(
                tag_name=tag_name,
                tag_color=tag_info.get('color'),
                articles=tag_articles,
                YEAR=datetime.now().year
            )

            safe_name = tag_info.get('safe_name', generate_safe_name(tag_name, set()))
            output_file = os.path.join("tags", f"{safe_name}.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(tag_html)
            print(f"✓ 生成標籤頁: {tag_name} ({len(tag_articles)} 篇文章)")
        except Exception as e:
            print(f"❌ 生成標籤頁 '{tag_name}' 失敗: {e}")

    # --- 生成标签总览页面 --- (已禁用，用户不需要导航栏标签入口)
    # print("生成標籤總覽頁...")
    # try:
    #     tags_template = env.get_template('tags.html')
    #     ...
    # except Exception as e:
    #     print(f"❌ 生成標籤總覽頁失敗: {e}")

    # 1. 生成主頁（按年份分组显示）
    print("生成主頁...")
    try:
        index_template = env.get_template('base.html')
        index_html = index_template.render(
            articles_by_year=articles_by_year,
            YEAR=datetime.now().year
        )
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(index_html)
        print("✓ 主頁已生成")
    except Exception as e:
        print(f"❌ 生成主頁失敗: {e}")

    # 2. 生成搜索頁
    if os.path.exists('templates/search.html'):
        print("生成搜索頁...")
        try:
            search_template = env.get_template('search.html')
            search_html = search_template.render(
                YEAR=datetime.now().year,
                label_info=label_info
            )
            with open("search.html", "w", encoding="utf-8") as f:
                f.write(search_html)
            print("✓ 搜索頁已生成")
        except Exception as e:
            print(f"⚠️ 生成搜索頁失敗: {e}")
    else:
        print("⏭️ 跳過搜索頁生成 (模板不存在)")

    # 3. 生成關於頁
    if os.path.exists('templates/about.html'):
        print("生成關於頁...")
        try:
            about_template = env.get_template('about.html')
            about_html = about_template.render(YEAR=datetime.now().year)
            with open("about.html", "w", encoding="utf-8") as f:
                f.write(about_html)
            print("✓ 關於頁已生成")
        except Exception as e:
            print(f"⚠️ 生成關於頁失敗: {e}")
    else:
        print("⏭️ 跳過關於頁生成 (模板不存在)")

    # 4. 生成 SEO 文件
    print("生成 SEO 文件...")
    generate_sitemap(issues)
    generate_robots_txt()


    # 複製靜態資源
    print("複製靜態資源...")
    os.makedirs("static", exist_ok=True)

    static_files = ["style.css"]
    for f in static_files:
        src = os.path.join("templates", f)
        if os.path.exists(src):
            try:
                shutil.copy(src, f"static/{f}")
                print(f"✓ 複製靜態文件: {f}")
            except Exception as e:
                print(f"⚠️ 複製 {f} 失敗: {e}")
        else:
            print(f"⏭️ 跳過 {f} (文件不存在)")

    print("\n🎉 任務完成！")
    print(f"已生成 {len(issues)} 篇文章")
    print(f"靜態資源位置: static/")
    print(f"文章目錄: {ARTICLES_DIR}/")

if __name__ == "__main__":
    main()
