#!/usr/bin/env python3
"""
GEO 多模型对比脚本 — 模拟送 4 个模型展示 prompt 差异和预估 token/费用

用法：
  python3 geo_compare.py --input tests/test_data/article_health.md --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# ---- 模型定义 ----
MODELS: dict[str, dict[str, object]] = {
    "gpt-4o-mini": {
        "input_price": 0.15,
        "output_price": 0.60,
        "max_output": 4096,
        "desc": "OpenAI GPT-4o Mini",
    },
    "deepseek-chat": {
        "input_price": 0.27,
        "output_price": 1.10,
        "max_output": 8192,
        "desc": "DeepSeek Chat (V3)",
    },
    "claude-3-haiku": {
        "input_price": 0.25,
        "output_price": 1.25,
        "max_output": 4096,
        "desc": "Anthropic Claude 3 Haiku",
    },
    "qwen-turbo": {
        "input_price": 0.30,
        "output_price": 0.60,
        "max_output": 6144,
        "desc": "Alibaba Qwen Turbo",
    },
}

# Token estimation: Chinese ~1.5 chars per token, English ~4 chars per token
CHARS_PER_TOKEN_CN = 1.5
CHARS_PER_TOKEN_EN = 4.0

# Prompt overhead (system prompt + instructions, approximately)
PROMPT_OVERHEAD_CHARS = {
    "gpt-4o-mini": 6500,
    "deepseek-chat": 6200,
    "claude-3-haiku": 7000,
    "qwen-turbo": 5800,
}

# Average rewrite output multiplier (relative to input)
OUTPUT_MULTIPLIER = 1.3


def chars_to_tokens(chars: int) -> int:
    """Estimate token count from character count (Chinese-heavy text)."""
    return int(chars / CHARS_PER_TOKEN_CN)


def estimate_cost(model_key: str, article_chars: int, article_path: str) -> dict[str, str | int | float]:
    """Estimate token count and cost for one model rewriting one article."""
    m = MODELS[model_key]
    overhead = PROMPT_OVERHEAD_CHARS.get(model_key, 6000)

    input_chars = overhead + article_chars
    input_tokens = chars_to_tokens(input_chars)
    output_tokens = int(input_tokens * OUTPUT_MULTIPLIER)

    input_cost = input_tokens / 1_000_000 * m["input_price"]  # type: ignore[operator]
    output_cost = output_tokens / 1_000_000 * m["output_price"]  # type: ignore[operator]
    total_cost = input_cost + output_cost

    # Simulated score (deterministic based on article content)
    seed = sum(ord(c) for c in os.path.basename(article_path)) % 100
    sim_score = {
        "gpt-4o-mini": min(60, 38 + seed % 15),
        "deepseek-chat": min(60, 40 + seed % 12),
        "claude-3-haiku": min(60, 42 + seed % 10),
        "qwen-turbo": min(60, 36 + seed % 14),
    }

    return {
        "model": model_key,
        "desc": m["desc"],  # type: ignore
        "prompt_chars": input_chars,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "sim_score": sim_score.get(model_key, 40),
    }


def print_dry_run(results: list[dict[str, str | int | float]], article_path: str) -> None:
    """Print comparison table for dry-run mode."""
    file_name = os.path.basename(article_path)

    print(f"\nGEO 多模型对比 — {file_name}")
    print("=" * 90)

    # Prompt length comparison
    print(f"\n{'模型':<18} {'Prompt长度':>12} {'输入Token':>10} {'输出Token':>10} {'预估费用':>10} {'模拟评分':>10}")
    print("-" * 90)

    for r in results:
        print(
            f"{r['desc']:<18} {r['prompt_chars']:>10}字 {r['input_tokens']:>10} "
            f"{r['output_tokens']:>10} ${r['total_cost']:>9.4f} {r['sim_score']:>8}/60"
        )

    print("-" * 90)

    # Pricing detail table
    print(f"\n{'模型':<18} {'输入$/1K':>10} {'输出$/1K':>10} {'千篇成本':>10} {'MaxOutput':>10}")
    print("-" * 70)

    for r in results:
        m = MODELS[r["model"]]  # type: ignore[index]
        cost_per_1k = r["total_cost"] * 1000
        print(
            f"{r['desc']:<18} ${m['input_price']:>9.4f} ${m['output_price']:>9.4f} "
            f"${cost_per_1k:>9.2f} {m['max_output']:>10}"
        )

    print("-" * 70)

    # Per-model prompt preview
    print(f"\n{'=' * 90}")
    print("各模型 Prompt 差异预览 (前 200 字符)")
    print(f"{'=' * 90}")

    prompt_previews = generate_prompt_previews(article_path)

    for model_key, preview in prompt_previews.items():
        m = MODELS[model_key]
        print(f"\n--- {m['desc']} ---")
        print(f"System: {preview['system'][:200]}...")
        print(f"User前段: {preview['user'][:200]}...")

    print()


def generate_prompt_previews(article_path: str) -> dict[str, dict[str, str]]:
    """Generate prompt previews for each model (dry-run simulation)."""
    prompts = {}

    for model_key in MODELS:
        provider = model_key.split("-")[0]  # gpt, deepseek, claude, qwen

        system_prompts = {
            "gpt": "You are a GEO optimization expert. Rewrite the following Chinese article to maximize AI search engine visibility. Follow the 6-dimension scoring framework: Q&A visibility, entity density, citation anchors, structured markup, platform adaptation, and readability. Output only the rewritten article.",
            "deepseek": "你是一位 GEO（生成式引擎优化）专家。请将以下中文文章改写为面向 AI 搜索引擎优化的版本，遵循六维评分体系：问答可见性、实体密度、引用锚点、结构化标记、平台适配、可读性。只输出改写后的文章，不要添加额外说明。",
            "claude": "You are a GEO (Generative Engine Optimization) specialist. Rewrite the article below for optimal AI search visibility. Apply the six-dimension framework: Q&A, entity, citation, structure, platform, readability. Return only the rewritten article.",
            "qwen": "你是一个 GEO（生成引擎优化）改写专家。请把下面的文章改写成面向 AI 搜索引擎优化的版本。遵循六维评分：问答结构化、实体植入、引用锚点、结构化标记、平台规则、可读性。只输出改写后内容。",
        }

        user_prefix = {
            "gpt": f"Platform: Zhihu\nIndustry: Technology\n\nArticle:\n",
            "deepseek": f"平台：知乎\n行业：科技\n\n文章内容：\n",
            "claude": f"Platform: Zhihu\nIndustry: Technology\n\nArticle:\n",
            "qwen": f"平台：知乎 | 行业：科技\n\n文章内容：\n",
        }

        article_text = ""
        if os.path.isfile(article_path):
            with open(article_path, "r", encoding="utf-8") as f:
                article_text = f.read()

        prompts[model_key] = {
            "system": system_prompts.get(provider, system_prompts["deepseek"]),
            "user": user_prefix.get(provider, user_prefix["deepseek"]) + article_text,
        }

    return prompts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GEO 多模型对比 — 模拟 4 模型改写效果预览",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --input tests/test_data/article_health.md --dry-run
        """,
    )

    parser.add_argument("--input", required=True, help="输入文章路径")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行（默认开启）")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"[ERROR] 文件未找到: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()
    article_chars = len(content)

    results = []
    for model_key in MODELS:
        results.append(estimate_cost(model_key, article_chars, args.input))

    print_dry_run(results, args.input)


if __name__ == "__main__":
    try:
        main()
    except json.JSONDecodeError as e:
        print(f"[错误] API 返回格式异常：{e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[错误] 未预期异常：{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
