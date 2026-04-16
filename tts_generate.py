#!/usr/bin/env python3
"""
Edge TTS 生成脚本
- 从 GitHub Issues 获取文章内容
- 使用 edge-tts 生成中文女声 MP3
- 上传到 Cloudflare R2（或本地模式存到 static/tts/）
- 输出 tts_cache.json 供 generate_page.py 使用

用法:
  python tts_generate.py            # R2 模式（需要 R2 环境变量）
  python tts_generate.py --local    # 本地模式（音频存到 static/tts/，无需 R2）
  python tts_generate.py --issue 17 # 只处理指定 issue
"""

import os
import re
import sys
import json
import asyncio
import argparse
import tempfile
from datetime import datetime

# --- 配置 ---
GITHUB_TOKEN = os.getenv("G_TT")
REPO_NAME = "myogg/gitblog"
VOICE = "zh-CN-XiaoxiaoNeural"
MAX_CHARS = 5000
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "gitblog-tts")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
CACHE_FILE = "tts_cache.json"
LOCAL_TTS_DIR = "static/tts"


def clean_text_for_tts(body):
    """清洗文章内容，只保留适合朗读的纯文本"""
    if not body:
        return ""

    text = body

    # 移除 YAML frontmatter
    text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)

    # 移除 tags 行
    text = re.sub(r'^tags:.*$', '', text, flags=re.MULTILINE)

    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)

    # 移除行内代码
    text = re.sub(r'`[^`]+`', '', text)

    # 移除图片（含 alt 文字，避免朗读文件名）
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 移除链接，保留文字（但丢弃纯 URL 链接）
    def replace_link(m):
        link_text = m.group(1).strip()
        link_url = m.group(2).strip()
        # 如果链接文字本身就是 URL，整段丢弃
        if re.match(r'https?://', link_text):
            return ''
        # 如果文字和 URL 一样，丢弃
        if link_text == link_url:
            return ''
        return link_text
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    # 移除裸 URL（http/https 开头的纯链接）
    text = re.sub(r'https?://\S+', '', text)

    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)

    # 移除 HTML 实体
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)

    # 移除 <!-- more --> 等注释
    text = re.sub(r'<!--.*?-->', '', text)

    # 移除 Markdown 标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 移除粗体/斜体标记
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)

    # 移除文件扩展名残留（.png .jpg .mp3 等）
    text = re.sub(r'\.\w{2,4}\b', '', text)

    # 移除纯数字编号残片（如 "3215" 单独出现的情况，但保留正文中的正常数字）
    # 仅移除行首的孤立数字（列表编号残留）
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # 移除下划线（Markdown 斜体残留或变量名）
    text = re.sub(r'_{2,}', ' ', text)

    # 移除引用标记
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # 移除列表标记
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 移除分割线
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

    # 移除特殊符号残留
    text = re.sub(r'[|>`~#$%^&+=]', ' ', text)

    # 移除多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    # 截取长度限制
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "..."

    return text
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # 截取长度限制
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "..."

    return text


def get_r2_client():
    """获取 R2 S3 兼容客户端"""
    import boto3
    from botocore.config import Config

    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(region_name="auto"),
    )
    return s3


def check_r2_exists(s3, issue_number):
    """检查 R2 中是否已有该文章的音频"""
    try:
        key = f"articles/{issue_number}.mp3"
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False


