#!/usr/bin/env python3
"""
GEO 评分追踪器 — 记录每次改写的评分卡数据，支持统计和趋势分析

用法：
  python3 geo_tracker.py --add --input rewrite-output.md
  python3 geo_tracker.py --list
  python3 geo_tracker.py --stats
  python3 geo_tracker.py --trend
  python3 geo_tracker.py --export scores.csv
"""

import argparse
import csv
import os
import re
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_scores.db")


def get_db():
    """Get or create database connection and table."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            platform TEXT DEFAULT '通用',
            model TEXT DEFAULT '',
            score_qa INTEGER DEFAULT 0,
            score_entity INTEGER DEFAULT 0,
            score_citation INTEGER DEFAULT 0,
            score_structure INTEGER DEFAULT 0,
            score_platform INTEGER DEFAULT 0,
            score_readability INTEGER DEFAULT 0,
            score_total INTEGER DEFAULT 0,
            word_count_before INTEGER DEFAULT 0,
            word_count_after INTEGER DEFAULT 0,
            duration_seconds REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def parse_score_from_text(text):
    """Attempt to extract GEO score card from audit output.

    Looks for patterns like:
      - 问答可见性: 8/10
      - 六维总分: 42/60
      - Score: 问答结构化 7, 实体植入 8 ...
    """
    scores = {
        "score_qa": 0,
        "score_entity": 0,
        "score_citation": 0,
        "score_structure": 0,
        "score_platform": 0,
        "score_readability": 0,
        "score_total": 0,
    }

    # Pattern 1: 维度名: N/10
    dim_patterns = [
        (r'问答[可结]?[见构]?[性化]?\s*[:：]\s*(\d+)', "score_qa"),
        (r'实体[密植][度入]\s*[:：]\s*(\d+)', "score_entity"),
        (r'引用[锚点]?\s*[:：]\s*(\d+)', "score_citation"),
        (r'结构[化标][标记]?\s*[:：]\s*(\d+)', "score_structure"),
        (r'平台[适配]?\s*[:：]\s*(\d+)', "score_platform"),
        (r'可读性\s*[:：]\s*(\d+)', "score_readability"),
    ]

    for pattern, key in dim_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            scores[key] = int(m.group(1))

    # Total score
    total_m = re.search(r'(?:总分|总计|total)\s*[:：]\s*(\d+)', text, re.IGNORECASE)
    if total_m:
        scores["score_total"] = int(total_m.group(1))
    else:
        scores["score_total"] = sum(scores[k] for k in [
            "score_qa", "score_entity", "score_citation",
            "score_structure", "score_platform", "score_readability",
        ])

    return scores


def parse_file_info(file_path):
    """Extract info from audit/rewrite output file."""
    if not os.path.isfile(file_path):
        print(f"[ERROR] 文件未找到: {file_path}", file=sys.stderr)
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    scores = parse_score_from_text(content)

    # Try to extract platform and word count
    platform = "通用"
    plat_m = re.search(r'平台\s*[:：]\s*(\S+)', content)
    if plat_m:
        platform = plat_m.group(1)

    word_count_before = len(content)
    word_count_after = len(content)

    wc_before_m = re.search(r'(?:原文|改写前)\s*字数\s*[:：]\s*(\d+)', content)
    if wc_before_m:
        word_count_before = int(wc_before_m.group(1))

    wc_after_m = re.search(r'(?:改写后|输出)\s*字数\s*[:：]\s*(\d+)', content)
    if wc_after_m:
        word_count_after = int(wc_after_m.group(1))

    file_name = os.path.basename(file_path)

    return {
        "file_name": file_name,
        "platform": platform,
        "word_count_before": word_count_before,
        "word_count_after": word_count_after,
        **scores,
    }


def cmd_add(args):
    """Add a score record from an audit/rewrite output file."""
    info = parse_file_info(args.input)
    if info is None:
        sys.exit(1)

    conn = get_db()
    conn.execute("""
        INSERT INTO scores
            (file_name, platform, model, score_qa, score_entity,
             score_citation, score_structure, score_platform,
             score_readability, score_total, word_count_before,
             word_count_after, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        info["file_name"],
        info.get("platform", "通用"),
        args.model or "",
        info.get("score_qa", 0),
        info.get("score_entity", 0),
        info.get("score_citation", 0),
        info.get("score_structure", 0),
        info.get("score_platform", 0),
        info.get("score_readability", 0),
        info.get("score_total", 0),
        info.get("word_count_before", 0),
        info.get("word_count_after", 0),
        args.duration or 0.0,
    ))
    conn.commit()

    print(f"[OK] 已添加评分记录")
    print(f"  文件: {info['file_name']}")
    print(f"  总分: {info['score_total']}/60")
    print(f"  平台: {info.get('platform', '通用')}")


