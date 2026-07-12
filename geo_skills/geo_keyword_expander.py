#!/usr/bin/env python3
"""GEO 关键词扩展脚本 v1.0 —— 从种子关键词生成长尾搜索问题 CSV。

对标 geo_rewrite.py 架构风格，纯 Python 标准库实现。

用法:
    python3 geo_keyword_expander.py --keywords "幽门螺杆菌,治疗"
    python3 geo_keyword_expander.py --keywords "防晒霜" --count 50
    python3 geo_keyword_expander.py --keywords "Python,入门" --output 我的关键词.csv
    python3 geo_keyword_expander.py --keywords "AI,写作" --dry-run
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from io import StringIO
from pathlib import Path

# ═══════════════════════════════════════════════════
# 关键词扩展提示词
# ═══════════════════════════════════════════════════

EXPAND_SYSTEM_PROMPT = """你是一名 GEO（Generative Engine Optimization，生成式引擎优化）关键词策略专家。你的任务是根据给定的种子关键词，从用户真实搜索意图出发，生成指定数量的长尾搜索问题。

你精通 6 个搜索意图维度：
- What（是什么）：定义类问题
- Why（为什么）：原理类问题
- How（怎么做）：实操类问题
- Compare（对比）：选择类问题
- When/If（条件）：场景类问题
- Best（推荐）：榜单/推荐类问题

每个生成的问题需要附带以下评分：
- 搜索量：高/中/低（基于该问题在搜索引擎中的预估查询频次）
- AI 引用潜力：1-10（该问题被 AI 搜索引擎作为答案引用来源的概率）
- 竞争度：高/中/低（已有内容的覆盖程度，低竞争 = 蓝海机会）
- 复合分：搜索量权重 40% + AI 引用潜力权重 60% 换算为 0-100 分

要求：
- 问题来自真实用户搜索场景，不要编造不自然的问题
- 6 个意图维度尽量均衡覆盖，不要集中在某一两个维度
- 对每个问题简要说明为什么它属于该意图维度"""


def build_expand_prompt(keywords, count):
    """构建关键词扩展 prompt。"""
    return f"""请根据以下种子关键词生成 {count} 个长尾搜索问题。

种子关键词：{keywords}

每个问题附带以下字段：
- 问题：完整的用户搜索问句
- 搜索量：高/中/低
- AI引用潜力：1-10
- 竞争度：高/中/低
- 复合分：搜索量(高=90,中=60,低=30)×0.4 + AI引用潜力×6×0.6（取整）
- 意图维度：What/Why/How/Compare/When/Best

请以 Markdown 表格格式输出，表头如下：

| 问题 | 搜索量 | AI引用潜力 | 竞争度 | 复合分 | 意图维度 |