def upload_to_r2(s3, file_path, issue_number):
    """上传音频文件到 R2"""
    key = f"articles/{issue_number}.mp3"
    content_type = "audio/mpeg"

    s3.upload_file(
        file_path,
        R2_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    public_url = f"{R2_PUBLIC_URL}/{key}"
    print(f"  ✓ 上传到 R2: {public_url}")
    return public_url


def save_local(file_path, issue_number):
    """保存音频到本地 static/tts/ 目录"""
    os.makedirs(LOCAL_TTS_DIR, exist_ok=True)
    dest = os.path.join(LOCAL_TTS_DIR, f"{issue_number}.mp3")

    import shutil
    shutil.copy2(file_path, dest)

    # 本地模式的 URL 相对于站点根目录
    url = f"../static/tts/{issue_number}.mp3"
    print(f"  ✓ 保存到本地: {dest}")
    return url


async def generate_tts(text, output_path, voice=VOICE):
    """使用 edge-tts 生成音频"""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def load_cache():
    """加载现有缓存"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    """保存缓存"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Edge TTS 生成脚本")
    parser.add_argument("--local", action="store_true", help="本地模式，音频存到 static/tts/ 而非 R2")
    parser.add_argument("--issue", type=int, help="只处理指定 issue 编号")
    parser.add_argument("--regenerate", action="store_true", help="强制重新生成，即使音频已存在")
    args = parser.parse_args()

    local_mode = args.local
    target_issue = args.issue

    print("=" * 50)
    print(f"Edge TTS 生成脚本 ({'本地模式' if local_mode else 'R2 模式'})")
    print("=" * 50)

    # 检查 GitHub Token
    if not GITHUB_TOKEN:
        print("❌ 缺少环境变量 G_TT (GitHub Token)")
        print("  设置方式: set G_TT=你的token (Windows) 或 export G_TT=你的token (Linux/Mac)")
        save_cache({})
        return

    # R2 模式检查环境变量
    if not local_mode:
        missing = []
        for var_name, var_val in [
            ("R2_ACCOUNT_ID", R2_ACCOUNT_ID),
            ("R2_ACCESS_KEY_ID", R2_ACCESS_KEY_ID),
            ("R2_SECRET_ACCESS_KEY", R2_SECRET_ACCESS_KEY),
            ("R2_PUBLIC_URL", R2_PUBLIC_URL),
        ]:
            if not var_val:
                missing.append(var_name)

        if missing:
            print(f"⚠️ 缺少 R2 环境变量: {', '.join(missing)}")
            print("  提示: 使用 --local 参数可在本地模式运行，无需 R2")
            save_cache({})
            return

    # 获取 GitHub Issues
    from github import Github

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    all_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]

    # 过滤指定 issue
    if target_issue:
        issues = [i for i in all_issues if i.number == target_issue]
        if not issues:
            print(f"❌ 未找到 issue #{target_issue}")
            return
    else:
        issues = all_issues

    print(f"找到 {len(issues)} 个 issues")

    # R2 客户端（仅 R2 模式）
    s3 = None
    if not local_mode:
        s3 = get_r2_client()

    # 加载缓存
    cache = load_cache()

    # 处理每篇文章
    success_count = 0
    skip_count = 0
    fail_count = 0

    for issue in issues:
        num = str(issue.number)
        print(f"\n处理 #{num}: {issue.title[:40]}...")

        # 检查是否已存在（非 --regenerate 时跳过）
        if not args.regenerate:
            if local_mode:
                local_path = os.path.join(LOCAL_TTS_DIR, f"{num}.mp3")
                if os.path.exists(local_path):
                    cache[num] = f"../static/tts/{num}.mp3"
                    print(f"  ⏭️ 本地已存在，跳过")
                    skip_count += 1
                    continue
            else:
                try:
                    if check_r2_exists(s3, num):
                        url = f"{R2_PUBLIC_URL}/articles/{num}.mp3"
                        cache[num] = url
                        print(f"  ⏭️ R2 已存在，跳过")
                        skip_count += 1
                        continue
                except Exception as e:
                    print(f"  ⚠️ R2 检查失败: {e}，继续生成")

        # 清洗文本
        text = clean_text_for_tts(issue.body)
        if not text or len(text.strip()) < 10:
            print(f"  ⏭️ 内容过短，跳过")
            continue

        # 生成 TTS
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            print(f"  🎙️ 生成音频 (voice={VOICE}, {len(text)} 字)...")
            asyncio.run(generate_tts(text, tmp_path))

            # 存储音频
            if local_mode:
                url = save_local(tmp_path, num)
            else:
                url = upload_to_r2(s3, tmp_path, num)

            cache[num] = url
            success_count += 1

            # 清理临时文件
            os.unlink(tmp_path)

        except Exception as e:
            print(f"  ❌ 生成失败: {e}")
            fail_count += 1
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # 保存缓存
    save_cache(cache)

    print(f"\n{'=' * 50}")
    print(f"TTS 生成完成:")
    print(f"  模式: {'本地' if local_mode else 'R2'}")
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  失败: {fail_count}")
    print(f"  缓存: {CACHE_FILE} ({len(cache)} 条)")
    if local_mode:
        print(f"  音频目录: {LOCAL_TTS_DIR}/")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
