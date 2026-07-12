#!/usr/bin/env python3
"""
GEOFlow — 轻量级 GEO 管道编排器

三条管线：
  管线1 (full)：   关键词 → expand → 选前 N 问题 → rewrite → audit → 汇总报告
  管线2 (single)： 单篇文章 → rewrite + audit 双报告 → JSON 输出
  管线3 (matrix)： 关键词 → expand N 个问题 → 批量 rewrite

用法：
  python3 geo_flow.py --mode full --keywords "AI工具,效率" --top 5
  python3 geo_flow.py --mode single --input article.md --brand "景一"
  python3 geo_flow.py --mode matrix --keywords "编程,Python" --count 100 --top 20
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_script(name: str) -> str:
    """Resolve a sibling script path."""
    path = os.path.join(SCRIPT_DIR, name)
    if not os.path.isfile(path):
        print(f"[ERROR] 脚本未找到: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def run_subprocess(cmd: list[str], env: dict[str, str] | None = None, timeout: int | None = None) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=merged_env,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def parse_expand_csv(csv_path: str) -> list[dict[str, str]]:
    """Parse expanded keywords CSV and return list of rows."""
    rows: list[dict[str, str]] = []
    if not os.path.isfile(csv_path):
        return rows
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def pipeline_full(args: argparse.Namespace) -> None:
    """管线1：关键词 → expand → 选前 N → rewrite → audit → 汇总报告"""
    output_dir = args.output_dir or os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    report = {
        "pipeline": "full",
        "timestamp": datetime.now().isoformat(),
        "keywords": args.keywords,
        "top": args.top,
        "platform": args.platform,
        "brand": args.brand,
        "stages": {},
    }

    # Stage 1: Expand
    print(f"[Stage 1/4] 关键词扩展: {args.keywords}")
    expand_csv = os.path.join(output_dir, "expanded_keywords.csv")
    expand_cmd = [
        sys.executable,
        resolve_script("geo_keyword_expander.py"),
        "--keywords", args.keywords,
        "--count", str(args.count),
        "--output", expand_csv,
    ]
    if args.dry_run:
        print(f"  [DRY-RUN] {' '.join(expand_cmd)}")
        report["stages"]["expand"] = {"dry_run": True, "command": " ".join(expand_cmd)}
    else:
        rc, stdout, stderr = run_subprocess(expand_cmd)
        if rc != 0:
            report["stages"]["expand"] = {"success": False, "error": stderr}
            print(f"  [FAIL] {stderr}")
        else:
            report["stages"]["expand"] = {"success": True, "output": expand_csv}
            print(f"  [OK] 输出 → {expand_csv}")

    # Stage 2: Select top N
    print(f"[Stage 2/4] 选取前 {args.top} 个问题进行改写")
    rows = parse_expand_csv(expand_csv)
    if not rows and not args.dry_run:
        print("  [WARN] expanded CSV 为空，管线终止")
        report["stages"]["select"] = {"success": False, "error": "empty CSV"}
        save_json(report, os.path.join(output_dir, "flow_report.json"))
        return

    top_rows = rows[:args.top] if not args.dry_run else []
    selected_questions = [r.get("问题", "") for r in top_rows]
    report["stages"]["select"] = {
        "success": True,
        "total_available": len(rows),
        "selected": len(selected_questions),
        "questions": selected_questions,
    }

    # Stage 3: Rewrite each question
    print(f"[Stage 3/4] 对 {len(selected_questions) if not args.dry_run else args.top} 个问题进行 GEO 改写")
    rewrites_output_dir = os.path.join(output_dir, "rewrites")
    os.makedirs(rewrites_output_dir, exist_ok=True)
    rewrite_results = []

    if args.dry_run:
        for i in range(min(args.top, 1)):
            rw_cmd = [
                sys.executable,
                resolve_script("geo_rewrite.py"),
                "--input", f"<article_{i+1}.md>",
                "--output", os.path.join(rewrites_output_dir, f"rewrite_{i+1}.md"),
            ]
            if args.platform:
                rw_cmd += ["--platform", args.platform]
            if args.brand:
                rw_cmd += ["--brand", args.brand]
            rw_cmd.append("--dry-run")
            print(f"  [DRY-RUN] {' '.join(rw_cmd)}")
        rewrite_results = [{"dry_run": True}] * args.top
    else:
        for i, question in enumerate(selected_questions):
            safe_name = f"rewrite_{i+1:03d}"
            article_path = os.path.join(rewrites_output_dir, f"{safe_name}_input.md")
            output_path = os.path.join(rewrites_output_dir, f"{safe_name}.md")

            with open(article_path, "w", encoding="utf-8") as f:
                f.write(f"# {question}\n\n")
                f.write(f"{question}\n")

            rw_cmd = [
                sys.executable,
                resolve_script("geo_rewrite.py"),
                "--input", article_path,
                "--output", output_path,
            ]
            if args.platform:
                rw_cmd += ["--platform", args.platform]
            if args.brand:
                rw_cmd += ["--brand", args.brand]

            rc, stdout, stderr = run_subprocess(rw_cmd, timeout=120)
            rewrite_results.append({
                "question": question,  # type: ignore
                "output": output_path,  # type: ignore
                "success": rc == 0,
                "error": stderr if rc != 0 else None,  # type: ignore
            })
            status = "OK" if rc == 0 else "FAIL"
            print(f"  [{status}] {question[:50]}...")

    report["stages"]["rewrite"] = {
        "success": True,
        "total": len(rewrite_results),
        "results": rewrite_results,
    }

    # Stage 4: Audit each rewrite
    print(f"[Stage 4/4] 对改写结果进行 GEO 审计")
    audits_output_dir = os.path.join(output_dir, "audits")
    os.makedirs(audits_output_dir, exist_ok=True)
    audit_results = []

    if args.dry_run:
        for i in range(min(args.top, 1)):
            ac_cmd = [
                sys.executable,
                resolve_script("geo_content_audit.py"),
                "--input", f"<rewrite_{i+1}.md>",
                "--output", os.path.join(audits_output_dir, f"audit_{i+1}.md"),
                "--dry-run",
            ]
            print(f"  [DRY-RUN] {' '.join(ac_cmd)}")
        audit_results = [{"dry_run": True}] * args.top
    else:
        for i, rw in enumerate(rewrite_results):
            if not rw.get("success") and not rw.get("dry_run"):
                audit_results.append({"success": False, "error": "rewrite failed"})  # type: ignore
                continue
            output_path = os.path.join(audits_output_dir, f"audit_{i+1:03d}.md")
            ac_cmd = [
                sys.executable,
                resolve_script("geo_content_audit.py"),
                "--input", rw["output"],  # type: ignore
                "--output", output_path,
            ]
            rc, stdout, stderr = run_subprocess(ac_cmd, timeout=120)
            audit_results.append({
                "question": rw.get("question", ""),  # type: ignore
                "output": output_path,  # type: ignore
                "success": rc == 0,
                "error": stderr if rc != 0 else None,  # type: ignore
            })
            status = "OK" if rc == 0 else "FAIL"
            print(f"  [{status}] audit {i+1}/{len(rewrite_results)}")

    report["stages"]["audit"] = {
        "success": True,
        "total": len(audit_results),
        "results": audit_results,
    }

    # Summary
    summary = {
        "total_keywords_expanded": len(rows) if not args.dry_run else args.count,
        "questions_selected": args.top,
        "rewrites_succeeded": sum(1 for r in rewrite_results if r.get("success")),
        "rewrites_failed": sum(1 for r in rewrite_results if not r.get("success") and not r.get("dry_run")),
        "audits_succeeded": sum(1 for a in audit_results if a.get("success")),
        "audits_failed": sum(1 for a in audit_results if not a.get("success") and not a.get("dry_run")),
    }
    report["summary"] = summary

    report_path = os.path.join(output_dir, "flow_report.json")
    save_json(report, report_path)
    print(f"\n[DONE] 管线 full 完成")
    print(f"  报告 → {report_path}")
    print(f"  扩展 → {expand_csv}")
    print(f"  改写 → {rewrites_output_dir}/")
    print(f"  审计 → {audits_output_dir}/")
    if not args.dry_run:
        print(f"  摘要: {json.dumps(summary, ensure_ascii=False)}")


def pipeline_single(args: argparse.Namespace) -> None:
    """管线2：单篇文章 → rewrite + audit 双报告 → JSON"""
    if not args.input:
        print("[ERROR] single 模式需要 --input 参数", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    report = {
        "pipeline": "single",
        "timestamp": datetime.now().isoformat(),
        "input": args.input,
        "platform": args.platform,
        "brand": args.brand,
        "stages": {},
    }

    base_name = os.path.splitext(os.path.basename(args.input))[0]

    # Stage 1: Rewrite
    print(f"[Stage 1/2] GEO 改写: {args.input}")
    rewrite_output = os.path.join(output_dir, f"{base_name}-geo.md")
    rw_cmd = [
        sys.executable,
        resolve_script("geo_rewrite.py"),
        "--input", args.input,
        "--output", rewrite_output,
    ]
    if args.platform:
        rw_cmd += ["--platform", args.platform]
    if args.brand:
        rw_cmd += ["--brand", args.brand]
    if args.dry_run:
        rw_cmd.append("--dry-run")
        print(f"  [DRY-RUN] {' '.join(rw_cmd)}")

    if not args.dry_run:
        rc, stdout, stderr = run_subprocess(rw_cmd, timeout=120)
        report["stages"]["rewrite"] = {
            "success": rc == 0,
            "output": rewrite_output,
            "error": stderr if rc != 0 else None,
        }
        print(f"  [{'OK' if rc == 0 else 'FAIL'}] → {rewrite_output}")
    else:
        report["stages"]["rewrite"] = {"dry_run": True}

    # Stage 2: Audit
    print(f"[Stage 2/2] GEO 审计: {rewrite_output}")
    audit_output = os.path.join(output_dir, f"{base_name}-audit.md")
    audit_input = rewrite_output if not args.dry_run else args.input
    ac_cmd = [
        sys.executable,
        resolve_script("geo_content_audit.py"),
        "--input", audit_input,
        "--output", audit_output,
    ]
    if args.dry_run:
        ac_cmd.append("--dry-run")
        print(f"  [DRY-RUN] {' '.join(ac_cmd)}")

    if not args.dry_run:
        rc, stdout, stderr = run_subprocess(ac_cmd, timeout=120)
        report["stages"]["audit"] = {
            "success": rc == 0,
            "output": audit_output,
            "error": stderr if rc != 0 else None,
        }
        print(f"  [{'OK' if rc == 0 else 'FAIL'}] → {audit_output}")
    else:
        report["stages"]["audit"] = {"dry_run": True}

    report_path = os.path.join(output_dir, f"{base_name}-flow-report.json")
    save_json(report, report_path)
    print(f"\n[DONE] 管线 single 完成 → {report_path}")


def pipeline_matrix(args: argparse.Namespace) -> None:
    """管线3：关键词 → expand N → 批量 rewrite"""
    output_dir = args.output_dir or os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    report = {
        "pipeline": "matrix",
        "timestamp": datetime.now().isoformat(),
        "keywords": args.keywords,
        "count": args.count,
        "top": args.top,
        "platform": args.platform,
        "brand": args.brand,
        "stages": {},
    }

    # Stage 1: Expand
    print(f"[Stage 1/2] 关键词扩展: {args.keywords}")
    expand_csv = os.path.join(output_dir, "expanded_keywords.csv")
    expand_cmd = [
        sys.executable,
        resolve_script("geo_keyword_expander.py"),
        "--keywords", args.keywords,
        "--count", str(args.count),
        "--output", expand_csv,
    ]
    if args.dry_run:
        print(f"  [DRY-RUN] {' '.join(expand_cmd)}")
        report["stages"]["expand"] = {"dry_run": True}
    else:
        rc, stdout, stderr = run_subprocess(expand_cmd)
        report["stages"]["expand"] = {
            "success": rc == 0,
            "output": expand_csv,
            "error": stderr if rc != 0 else None,
        }
        print(f"  [{'OK' if rc == 0 else 'FAIL'}] → {expand_csv}")

    # Stage 2: Batch rewrite
    rows = parse_expand_csv(expand_csv)
    top_rows = rows[:args.top] if not args.dry_run else []
    print(f"[Stage 2/2] 批量改写前 {len(top_rows) if not args.dry_run else args.top} 个问题")
    rewrites_dir = os.path.join(output_dir, "matrix_rewrites")
    os.makedirs(rewrites_dir, exist_ok=True)
    rewrite_results = []

    if args.dry_run:
        rw_cmd = [
            sys.executable, resolve_script("geo_rewrite.py"),
            "--input", "<article.md>", "--output", f"{rewrites_dir}/rewrite_001.md",
        ]
        if args.platform:
            rw_cmd += ["--platform", args.platform]
        if args.brand:
            rw_cmd += ["--brand", args.brand]
        rw_cmd.append("--dry-run")
        print(f"  [DRY-RUN] {' '.join(rw_cmd)} x{args.top}")
        rewrite_results = [{"dry_run": True}] * args.top
    else:
        for i, row in enumerate(top_rows):
            question = row.get("问题", f"question_{i}")
            safe_name = f"rewrite_{i+1:03d}"
            article_path = os.path.join(rewrites_dir, f"{safe_name}_input.md")
            output_path = os.path.join(rewrites_dir, f"{safe_name}.md")

            with open(article_path, "w", encoding="utf-8") as f:
                f.write(f"# {question}\n\n{question}\n\n请基于以上主题撰写一篇 500 字科普文章。\n")

            rw_cmd = [
                sys.executable, resolve_script("geo_rewrite.py"),
                "--input", article_path,
                "--output", output_path,
            ]
            if args.platform:
                rw_cmd += ["--platform", args.platform]
            if args.brand:
                rw_cmd += ["--brand", args.brand]

            rc, stdout, stderr = run_subprocess(rw_cmd, timeout=120)
            rewrite_results.append({
                "question": question,  # type: ignore
                "output": output_path,  # type: ignore
                "success": rc == 0,
                "error": stderr if rc != 0 else None,  # type: ignore
            })
            print(f"  [{'OK' if rc == 0 else 'FAIL'}] {i+1}/{len(top_rows)}: {question[:50]}...")

    report["stages"]["rewrite"] = {
        "success": True,
        "total": len(rewrite_results),
        "succeeded": sum(1 for r in rewrite_results if r.get("success")),
        "results": rewrite_results,
    }

    report_path = os.path.join(output_dir, "flow_report.json")
    save_json(report, report_path)
    print(f"\n[DONE] 管线 matrix 完成 → {report_path}")


def pipeline_mock(args: argparse.Namespace) -> None:
    """Mock 全链路演示：生成 5 个示例输出文件到 results/pipeline-demo/"""
    demo_dir = os.path.join(SCRIPT_DIR, "results", "pipeline-demo")
    os.makedirs(demo_dir, exist_ok=True)

    # 1. 01-keywords.csv
    keywords_csv = os.path.join(demo_dir, "01-keywords.csv")
    with open(keywords_csv, "w", encoding="utf-8") as f:
        f.write("关键词,搜索量,难度\n")
        f.write("AI 写作工具,12000,中\n")
        f.write("Python 自动生成文章,8500,低\n")
        f.write("GEO 搜索优化,6200,高\n")

    # 2. 02-rewritten.md — 基于 tests/test_data/article_health.md
    article_path = os.path.join(SCRIPT_DIR, "tests", "test_data", "article_health.md")
    article_content = ""
    if os.path.isfile(article_path):
        with open(article_path, "r", encoding="utf-8") as f:
            article_content = f.read()

    rewritten_md = os.path.join(demo_dir, "02-rewritten.md")
    with open(rewritten_md, "w", encoding="utf-8") as f:
        f.write("# 健康饮食指南（GEO Skills 改写版）\n\n")
        f.write("> [由 GEO Skills 改写] 基于原始文章优化，提升搜索引擎可见度\n\n")
        f.write("## 改写说明\n\n")
        f.write("本文基于原始文章进行五维度优化：\n\n")
        f.write('1. **关键词密度优化**：核心关键词\u201c健康饮食\u201d出现 8 次，密度 2.1%\n')
        f.write("2. **结构化增强**：增加 H2/H3 层级标题，添加要点列表\n")
        f.write(
            "3. **可读性提升**：段落长度从平均 120 字压缩到 60 字，"
            "Flesch 分数从 45 → 72\n"
        )
        f.write("4. **语义丰富度**：增加同义词、相关概念（营养均衡、膳食指南、食品安全）\n")
        f.write("5. **权威引用**：添加 WHO、中国营养学会等权威来源引用\n\n")
        f.write("---\n\n")
        f.write(article_content)

    # 3. 03-audit.md
    audit_md = os.path.join(demo_dir, "03-audit.md")
    with open(audit_md, "w", encoding="utf-8") as f:
        f.write("# GEO 审计报告\n\n")
        f.write("**审计对象**：`02-rewritten.md`  \n")
        f.write("**审计时间**：2026-07-12T10:30:00  \n\n")
        f.write("## 六维评分\n\n")
        f.write("| 维度 | 得分 | 满分 | 说明 |\n")
        f.write("|------|------|------|------|\n")
        f.write("| 关键词覆盖 | 8 | 10 | 核心词密度达标，长尾词覆盖一般 |\n")
        f.write("| 结构化程度 | 9 | 10 | H2/H3 层级清晰，要点列表完整 |\n")
        f.write("| 可读性 | 8 | 10 | 段落短小，但部分术语需解释 |\n")
        f.write("| 原创性 | 7 | 10 | 有一定改写但核心观点与原文重合度高 |\n")
        f.write("| 权威性 | 9 | 10 | 引用了 WHO 和营养学会来源 |\n")
        f.write("| E-E-A-T | 12 | 20 | 经验分享不足，缺少一手数据 |\n\n")
        f.write("**总分**：53 / 70（良好）\n\n")
        f.write("## 改进建议\n\n")
        f.write("1. 增加个人经验或案例分享以提升 E-E-A-T 得分\n")
        f.write("2. 补充具体数据（如营养素含量表）增强可信度\n")
        f.write("3. 添加内链指向相关主题文章\n")

    # 4. 04-tracker.json
    tracker_json = os.path.join(demo_dir, "04-tracker.json")
    tracker_data: dict = {
        "article": "健康饮食指南（GEO Skills 改写版）",
        "total_score": 53,
        "max_score": 70,
        "timestamp": "2026-07-12T10:30:00",
        "dimensions": {
            "keyword_coverage": 8,
            "structure": 9,
            "readability": 8,
            "originality": 7,
            "authority": 9,
            "eeat": 12,
        },
        "pipeline": "mock-demo",
    }
    with open(tracker_json, "w", encoding="utf-8") as f:
        json.dump(tracker_data, f, ensure_ascii=False, indent=2)

    # 5. 05-summary.md
    summary_md = os.path.join(demo_dir, "05-summary.md")
    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("# 全链路摘要\n\n")
        f.write("**管道模式**：full (mock)  \n")
        f.write("**执行时间**：2026-07-12T10:30:00  \n\n")
        f.write("| 步骤 | 输入 | 输出 | 耗时 |\n")
        f.write("|------|------|------|------|\n")
        f.write("| 1. 关键词扩展 | 种子词: AI工具 | `01-keywords.csv` (3行) | 0.2s |\n")
        f.write("| 2. 内容改写 | 原始文章 → geo_rewrite | `02-rewritten.md` | 0.5s |\n")
        f.write("| 3. GEO 审计 | 改写后文章 → audit | `03-audit.md` (53/70) | 0.3s |\n")
        f.write("| 4. 结果入库 | 审计结果 → tracker | `04-tracker.json` | 0.1s |\n")
        f.write("| 5. 摘要汇总 | 全链路数据 | `05-summary.md` | 0.1s |\n\n")
        f.write("**总耗时**：1.2s (mock)  \n")
        f.write("**输出目录**：`results/pipeline-demo/`\n")

    print("[MOCK] 全链路演示完成")
    print(f"  输出目录: {demo_dir}/")
    for fname in [
        "01-keywords.csv", "02-rewritten.md", "03-audit.md",
        "04-tracker.json", "05-summary.md",
    ]:
        fpath = os.path.join(demo_dir, fname)
        size = os.path.getsize(fpath)
        print(f"  [OK] {fname} ({size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GEOFlow — GEO 管道编排器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --mode full --keywords "AI工具,效率" --top 5
  %(prog)s --mode single --input article.md --brand "景一"
  %(prog)s --mode matrix --keywords "编程,Python" --top 20
  %(prog)s --mode full --keywords "健康,养生" --top 10 --dry-run
  %(prog)s --mode full --mock
        """,
    )

    parser.add_argument("--mode", required=True, choices=["full", "single", "matrix"],
                        help="管线模式: full(全流程) / single(单篇深度) / matrix(批量矩阵)")
    parser.add_argument("--keywords", default="",
                        help="种子关键词，逗号分隔 (full/matrix 模式)")
    parser.add_argument("--input", default="",
                        help="单篇文章路径 (single 模式)")
    parser.add_argument("--count", type=int, default=100,
                        help="expand 生成数量 (默认 100)")
    parser.add_argument("--top", type=int, default=10,
                        help="选取前 N 个问题改写 (默认 10)")
    parser.add_argument("--platform", default="",
                        help="目标平台 (zhihu/wechat/baijiahao/xiaohongshu)")
    parser.add_argument("--brand", default="",
                        help="品牌实体名称")
    parser.add_argument("--output-dir", default="",
                        help="输出目录 (默认 geo-skills/output/)")

    run_mode = parser.add_mutually_exclusive_group()
    run_mode.add_argument("--dry-run", action="store_true",
                           help="只打印执行计划，不调用 API")
    run_mode.add_argument("--mock", action="store_true",
                           help="Mock 全链路演示，生成示例输出文件")

    args = parser.parse_args()

    if args.mock:
        pipeline_mock(args)
        return

    if args.mode in ("full", "matrix") and not args.keywords:
        print(f"[ERROR] {args.mode} 模式需要 --keywords 参数", file=sys.stderr)
        sys.exit(1)

    if args.mode == "single" and not args.input:
        print("[ERROR] single 模式需要 --input 参数", file=sys.stderr)
        sys.exit(1)

    print(f"GEOFlow — mode={args.mode}" + (" [DRY-RUN]" if args.dry_run else ""))
    print(f"  脚本目录: {SCRIPT_DIR}")
    if args.output_dir:
        print(f"  输出目录: {args.output_dir}")

    if args.dry_run:
        print("\n--- 执行计划 ---")

    if args.mode == "full":
        pipeline_full(args)
    elif args.mode == "single":
        pipeline_single(args)
    elif args.mode == "matrix":
        pipeline_matrix(args)


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
