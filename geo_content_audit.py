#!/usr/bin/env python3
"""GEO 内容审计脚本 v1.0 —— 调用 OpenAI 兼容 API，逐段标注 GEO 特征并输出六维评分卡。

对标 geo_rewrite.py 架构风格，纯 Python 标准库实现。

用法:
    python3 geo_content_audit.py --input 文章.md
    python3 geo_content_audit.py --input 文章.md --output 审计报告.md
    python3 geo_content_audit.py --input 文章.md --dry-run
    python3 geo_content_audit.py --input 文章.md --retry 3
    python3 geo_content_audit.py --input 文章.md --stream
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ═══════════════════════════════════════════════════
# GEO 审计提示词（内嵌为字符串常量）
# ═══════════════════════════════════════════════════

AUDIT_SYSTEM_PROMPT = """你是一名 GEO（Generative Engine Optimization，生成式引擎优化）内容审计专家。你的任务是对一篇给定的文章进行 GEO 特征审计，逐段标注其 AI 搜索引擎友好度，并输出结构化评分卡和改进清单。

审计符号：
- ✅ 做得好的：已符合 GEO 最佳实践的点
- ⚠️ 可改进的：尚未达到 GEO 标准的点
- 💡 具体建议：如何改进以提升 AI 搜索引擎引用率

你理解的 GEO 五维规则：
1. 问答结构化——前 150 字是否直接回答核心问题
2. 实体植入——品牌/产品/方法论实体在正文中出现的密度和自然度
3. 引用锚点——数据和结论是否标注来源（机构 + 年份 + 报告名称）
4. 结构化标记——H2/H3 标题 + 列表 + 加粗关键词 + FAQ 的使用情况
5. 关键词覆盖——核心关键词在标题、首段、H2 标题中的分布

六维评分卡（第 6 维可读性替代第 5 维在审计时的位置，实际六维为：问答可见性/实体密度/引用锚点/结构化/关键词覆盖/可读性）"""

AUDIT_INSTRUCTION = """
请对以下文章执行 GEO 审计，输出三部分：

## 第一部分：逐段标注

按文章的自然段落结构，对每段标注：
- ✅ 符合 GEO 最佳实践的点（如有）
- ⚠️ 可改进的地方（如有）
- 💡 具体改进建议（如有）

标注风格参考——每条标注用一行简述 + 用 `<!-- GEO标注: ... -->` 的注释格式包裹。每个 ⚠️ 必须跟一个 💡 建议。

## 第二部分：六维评分卡

| 维度 | 分数 | 说明 |
|------|------|------|
| 问答可见性 | ?/10 | 前 150 字是否直接回答核心问题 |
| 实体密度 | ?/10 | 品牌实体在正文中出现次数和自然度 |
| 引用锚点 | ?/10 | 数据/结论是否标注来源（机构+年份+报告名） |
| 结构化 | ?/10 | H2/H3/列表/FAQ 使用情况 |
| 关键词覆盖 | ?/10 | 核心关键词在标题/首段/H2 中是否出现 |
| 可读性 | ?/10 | 人类读者的阅读流畅度 |

总分 ?/60。评级：50-60 优秀 / 42-49 合格 / 30-41 不足 / <30 几乎不会被引用。

## 第三部分：优先级改进清单

| 优先级 | 改动 | 预期效果 |
|--------|------|----------|
| 🔴 高 | ... | ... |
| 🟡 中 | ... | ... |
| 🟢 低 | ... | ... |
"""


# ═══════════════════════════════════════════════════
# API 调用
# ═══════════════════════════════════════════════════

def build_api_request(messages, stream=False, max_tokens=16000):
    """构建 OpenAI 兼容 API 请求体。"""
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    return {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": stream,
    }


def call_api(messages, stream=False, retry=1):
    """调用 OpenAI 兼容 API，支持重试和流式输出。"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retry + 1):
        try:
            payload = build_api_request(messages, stream=stream)
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

            if stream:
                return _handle_stream_response(req, attempt, retry)
            else:
                return _handle_normal_response(req, attempt, retry)
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:
                pass
            print(f"[API Error] HTTP {e.code}: {body[:500]}", file=sys.stderr)
            if attempt < retry:
                wait = 2 ** attempt
                print(f"[Retry] 等待 {wait}s 后重试 ({attempt}/{retry})...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            print(f"[API Error] {e}", file=sys.stderr)
            if attempt < retry:
                wait = 2 ** attempt
                print(f"[Retry] 等待 {wait}s 后重试 ({attempt}/{retry})...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise

    return ""


def _handle_normal_response(req, attempt, retry):
    """处理非流式 API 响应。"""
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = resp.read().decode("utf-8")
        result = json.loads(body)
    return result["choices"][0]["message"]["content"]


def _handle_stream_response(req, attempt, retry):
    """处理流式 API 响应，实时打印并累积返回。"""
    full_content = []
    with urllib.request.urlopen(req, timeout=600) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                try:
                    chunk = json.loads(line[6:])
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        sys.stdout.write(content)
                        sys.stdout.flush()
                        full_content.append(content)
                except json.JSONDecodeError:
                    continue
    sys.stdout.write("\n")
    return "".join(full_content)


# ═══════════════════════════════════════════════════
# 核心逻辑
# ═══════════════════════════════════════════════════

def read_article(file_path):
    """读取文章内容。"""
    path = Path(file_path)
    if not path.exists():
        print(f"[Error] 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def build_audit_prompt(article):
    """构建审计 prompt。"""
    return f"{AUDIT_INSTRUCTION}\n\n---\n\n## 待审计文章\n\n{article}"


def run_audit(input_path, output_path, dry_run, retry, stream):
    """执行完整的审计流程。"""
    article = read_article(input_path)

    if dry_run:
        print("=" * 60)
        print("[DRY RUN] 以下是将发送给 LLM 的 prompt：")
        print("=" * 60)
        print(AUDIT_SYSTEM_PROMPT)
        print()
        print(build_audit_prompt(article))
        print("=" * 60)
        print("[DRY RUN] 仅预览 prompt，未调用 API。")
        return

    messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user", "content": build_audit_prompt(article)},
    ]

    print(f"[Audit] 开始审计: {input_path}")
    if stream:
        print("[Audit] 流式输出:")
        print("---")

    result = call_api(messages, stream=stream, retry=retry)

    if not stream:
        print(result)

    output = output_path or f"{Path(input_path).stem}-audit.md"
    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header = f"> 原文: {Path(input_path).resolve()}\n> 审计时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    out_path.write_text(header + result, encoding="utf-8")

    print(f"\n[Audit] 审计报告已保存: {out_path}")


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="GEO 内容审计 —— 逐段标注 GEO 特征，输出六维评分卡",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 geo_content_audit.py --input article.md
  python3 geo_content_audit.py --input article.md --output audit-report.md
  python3 geo_content_audit.py --input article.md --dry-run
  python3 geo_content_audit.py --input article.md --retry 3 --stream
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="待审计文章的路径（.md）")
    parser.add_argument("--output", "-o", default=None, help="输出路径（默认 原名-audit.md）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 prompt，不调用 API")
    parser.add_argument("--retry", type=int, default=1, help="API 调用失败自动重试次数（默认 1）")
    parser.add_argument("--stream", action="store_true", help="启用流式输出")

    args = parser.parse_args()
    run_audit(args.input, args.output, args.dry_run, args.retry, args.stream)


if __name__ == "__main__":
    main()
