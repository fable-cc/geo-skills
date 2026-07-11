#!/usr/bin/env python3
"""
GEO 对比基准测试 — 多模型 / 多文章 / 预计 GEO 评分对比矩阵

用法：
  python3 tests/benchmark.py                             # 对比矩阵 (dry-run)
  python3 tests/benchmark.py --models gpt-4o,deepseek-v3 # 指定模型
  python3 tests/benchmark.py --models gpt-4o --dry-run   # 只打印矩阵
"""

import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "test_data")

TEST_ARTICLES = [
    ("article_health.md", "zhihu", "健康科普"),
    ("article_tech.md", "wechat", "科技工具"),
    ("article_business.md", "baijiahao", "商业分析"),
]

DEFAULT_MODELS = ["gpt-4o", "deepseek-v3", "claude-3.5-sonnet"]


def resolve_script(name):
    path = os.path.join(PROJECT_DIR, name)
    if not os.path.isfile(path):
        return None
    return path


def estimate_geo_score(article_path, model):
    """
    基于五维规则评估预计 GEO 评分（0-60，每维 0-10）
    这里从 article 内容做文本特征提取，结合模型能力给出估计得分。

    由于 dry-run 模式下不调 API，此函数基于文本特征做启发式评分：
    - 问答可见性：是否有 QA 结构 (0-10)
    - 实体密度：品牌/术语出现次数 (0-10)
    - 引用锚点：引用/数据/来源标记 (0-10)
    - 结构化标记：H2/H3/列表/加粗 (0-10)
    - 平台适配：是否匹配目标平台特征 (0-10)
    - 可读性：段落长度/句式复杂度 (0-10)
    """
    if not os.path.isfile(article_path):
        return {"error": "article not found"}

    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # 问答可见性：检测 ? 和问答句式
    qa_count = content.count("？") + content.count("?")
    qa_score = min(10, qa_count * 3)

    # 实体密度：检测专有名词、品牌、术语
    import re
    entities = re.findall(r'[A-Z][a-z]+|[A-Z]{2,}', content)
    entity_count = len(entities)
    entity_score = min(10, entity_count)

    # 引用锚点：检测引用标记、数字、百分比
    citations = len(re.findall(r'[\d]+%|根据|来源|引用|报告|研究|显示|数据', content))
    citation_score = min(10, citations * 2)

    # 结构化标记：H2、H3、加粗、列表
    h2_count = sum(1 for l in lines if l.startswith("## "))
    h3_count = sum(1 for l in lines if l.startswith("### "))
    bold_count = content.count("**")
    list_count = sum(1 for l in lines if l.strip().startswith("- ") or l.strip().startswith("* "))
    struct_score = min(10, (h2_count * 2 + h3_count + bold_count // 2 + list_count) // 2)

    # 平台适配：基于 heuristic（此处简化处理）
    platform_score = 7  # baseline

    # 可读性：段落长度
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    avg_para_len = sum(len(p) for p in paragraphs) / max(1, len(paragraphs))
    readability_score = 10 if avg_para_len < 300 else (7 if avg_para_len < 600 else 4)

    # 模型能力乘数（不同模型在结构化改写上能力不同）
    model_multiplier = {
        "gpt-4o": 1.0,
        "deepseek-v3": 0.92,
        "claude-3.5-sonnet": 0.95,
    }.get(model, 0.85)

    base_scores = {
        "问答可见性": qa_score,
        "实体密度": entity_score,
        "引用锚点": citation_score,
        "结构化标记": struct_score,
        "平台适配": platform_score,
        "可读性": readability_score,
    }

    # 应用模型乘数到改写后的预计得分（改写前保持原样）
    predicted_scores = {k: round(v * model_multiplier, 1) for k, v in base_scores.items()}
    predicted_total = sum(predicted_scores.values())

    return {
        "base_scores": base_scores,
        "predicted_scores": predicted_scores,
        "predicted_total": round(predicted_total, 1),
    }


def print_matrix(models, dry_run):
    """打印对比矩阵"""
    print("\n" + "=" * 100)
    print("GEO 对比基准测试 — 模型 × 文章 × 预计 GEO 评分矩阵")
    print("=" * 100)

    # Header
    print(f"\n{'模型':<20} {'文章':<22} {'平台':<12} {'问答':>5} {'实体':>5} {'引用':>5} {'标记':>5} {'适配':>5} {'可读':>5} {'总分':>6}")
    print("-" * 100)

    all_results = []
    for model in models:
        for article, platform, category in TEST_ARTICLES:
            article_path = os.path.join(TEST_DATA_DIR, article)
            scores = estimate_geo_score(article_path, model)
            if "error" in scores:
                continue

            ps = scores["predicted_scores"]
            pt = scores["predicted_total"]
            print(f"{model:<20} {article:<22} {platform:<12} "
                  f"{ps['问答可见性']:>5.1f} {ps['实体密度']:>5.1f} "
                  f"{ps['引用锚点']:>5.1f} {ps['结构化标记']:>5.1f} "
                  f"{ps['平台适配']:>5.1f} {ps['可读性']:>5.1f} {pt:>6.1f}")

            all_results.append({
                "model": model,
                "article": article,
                "platform": platform,
                "scores": ps,
                "total": pt,
            })

    # Summary by model
    print("\n" + "=" * 100)
    print("模型平均得分汇总")
    print("-" * 100)
    print(f"{'模型':<20} {'平均总分':>8} {'最佳文章':>22} {'最佳得分':>8}")
    print("-" * 60)

    model_summary = {}
    for r in all_results:
        m = r["model"]
        if m not in model_summary:
            model_summary[m] = {"total": 0.0, "count": 0, "best": ("", 0.0)}
        model_summary[m]["total"] += r["total"]
        model_summary[m]["count"] += 1
        if r["total"] > model_summary[m]["best"][1]:
            model_summary[m]["best"] = (r["article"], r["total"])

    for model, stats in sorted(model_summary.items()):
        avg = stats["total"] / stats["count"]
        print(f"{model:<20} {avg:>8.1f} {stats['best'][0]:>22} {stats['best'][1]:>8.1f}")

    print(f"\n{'':->60}")
    print("评分规则说明:")
    print("  每维度 0-10 分，总分 60 分。预测得分为原始文本特征 × 模型改写能力系数。")
    print("  模型系数: gpt-4o=1.0 / deepseek-v3=0.92 / claude-3.5-sonnet=0.95")
    print("  六维评分卡: 问答可见性 / 实体密度 / 引用锚点 / 结构化标记 / 平台适配 / 可读性")
    print(f"\n  模式: {'DRY-RUN (不调用 API)' if dry_run else '真实调用'}")


def real_benchmark(models):
    """执行真实 API 调用对比（需要 OPENAI_API_KEY）"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n[SKIP] 未设置 OPENAI_API_KEY，跳过真实 API 对比")
        return

    rewrite_script = resolve_script("geo_rewrite.py")
    if not rewrite_script:
        print("[ERROR] geo_rewrite.py 未找到")
        return

    print("\n⚠️  真实 API 对比将消耗大量 token，请确认。")
    print(f"  模型: {models}")
    print(f"  文章: {[a[0] for a in TEST_ARTICLES]}")
    print(f"  总计: {len(models) * len(TEST_ARTICLES)} 次 API 调用")

    if os.environ.get("AUTO_CONFIRM", "").lower() not in ("true", "1", "yes"):
        resp = input("\n  确认执行? (y/N): ")
        if resp.lower() != "y":
            print("  已取消")
            return

    for model in models:
        for article, platform, _ in TEST_ARTICLES:
            article_path = os.path.join(TEST_DATA_DIR, article)
            output_path = os.path.join(
                SCRIPT_DIR, f"bench_output_{model.replace('.', '_')}_{article}"
            )
            cmd = [
                sys.executable, rewrite_script,
                "--input", article_path,
                "--output", output_path,
                "--platform", platform,
            ]
            env = os.environ.copy()
            env["LLM_MODEL"] = model

            print(f"\n  [{model}] {article} → {platform}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
                print(f"    returncode={result.returncode}")
                if result.returncode != 0:
                    print(f"    error: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                print(f"    [TIMEOUT]")
            except Exception as e:
                print(f"    [ERROR] {e}")


def main():
    parser = argparse.ArgumentParser(
        description="GEO 对比基准测试 — 模型 × 文章 × GEO评分矩阵"
    )
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help=f"模型列表，逗号分隔 (默认: {','.join(DEFAULT_MODELS)})")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="只打印对比矩阵，不调用 API (默认)")
    parser.add_argument("--real", action="store_true",
                        help="执行真实 API 对比（会消耗 token）")

    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    print_matrix(models, dry_run=not args.real)

    if args.real:
        print("\n" + "#" * 60)
        print("# 真实 API 对比")
        print("#" * 60)
        real_benchmark(models)


if __name__ == "__main__":
    main()
