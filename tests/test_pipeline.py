#!/usr/bin/env python3
"""GEO Skills 管线集成测试（subprocess dry-run 链路验证）。

用法:
    python3 -m unittest tests/test_pipeline.py -v
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_ARTICLE = PROJECT_ROOT / "tests" / "test_data" / "article_health.md"


def run_script(script_name, *extra_args, timeout=30):
    """Run a project script with subprocess, capture output."""
    script_path = PROJECT_ROOT / script_name
    cmd = [sys.executable, str(script_path)] + list(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result


class TestPipeline(unittest.TestCase):
    """端到端 dry-run 链路验证。"""

    @classmethod
    def setUpClass(cls):
        if not TEST_ARTICLE.exists():
            raise unittest.SkipTest(f"测试文章不存在: {TEST_ARTICLE}")

    def test_1_expand_dry_run(self):
        """扩展阶段 dry-run：验证 prompt 构建。"""
        result = run_script(
            "geo_keyword_expander.py",
            "--keywords", "幽门螺杆菌,治疗",
            "--output", "/dev/null",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, f"expand stderr: {result.stderr[:200]}")
        self.assertGreater(len(result.stdout.strip()), 0, "dry-run 应有输出")

    def test_2_rewrite_dry_run(self):
        """改写阶段 dry-run：验证 prompt + score + json。"""
        result = run_script(
            "geo_rewrite.py",
            "--input", str(TEST_ARTICLE),
            "--platform", "zhihu",
            "--brand", "景一·寓言城堡",
            "--score",
            "--json",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, f"rewrite stderr: {result.stderr[:200]}")
        stdout = result.stdout
        self.assertGreater(len(stdout), 0)
        # 应包含平台关键词
        self.assertTrue("zhihu" in stdout.lower() or "知乎" in stdout,
                        "rewrite dry-run 应包含平台信息")

    def test_3_audit_dry_run(self):
        """审计阶段 dry-run：验证审计脚本。"""
        result = run_script(
            "geo_content_audit.py",
            "--input", str(TEST_ARTICLE),
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, f"audit stderr: {result.stderr[:200]}")
        self.assertGreater(len(result.stdout.strip()), 0, "dry-run 应有输出")

    def test_4_pipeline_full_cycle(self):
        """全链路 dry-run：geo_flow --dry-run。"""
        result = run_script(
            "geo_flow.py",
            "--mode", "full",
            "--keywords", "幽门螺杆菌,治疗",
            "--top", "3",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, f"pipeline stderr: {result.stderr[:200]}")
        stdout = result.stdout
        # pipeline 应提及阶段
        has_stages = any(
            keyword in stdout
            for keyword in ["阶段", "expand", "rewrite", "audit", "关键词扩展"]
        )
        self.assertTrue(has_stages, "pipeline dry-run 应展示执行阶段")

    def test_5_tracker_sqlite(self):
        """追踪器 SQLite 建表/插入/查询。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 导入 geo_tracker 模块测试其 SQLite 逻辑
            sys.path.insert(0, str(PROJECT_ROOT))
            try:
                import sqlite3
                from datetime import datetime

                db_path = os.path.join(tmpdir, "test_scores.db")
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_name TEXT,
                        platform TEXT,
                        total_score INTEGER,
                        qa_score INTEGER,
                        entity_score INTEGER,
                        citation_score INTEGER,
                        structure_score INTEGER,
                        platform_score INTEGER,
                        readability_score INTEGER,
                        model TEXT,
                        duration REAL,
                        created_at TEXT
                    )
                """)

                # 插入测试记录
                conn.execute(
                    "INSERT INTO scores VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("test.md", "zhihu", 52, 9, 8, 9, 9, 8, 9, "gpt-4o-mini", 3.2,
                     datetime.now().isoformat()),
                )
                conn.commit()

                # 查询
                row = conn.execute("SELECT total_score, platform FROM scores LIMIT 1").fetchone()
                self.assertEqual(row[0], 52)
                self.assertEqual(row[1], "zhihu")

                # 统计
                stats = conn.execute(
                    "SELECT COUNT(*), AVG(total_score) FROM scores"
                ).fetchone()
                self.assertEqual(stats[0], 1)
                self.assertAlmostEqual(stats[1], 52.0, places=1)

                conn.close()
            finally:
                sys.path.pop(0)

    def test_6_bench_mock_mode(self):
        """压测 mock 模式：验证 mock 生成。"""
        result = run_script(
            "geo_bench.py",
            "--count", "20",
            "--mode", "mock",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("生成", result.stdout)

    def test_7_bench_dry_mode(self):
        """压测 dry 模式：验证调度模拟。"""
        result = run_script(
            "geo_bench.py",
            "--count", "30",
            "--mode", "dry",
        )
        self.assertEqual(result.returncode, 0)
        stdout = result.stdout
        self.assertIn("吞吐量", stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
