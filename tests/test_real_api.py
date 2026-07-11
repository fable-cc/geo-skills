#!/usr/bin/env python3
"""
API 联调测试 — 验证 GEO 脚本的 prompt 构建和管道集成

用法：
  python3 tests/test_real_api.py                     # dry-run 模式（不调 API）
  REAL_API=true python3 tests/test_real_api.py       # 真实 API 调用（需要 OPENAI_API_KEY）
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "test_data")
TEST_ARTICLES = [
    ("article_health.md", "zhihu"),
    ("article_tech.md", "wechat"),
    ("article_business.md", "baijiahao"),
]


def resolve_script(name):
    path = os.path.join(PROJECT_DIR, name)
    if not os.path.isfile(path):
        print(f"[ERROR] 脚本未找到: {path}", file=sys.stderr)
        return None
    return path


def run(cmd, description=""):
    print(f"\n{'='*60}")
    print(f"[TEST] {description}")
    print(f"  CMD: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy(), timeout=30)
        print(f"  RETURNCODE: {result.returncode}")
        print(f"  STDOUT ({len(result.stdout)} bytes):")
        print(f"  {result.stdout[:600]}")
        if result.stderr:
            print(f"  STDERR ({len(result.stderr)} bytes):")
            print(f"  {result.stderr[:400]}")
        return result
    except subprocess.TimeoutExpired:
        print("  [TIMEOUT]")
        return None
    except FileNotFoundError:
        print(f"  [ERROR] Command not found: {cmd[0]}")
        return None


def test_rewrite_dry_run():
    """测试 rewrite 的 prompt 构建（dry-run，不调 API）"""
    results = []
    rewrite_script = resolve_script("geo_rewrite.py")
    if not rewrite_script:
        return []

    for filename, platform in TEST_ARTICLES:
        article_path = os.path.join(TEST_DATA_DIR, filename)
        if not os.path.isfile(article_path):
            print(f"  [SKIP] 测试文章不存在: {article_path}")
            continue

        cmd = [
            sys.executable, rewrite_script,
            "--input", article_path,
            "--platform", platform,
            "--brand", "geo-skills",
            "--dry-run",
        ]
        result = run(cmd, f"rewrite dry-run: {filename} → {platform}")

        # Parse prompt length and coverage from output
        prompt_length = 0
        has_structure = False
        has_entity = False
        has_citation = False
        has_markup = False
        has_platform = False

        if result and result.stdout:
            stdout = result.stdout
            prompt_length = len(stdout)
            has_structure = "结构化" in stdout or "问答" in stdout
            has_entity = "品牌" in stdout or "实体" in stdout or "植入" in stdout
            has_citation = "引用" in stdout or "锚点" in stdout or "权威" in stdout
            has_markup = "标记" in stdout or "格式" in stdout or "列表" in stdout
            has_platform = platform in stdout.lower() or platform in stdout

        results.append({
            "article": filename,
            "platform": platform,
            "returncode": result.returncode if result else -1,
            "prompt_length": prompt_length,
            "rule_coverage": {
                "结构化和问答": has_structure,
                "实体植入": has_entity,
                "引用锚点": has_citation,
                "结构化标记": has_markup,
                "平台适配": has_platform,
            },
        })
    return results


def test_audit_dry_run():
    """测试 audit 的评分卡结构（dry-run）"""
    results = []
    audit_script = resolve_script("geo_content_audit.py")
    if not audit_script:
        return []

    for filename, _ in TEST_ARTICLES:
        article_path = os.path.join(TEST_DATA_DIR, filename)
        if not os.path.isfile(article_path):
            continue

        cmd = [
            sys.executable, audit_script,
            "--input", article_path,
            "--dry-run",
        ]
        result = run(cmd, f"audit dry-run: {filename}")

        has_score_card = False
        if result and result.stdout:
            has_score_card = (
                "评分卡" in result.stdout
                or "六维" in result.stdout
                or "总分" in result.stdout
                or "优先级" in result.stdout
            )

        results.append({
            "article": filename,
            "returncode": result.returncode if result else -1,
            "has_score_card": has_score_card,
        })
    return results


def test_expand_dry_run():
    """测试 expand 关键词扩展"""
    expand_script = resolve_script("geo_keyword_expander.py")
    if not expand_script:
        return []

    cmd = [
        sys.executable, expand_script,
        "--keywords", "AI工具,数字化转型",
        "--count", "10",
        "--dry-run",
    ]
    result = run(cmd, "expand dry-run: AI工具,数字化转型 x10")
    return {
        "returncode": result.returncode if result else -1,
        "prompt_length": len(result.stdout) if result else 0,
    }


def test_real_api_calls():
    """真实 API 调用测试（仅当 REAL_API=true）"""
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n[SKIP] 未设置 OPENAI_API_KEY，跳过真实 API 调用")
        return

    print("\n" + "=" * 60)
    print(f"[REAL API] OPENAI_API_KEY={os.environ['OPENAI_API_KEY'][:8]}...")
    print("⚠️  真实 API 调用将消耗 token，请确认后继续。")

    rewrite_script = resolve_script("geo_rewrite.py")
    if not rewrite_script:
        return

    article_path = os.path.join(TEST_DATA_DIR, "article_health.md")
    output_path = os.path.join(SCRIPT_DIR, "test_output_health_geo.md")
    cmd = [
        sys.executable, rewrite_script,
        "--input", article_path,
        "--output", output_path,
        "--platform", "zhihu",
        "--brand", "geo-skills",
    ]
    result = run(cmd, "真实调用: rewrite article_health.md")
    if result and result.returncode == 0:
        print(f"  [OK] 输出 → {output_path}")
    else:
        print(f"  [FAIL] {result.stderr if result else 'N/A'}")


def print_summary(rewrite_results, audit_results, expand_result):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    print("\n【GEO 改写 — Prompt 构建验证】")
    print(f"{'文章':<25} {'平台':<12} {'Prompt长度':>10} {'返回码':>8}  五维覆盖")
    print("-" * 85)
    for r in rewrite_results:
        cov = r["rule_coverage"]
        rules_passed = sum(1 for v in cov.values() if v)
        print(f"{r['article']:<25} {r['platform']:<12} {r['prompt_length']:>10} {r['returncode']:>8}   "
              f"{rules_passed}/5 (结构化:{'Y' if cov['结构化和问答'] else 'N'} "
              f"实体:{'Y' if cov['实体植入'] else 'N'} "
              f"引用:{'Y' if cov['引用锚点'] else 'N'} "
              f"标记:{'Y' if cov['结构化标记'] else 'N'} "
              f"平台:{'Y' if cov['平台适配'] else 'N'})")

    print("\n【GEO 审计 — 评分卡验证】")
    for r in audit_results:
        print(f"  {r['article']:<25} 返回码:{r['returncode']:>4}  评分卡结构:{'Y' if r['has_score_card'] else 'N'}")

    if expand_result:
        print(f"\n【关键词扩展】")
        print(f"  返回码: {expand_result['returncode']}  Prompt长度: {expand_result['prompt_length']}")

    total_passed = sum(1 for r in rewrite_results if r["returncode"] == 0) \
        + sum(1 for a in audit_results if a["returncode"] == 0)
    total = len(rewrite_results) + len(audit_results)
    print(f"\n  ✅ 通过: {total_passed}/{total}")


def main():
    print("geo-skills API 联调测试")
    print(f"  项目目录: {PROJECT_DIR}")
    print(f"  测试数据: {TEST_DATA_DIR}")

    real_api = os.environ.get("REAL_API", "").lower() in ("true", "1", "yes")
    print(f"  模式: {'真实API调用' if real_api else 'dry-run (prompt验证)'}")

    # 1. Dry-run tests
    print("\n" + "#" * 60)
    print("# 阶段 1: Dry-Run Prompt 构建验证")
    print("#" * 60)

    rewrite_results = test_rewrite_dry_run()
    audit_results = test_audit_dry_run()
    expand_result = test_expand_dry_run()

    print_summary(rewrite_results, audit_results, expand_result)

    # 2. Real API tests (optional)
    if real_api:
        print("\n" + "#" * 60)
        print("# 阶段 2: 真实 API 调用")
        print("#" * 60)
        test_real_api_calls()
    else:
        print("\n💡 设置 REAL_API=true 可执行真实 API 调用（需 OPENAI_API_KEY）")


if __name__ == "__main__":
    main()
