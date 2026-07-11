#!/usr/bin/env python3
"""
GEO 用量/成本估算器 — 估算单篇或批量改写的 token 消耗和费用

用法：
  python3 geo_cost.py --input 文章.md
  python3 geo_cost.py --input-dir ./articles
  python3 geo_cost.py --keywords "AI工具" --count 100 --top 10
  python3 geo_cost.py --input 文章.md --model gpt-4o-mini
"""

import argparse
import os
import sys

# ---- Pricing Table (per 1M tokens) ----
PRICING = {
    "gpt-4o-mini":      {"input": 0.15,  "output": 0.60},
    "gpt-4o":           {"input": 2.50,  "output": 10.00},
    "deepseek-v3":      {"input": 0.27,  "output": 1.10},
    "claude-3.5-sonnet": {"input": 3.00,  "output": 15.00},
}

# Token estimation: Chinese ~1.5 chars per token
CHARS_PER_TOKEN = 1.5

# Prompt overhead (system prompt + instructions in geo_rewrite.py / geo_keyword_expander.py)
REWRITE_PROMPT_OVERHEAD_CHARS = 6000   # ~4000 tokens
AUDIT_PROMPT_OVERHEAD_CHARS = 5000     # ~3333 tokens
EXPAND_PROMPT_OVERHEAD_CHARS = 3000    # ~2000 tokens


def chars_to_tokens(chars):
    return int(chars / CHARS_PER_TOKEN)


def estimate_single(article_path, model_name):
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


def cmd_input(args):
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


def cmd_input_dir(args):
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


def cmd_keywords(args):
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


def main():
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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
