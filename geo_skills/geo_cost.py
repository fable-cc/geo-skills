#!/usr/bin/env python3
"""
GEO 用量/成本估算器 — 估算单篇或批量改写的 token 消耗和费用

用法：
  python3 geo_cost.py --input 文章.md
  python3 geo_cost.py --input-dir ./articles
  python3 geo_cost.py --keywords "AI工具" --count 100 --top 10
  python3 geo_cost.py --input 文章.md --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any

# ---- Pricing Table (per 1M tokens) ----
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini":       {"input": 0.15,  "output": 0.60},
    "gpt-4o":            {"input": 2.50,  "output": 10.00},
    "deepseek-v3":       {"input": 0.27,  "output": 1.10},
    "claude-3.5-sonnet": {"input": 3.00,  "output": 15.00},
}

# Model human-readable names
MODEL_NAMES: dict[str, str] = {
    "gpt-4o-mini":       "GPT-4o Mini",
    "gpt-4o":            "GPT-4o",
    "deepseek-v3":       "DeepSeek V3",
    "claude-3.5-sonnet": "Claude 3.5 Sonnet",
}

# Average article length for estimation
AVG_ARTICLE_CHARS = 1500

# Token estimation: Chinese ~1.5 chars per token
CHARS_PER_TOKEN = 1.5

# Prompt overhead (system prompt + instructions in geo_rewrite.py / geo_keyword_expander.py)
REWRITE_PROMPT_OVERHEAD_CHARS = 6000   # ~4000 tokens
AUDIT_PROMPT_OVERHEAD_CHARS = 5000     # ~3333 tokens
EXPAND_PROMPT_OVERHEAD_CHARS = 3000    # ~2000 tokens


def chars_to_tokens(chars: int) -> int:
    return int(chars / CHARS_PER_TOKEN)


def estimate_single(article_path: str, model_name: str) -> Any:
    """Estimate cost for rewriting a single article."""
    if not os.path.isfile(article_path):
        return None

    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()

    article_chars = len(content)
    article_tokens = chars_to_tokens(article_chars)

    # Rewrite
    input_tokens_rw = chars_to_tokens(REWRITE_PROMPT_OVERHEAD_CHARS + article_chars)
    output_tokens_rw = int(input_tokens_rw * 1.3)
    cost_rw_input = input_tokens_rw / 1_000_000 * PRICING[model_name]["input"]
    cost_rw_output = output_tokens_rw / 1_000_000 * PRICING[model_name]["output"]
    cost_rw = cost_rw_input + cost_rw_output

    # Audit
    input_tokens_au = chars_to_tokens(AUDIT_PROMPT_OVERHEAD_CHARS + article_chars)
    output_tokens_au = int(input_tokens_au * 0.8)
    cost_au_input = input_tokens_au / 1_000_000 * PRICING[model_name]["input"]
    cost_au_output = output_tokens_au / 1_000_000 * PRICING[model_name]["output"]
    cost_au = cost_au_input + cost_au_output

    total_cost = cost_rw + cost_au

    return {
        "file": os.path.basename(article_path),
        "chars": article_chars,
        "tokens": article_tokens,
        "rewrite": {
            "input_tokens": input_tokens_rw,
            "output_tokens": output_tokens_rw,
            "cost": cost_rw,
        },
        "audit": {
            "input_tokens": input_tokens_au,
            "output_tokens": output_tokens_au,
            "cost": cost_au,
        },
        "total_cost": total_cost,
    }


def cmd_input(args: argparse.Namespace) -> None:
    """Estimate single article cost across all models or a specific model."""
    models = [args.model] if args.model else list(PRICING.keys())

    if not os.path.isfile(args.input):
        print(f"[ERROR] 文件未找到: {args.input}", file=sys.stderr)
        sys.exit(1)

    file_name = os.path.basename(args.input)
    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()
    article_chars = len(content)
    article_tokens = chars_to_tokens(article_chars)

    print(f"\n单篇成本估算: {file_name}")
    print(f"  文章长度: {article_chars} 字符 ≈ {article_tokens} tokens")
    print()

    # Table header
    print(f"{'模型':<20} {'改写输入':>10} {'改写输出':>10} {'改写费用':>10} {'审计费用':>10} {'单篇费用':>10}")
    print("-" * 80)

    for model in models:
        est = estimate_single(args.input, model)
        if est is None:
            continue
        print(f"{model:<20} {est['rewrite']['input_tokens']:>10} {est['rewrite']['output_tokens']:>10} "
              f"${est['rewrite']['cost']:>9.4f} ${est['audit']['cost']:>9.4f} ${est['total_cost']:>9.4f}")

    print("-" * 80)

    # Summary row (cheapest)
    all_ests = [(m, estimate_single(args.input, m)) for m in models]
    all_ests = [(m, e) for m, e in all_ests if e is not None]
    if all_ests:
        cheapest = min(all_ests, key=lambda x: x[1]["total_cost"])
        most_expensive = max(all_ests, key=lambda x: x[1]["total_cost"])
        print(f"\n  最省钱: {cheapest[0]} — ${cheapest[1]['total_cost']:.4f}/篇")
        print(f"  最贵:   {most_expensive[0]} — ${most_expensive[1]['total_cost']:.4f}/篇")

    # Batch projection: 100 articles
    print(f"\n  批量估算 (×100 篇):")
    for m, e in all_ests:
        print(f"    {m:<20} ${e['total_cost'] * 100:>8.2f}")


def cmd_input_dir(args: argparse.Namespace) -> None:
    """Estimate cost for a batch of articles in a directory."""
    if not os.path.isdir(args.input_dir):
        print(f"[ERROR] 目录未找到: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    files = [f for f in os.listdir(args.input_dir)
             if os.path.splitext(f)[1].lower() in (".md", ".txt")]
    files = [os.path.join(args.input_dir, f) for f in files]

    if not files:
        print("目录中没有 .md / .txt 文件。")
        return

    models = [args.model] if args.model else list(PRICING.keys())

    print(f"\n批量成本估算: {args.input_dir}")
    print(f"  文件数: {len(files)}")
    print()

    print(f"{'模型':<20} {'文章数':>6} {'总字符':>10} {'单篇均费':>10} {'批量总费':>10}")
    print("-" * 66)

    all_chars = 0
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            all_chars += len(f.read())

    for model in models:
        total_cost = 0.0
        for fp in files:
            est = estimate_single(fp, model)
            if est:
                total_cost += est["total_cost"]

        avg_cost = total_cost / len(files) if files else 0
        print(f"{model:<20} {len(files):>6} {all_chars:>10} ${avg_cost:>9.4f} ${total_cost:>9.4f}")


def cmd_keywords(args: argparse.Namespace) -> None:
    """Estimate cost for full pipeline: expand + rewrite + audit."""
    models = [args.model] if args.model else list(PRICING.keys())
    count = args.count or 100
    top = args.top or 10

    # Estimate prompt chars for expand, rewrite, audit
    expand_input_chars = EXPAND_PROMPT_OVERHEAD_CHARS + len(args.keywords) + 200
    expand_input_tokens = chars_to_tokens(expand_input_chars)
    expand_output_tokens = chars_to_tokens(count * 80)  # ~80 chars per question

    rewrite_input_chars_per = REWRITE_PROMPT_OVERHEAD_CHARS + 1500  # ~avg article 1500 chars
    rewrite_input_tokens_per = chars_to_tokens(rewrite_input_chars_per)
    rewrite_output_tokens_per = int(rewrite_input_tokens_per * 1.3)

    audit_input_chars_per = AUDIT_PROMPT_OVERHEAD_CHARS + 1500
    audit_input_tokens_per = chars_to_tokens(audit_input_chars_per)
    audit_output_tokens_per = int(audit_input_tokens_per * 0.8)

    print(f"\n全流程成本估算")
    print(f"  关键词: {args.keywords}")
    print(f"  Expand:  {count} 问题")
    print(f"  Rewrite: {top} 篇")
    print(f"  Audit:   {top} 篇")
    print()

    print(f"{'模型':<20} {'Expand费':>10} {'改写费':>10} {'审计费':>10} {'全流程费':>10}")
    print("-" * 70)

    for model in models:
        p = PRICING[model]

        # Expand
        cost_expand = (expand_input_tokens / 1_000_000 * p["input"]
                       + expand_output_tokens / 1_000_000 * p["output"])

        # Rewrite × top
        cost_rewrite = top * (
            rewrite_input_tokens_per / 1_000_000 * p["input"]
            + rewrite_output_tokens_per / 1_000_000 * p["output"]
        )

        # Audit × top
        cost_audit = top * (
            audit_input_tokens_per / 1_000_000 * p["input"]
            + audit_output_tokens_per / 1_000_000 * p["output"]
        )

        total = cost_expand + cost_rewrite + cost_audit

        print(f"{model:<20} ${cost_expand:>9.4f} ${cost_rewrite:>9.4f} ${cost_audit:>9.4f} ${total:>9.4f}")

    print("-" * 70)

    # Token breakdown
    total_input = (expand_input_tokens
                   + top * rewrite_input_tokens_per
                   + top * audit_input_tokens_per)
    total_output = (expand_output_tokens
                    + top * rewrite_output_tokens_per
                    + top * audit_output_tokens_per)

    print(f"\n  Token 估算:")
    print(f"    Expand:  {expand_input_tokens:,} in + {expand_output_tokens:,} out")
    print(f"    Rewrite: {top * rewrite_input_tokens_per:,} in + {top * rewrite_output_tokens_per:,} out (×{top})")
    print(f"    Audit:   {top * audit_input_tokens_per:,} in + {top * audit_output_tokens_per:,} out (×{top})")
    print(f"    总计:    {total_input:,} in + {total_output:,} out = {total_input + total_output:,} tokens")


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Generate a single-page HTML cost dashboard."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "cost-dashboard.html")

    # Calculate estimated costs per model for 1000 articles
    est_costs = {}
    for model_key in PRICING:
        p = PRICING[model_key]
        article_tokens = chars_to_tokens(AVG_ARTICLE_CHARS)
        input_tokens = chars_to_tokens(REWRITE_PROMPT_OVERHEAD_CHARS + AVG_ARTICLE_CHARS)
        output_tokens = int(input_tokens * 1.3)

        single_cost = (input_tokens / 1_000_000 * p["input"]
                       + output_tokens / 1_000_000 * p["output"])
        thousand_cost = single_cost * 1000

        est_costs[model_key] = {
            "input_per_1k": p["input"] / 1000 * 10000,  # per 10K tokens for display
            "output_per_1k": p["output"] / 1000 * 10000,
            "single_cost": single_cost,
            "thousand_cost": thousand_cost,
        }

    # Find max cost for bar scaling
    max_thousand = max(e["thousand_cost"] for e in est_costs.values())

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GEO Skills — 费用看板 v1.1.0</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    padding: 32px 24px;
    max-width: 900px;
    margin: 0 auto;
}}
h1 {{ font-size: 28px; color: #58a6ff; margin-bottom: 4px; }}
.subtitle {{ color: #8b949e; font-size: 14px; margin-bottom: 32px; }}

.card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 24px;
}}
.card h2 {{
    font-size: 18px;
    color: #e6edf3;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
}}

/* Pricing table */
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}
th {{
    text-align: left;
    color: #8b949e;
    font-weight: 600;
    padding: 10px 12px;
    border-bottom: 1px solid #21262d;
}}
td {{
    padding: 10px 12px;
    border-bottom: 1px solid #21262d;
}}
tr:last-child td {{ border-bottom: none; }}
td:nth-child(4), td:nth-child(5), td:nth-child(6) {{
    text-align: right;
    font-variant-numeric: tabular-nums;
}}
.highlight {{ color: #3fb950; font-weight: 600; }}

/* Bar chart */
.bar-chart {{ margin-top: 8px; }}
.bar-row {{
    display: flex;
    align-items: center;
    margin-bottom: 12px;
}}
.bar-label {{
    width: 140px;
    font-size: 13px;
    color: #c9d1d9;
    flex-shrink: 0;
}}
.bar-track {{
    flex: 1;
    height: 24px;
    background: #21262d;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}}
.bar-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}}
.bar-val {{
    width: 80px;
    font-size: 13px;
    color: #8b949e;
    text-align: right;
    flex-shrink: 0;
    margin-left: 8px;
}}

.footer {{
    text-align: center;
    color: #484f58;
    font-size: 12px;
    margin-top: 32px;
}}
</style>
</head>
<body>

<h1>GEO Skills 费用看板</h1>
<p class="subtitle">v1.1.0 · 数据生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} · 基准文章长度: {AVG_ARTICLE_CHARS} 字符</p>

<div class="card">
<h2>模型单价对比</h2>
<table>
<thead>
<tr>
<th>模型</th>
<th>输入 /10K tokens</th>
<th>输出 /10K tokens</th>
<th>单篇成本</th>
<th>千篇成本</th>
</tr>
</thead>
<tbody>
"""

    for model_key in PRICING:
        name = MODEL_NAMES.get(model_key, model_key)
        c = est_costs[model_key]
        html += f"""<tr>
<td>{name}</td>
<td>${c["input_per_1k"]:.4f}</td>
<td>${c["output_per_1k"]:.4f}</td>
<td>${c["single_cost"]:.4f}</td>
<td>${c["thousand_cost"]:.2f}</td>
</tr>
"""

    html += """
</tbody>
</table>
</div>

<div class="card">
<h2>千篇文章成本对比</h2>
<p class="subtitle" style="margin-bottom:16px">基于 {chars} 字符平均文章，含改写 + 审计流程</p>
<div class="bar-chart">
""".format(chars=AVG_ARTICLE_CHARS)

    bar_colors = ["#58a6ff", "#3fb950", "#d2a8ff", "#f78166"]
    for i, model_key in enumerate(PRICING):
        name = MODEL_NAMES.get(model_key, model_key)
        c = est_costs[model_key]
        pct = int(c["thousand_cost"] / max_thousand * 100)
        color = bar_colors[i % len(bar_colors)]
        html += f"""<div class="bar-row">
<div class="bar-label">{name}</div>
<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
<div class="bar-val">${c["thousand_cost"]:.2f}</div>
</div>
"""

    html += """</div>
</div>

<div class="footer">
Generated by GEO Skills geo_cost.py — <a href="https://github.com/fable-cc/geo-skills" style="color:#58a6ff">github.com/fable-cc/geo-skills</a>
</div>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] 费用看板已生成 → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GEO 用量/成本估算器 — 估算 token 消耗和 API 费用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模型定价 (per 1M tokens):
  gpt-4o-mini        $0.15 in / $0.60 out
  gpt-4o             $2.50 in / $10.00 out
  deepseek-v3        $0.27 in / $1.10 out
  claude-3.5-sonnet  $3.00 in / $15.00 out

Token 估算: 中文约 1.5 字符/token，输出按输入的 1.3 倍估算。

示例:
  %(prog)s --input 文章.md                       # 单篇（所有模型）
  %(prog)s --input 文章.md --model gpt-4o-mini   # 单篇（指定模型）
  %(prog)s --input-dir ./articles                # 批量目录
  %(prog)s --keywords "AI工具" --count 100 --top 10  # 全流程
        """,
    )

    parser.add_argument("--input", default="", help="单篇文章路径")
    parser.add_argument("--input-dir", default="", help="文章目录路径")
    parser.add_argument("--keywords", default="", help="种子关键词（用于全流程估算）")
    parser.add_argument("--count", type=int, default=100, help="expand 数量 (默认 100)")
    parser.add_argument("--top", type=int, default=10, help="选取前 N 改写 (默认 10)")
    parser.add_argument("--model", default="",
                        help="指定模型 (gpt-4o-mini/gpt-4o/deepseek-v3/claude-3.5-sonnet)，不指定则全列表")
    parser.add_argument("--dashboard", action="store_true",
                        help="生成 HTML 费用看板 (results/cost-dashboard.html)")

    args = parser.parse_args()

    if args.model and args.model not in PRICING:
        print(f"[ERROR] 未知模型: {args.model}", file=sys.stderr)
        print(f"  可用: {', '.join(PRICING.keys())}", file=sys.stderr)
        sys.exit(1)

    if args.input:
        cmd_input(args)
    elif args.input_dir:
        cmd_input_dir(args)
    elif args.keywords:
        cmd_keywords(args)
    elif args.dashboard:
        cmd_dashboard(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