def cmd_list(args):
    """List recent 20 score records."""
    conn = get_db()
    limit = args.limit or 20
    rows = conn.execute(
        "SELECT id, file_name, platform, model, score_total, word_count_after, created_at "
        "FROM scores ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()

    if not rows:
        print("暂无评分记录。使用 --add 添加第一条记录。")
        return

    print(f"{'ID':>4}  {'文件名':<35} {'平台':<8} {'模型':<16} {'总分':>4} {'字数':>6}  {'时间'}")
    print("-" * 100)
    for r in rows:
        fid, fname, plat, model, total, wc, ts = r
        fname = fname[:33] + ".." if len(fname) > 35 else fname
        model = (model[:14] + "..") if len(model) > 16 else model
        print(f"{fid:>4}  {fname:<35} {plat or '-':<8} {model or '-':<16} {total:>4} {wc:>6}  {ts or '-'}")

    total = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    print(f"\n共 {total} 条记录，显示最近 {min(limit, len(rows))} 条")


def cmd_stats(args):
    """Print summary statistics."""
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    if total == 0:
        print("暂无评分记录。")
        return

    avg = conn.execute("SELECT AVG(score_total) FROM scores").fetchone()[0] or 0
    max_s = conn.execute("SELECT MAX(score_total) FROM scores").fetchone()[0] or 0
    min_s = conn.execute("SELECT MIN(score_total) FROM scores").fetchone()[0] or 0

    dims = conn.execute("""
        SELECT
            AVG(score_qa), AVG(score_entity), AVG(score_citation),
            AVG(score_structure), AVG(score_platform), AVG(score_readability)
        FROM scores
    """).fetchone()

    dim_avg = {
        "问答可见性": dims[0] or 0,
        "实体密度": dims[1] or 0,
        "引用锚点": dims[2] or 0,
        "结构化标记": dims[3] or 0,
        "平台适配": dims[4] or 0,
        "可读性": dims[5] or 0,
    }

    best = conn.execute(
        "SELECT file_name, score_total, created_at FROM scores ORDER BY score_total DESC LIMIT 1"
    ).fetchone()

    print("GEO 评分追踪 — 汇总统计")
    print("=" * 50)
    print(f"  总改写次数: {total}")
    print(f"  平均总分:   {avg:.1f}/60")
    print(f"  最高总分:   {max_s}/60" + (f" ({best[0]} @ {best[2]})" if best else ""))
    print(f"  最低总分:   {min_s}/60")
    print()
    print("  各维度均分:")
    for dim, val in dim_avg.items():
        bar = "█" * int(val) + "░" * (10 - int(val))
        print(f"    {dim:<10} {bar} {val:.1f}/10")

    # Platform breakdown
    plat_stats = conn.execute(
        "SELECT platform, COUNT(*), AVG(score_total) FROM scores GROUP BY platform"
    ).fetchall()
    if plat_stats and len(plat_stats) > 1:
        print("\n  按平台统计:")
        for plat, cnt, pavg in plat_stats:
            print(f"    {plat:<12} {cnt:>3} 篇  均分 {pavg:.1f}")


def cmd_trend(args):
    """Print ASCII trend line chart of recent scores."""
    conn = get_db()
    limit = args.limit or 20
    rows = conn.execute(
        "SELECT id, score_total, file_name FROM scores ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()

    if not rows:
        print("暂无评分记录。")
        return

    rows = list(reversed(rows))  # oldest first

    scores = [r[1] for r in rows]
    max_s = max(scores)
    min_s = min(scores) if scores else 0
    range_s = max(max_s - min_s, 1)

    height = 15
    chart = [[" " for _ in range(len(scores))] for _ in range(height)]

    for x, s in enumerate(scores):
        y = height - 1 - int((s - min_s) / range_s * (height - 1))
        y = max(0, min(height - 1, y))
        chart[y][x] = "●"

    # Connect dots
    for x in range(len(scores) - 1):
        y1 = height - 1 - int((scores[x] - min_s) / range_s * (height - 1))
        y2 = height - 1 - int((scores[x + 1] - min_s) / range_s * (height - 1))
        y1 = max(0, min(height - 1, y1))
        y2 = max(0, min(height - 1, y2))

        if y1 == y2:
            continue
        step = 1 if y2 > y1 else -1
        for yy in range(y1 + step, y2, step):
            chart[yy][x] = "─" if step > 0 else "─"
            chart[yy][x + 1] = "─" if step > 0 else "─"

    print("\nGEO 评分趋势 (最近 {} 次)".format(len(rows)))
    print("=" * (len(scores) + 10))
    for y, line in enumerate(chart):
        val = max_s - (y * range_s / (height - 1))
        label = f"{val:5.0f} │" if y % 3 == 0 else "      │"
        print(label + "".join(line))

    print("      └" + "─" * len(scores))
    # Print first and last ID
    print(f"       {rows[0][0]}{' ' * (len(scores) - len(str(rows[-1][0])) - 1)}{rows[-1][0]}")
    print(f"       ID 范围: {rows[0][0]} → {rows[-1][0]}  分数: {scores[0]} → {scores[-1]}")


def cmd_export(args):
    """Export scores to CSV."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, file_name, platform, model, score_qa, score_entity, score_citation, "
        "score_structure, score_platform, score_readability, score_total, "
        "word_count_before, word_count_after, duration_seconds, created_at "
        "FROM scores ORDER BY id"
    ).fetchall()

    if not rows:
        print("暂无评分记录。")
        return

    output_path = args.output or "geo_scores_export.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "file_name", "platform", "model",
            "score_qa", "score_entity", "score_citation",
            "score_structure", "score_platform", "score_readability",
            "score_total", "word_count_before", "word_count_after",
            "duration_seconds", "created_at",
        ])
        writer.writerows(rows)

    print(f"[OK] 已导出 {len(rows)} 条记录 → {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GEO 评分追踪器 — 记录/查看/分析改写评分",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --add --input article-audit.md          # 添加评分记录
  %(prog)s --list                                   # 查看最近 20 条
  %(prog)s --stats                                  # 汇总统计
  %(prog)s --trend                                  # 趋势图
  %(prog)s --export scores.csv                      # 导出 CSV
        """,
    )

    parser.add_argument("--add", action="store_true", help="添加评分记录")
    parser.add_argument("--input", default="", help="输入文件路径（audit 输出）")
    parser.add_argument("--model", default="", help="模型名称")
    parser.add_argument("--duration", type=float, default=0.0, help="处理时长（秒）")

    parser.add_argument("--list", action="store_true", help="列出最近评分记录")
    parser.add_argument("--limit", type=int, default=20, help="列出条数上限 (默认 20)")

    parser.add_argument("--stats", action="store_true", help="汇总统计")
    parser.add_argument("--trend", action="store_true", help="趋势图")
    parser.add_argument("--export", action="store_true", help="导出 CSV")
    parser.add_argument("--output", default="", help="导出路径")

    args = parser.parse_args()

    # Determine command
    if args.add:
        if not args.input:
            print("[ERROR] --add 需要 --input 参数", file=sys.stderr)
            sys.exit(1)
        cmd_add(args)
    elif args.list:
        cmd_list(args)
    elif args.stats:
        cmd_stats(args)
    elif args.trend:
        cmd_trend(args)
    elif args.export:
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