要求：
1. 问题必须来自真实用户搜索场景
2. 6 个意图维度尽量均衡分布（每个维度至少 {max(1, count // 8)} 个问题）
3. 按复合分降序排列
4. 不要输出任何表格之外的文字
"""


# ═══════════════════════════════════════════════════
# API 调用
# ═══════════════════════════════════════════════════

def build_api_request(messages):
    """构建 OpenAI 兼容 API 请求体。"""
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    return {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        "temperature": 0.8,
    }


def call_api(messages, retry=1):
    """调用 OpenAI 兼容 API，支持重试。"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retry + 1):
        try:
            payload = build_api_request(messages)
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
            return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
            except Exception:
                pass
            print(f"[API Error] HTTP {e.code}: {body.decode('utf-8', errors='replace')[:500]}", file=sys.stderr)
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


# ═══════════════════════════════════════════════════
# Markdown 表格 → CSV 解析
# ═══════════════════════════════════════════════════

def parse_markdown_table_to_csv(md_text):
    """将 Markdown 表格解析为 CSV 字符串。"""
    lines = md_text.strip().split("\n")
    data_rows = []

    for line in lines:
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # 跳过分隔行（如 |---|---|）
        if line.replace("|", "").replace("-", "").replace(" ", "").strip() == "":
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        data_rows.append(cells)

    if not data_rows:
        return ""

    # 检查第一行是否为表头（含字段名）
    header_keywords = ["问题", "搜索量", "AI引用潜力", "竞争度", "复合分"]
    header_row = data_rows[0]
    has_header = any(
        any(kw in cell for kw in header_keywords)
        for cell in header_row
    )

    output = StringIO()
    writer = csv.writer(output)

    if has_header:
        writer.writerow(["问题", "搜索量", "AI引用潜力", "竞争度", "复合分", "意图维度"])
        start_row = 1
    else:
        writer.writerow(["问题", "搜索量", "AI引用潜力", "竞争度", "复合分", "意图维度"])
        start_row = 0

    for row in data_rows[start_row:]:
        if len(row) >= 6:
            writer.writerow(row[:6])
        elif len(row) >= 1:
            writer.writerow(row + [""] * (6 - len(row)))

    return output.getvalue()


# ═══════════════════════════════════════════════════
# 核心逻辑
# ═══════════════════════════════════════════════════

def run_expand(keywords, count, output_path, dry_run, retry):
    """执行关键词扩展。"""
    if dry_run:
        print("=" * 60)
        print("[DRY RUN] 以下是将发送给 LLM 的 prompt：")
        print("=" * 60)
        print(EXPAND_SYSTEM_PROMPT)
        print()
        print(build_expand_prompt(keywords, count))
        print("=" * 60)
        print("[DRY RUN] 仅预览 prompt，未调用 API。")
        return

    messages = [
        {"role": "system", "content": EXPAND_SYSTEM_PROMPT},
        {"role": "user", "content": build_expand_prompt(keywords, count)},
    ]

    print(f"[Expand] 种子词: {keywords}")
    print(f"[Expand] 目标数量: {count}")
    print(f"[Expand] 调用 API ...")

    result = call_api(messages, retry=retry)
    print(result)

    # 解析为 CSV
    csv_content = parse_markdown_table_to_csv(result)
    if not csv_content.strip():
        print("[Error] 未能从 API 返回中解析出表格数据", file=sys.stderr)
        sys.exit(1)

    out_path = Path(output_path) if output_path else Path(f"关键词-expanded.csv")
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(csv_content, encoding="utf-8")

    # 统计
    csv_lines = [l for l in csv_content.strip().split("\n") if l.strip()]
    row_count = len(csv_lines) - 1  # 减去表头
    print(f"\n[Expand] 已生成 {row_count} 个长尾问题，保存至: {out_path}")


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="GEO 关键词扩展 —— 从种子关键词生成长尾搜索问题 CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 geo_keyword_expander.py --keywords "幽门螺杆菌,治疗"
  python3 geo_keyword_expander.py --keywords "防晒霜" --count 50
  python3 geo_keyword_expander.py --keywords "Python,入门" --output my-keywords.csv
  python3 geo_keyword_expander.py --keywords "AI,写作" --dry-run
        """,
    )
    parser.add_argument("--keywords", "-k", required=True,
                        help="种子关键词，逗号分隔（如 '幽门螺杆菌,治疗'）")
    parser.add_argument("--count", "-n", type=int, default=100,
                        help="生成长尾问题数量（默认 100）")
    parser.add_argument("--output", "-o", default=None,
                        help="输出 CSV 路径（默认 关键词-expanded.csv）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅打印 prompt，不调用 API")
    parser.add_argument("--retry", type=int, default=1,
                        help="API 调用失败重试次数（默认 1）")

    args = parser.parse_args()

    keywords = args.keywords.strip()
    if not keywords:
        print("[Error] --keywords 不能为空", file=sys.stderr)
        sys.exit(1)

    run_expand(keywords, args.count, args.output, args.dry_run, args.retry)


if __name__ == "__main__":
    main()
