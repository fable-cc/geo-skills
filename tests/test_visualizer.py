#!/usr/bin/env python3
"""Tests for visualizer.py — import / dry-run / arg parsing."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImportModule(unittest.TestCase):
    def test_import_module(self):
        import visualizer

        self.assertTrue(hasattr(visualizer, "main"))
        self.assertTrue(hasattr(visualizer, "count_stats"))


class TestDryRun(unittest.TestCase):
    def test_dry_run(self):
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f_before:
            f_before.write("# Test Article\n\nThis is a test article.\n")
            before_path = f_before.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f_after:
            f_after.write("# Test Article GEO\n\n## FAQ\n\nQ: Test?\nA: Yes.\n")
            after_path = f_after.name

        try:
            out_path = os.path.join(tempfile.gettempdir(), "test_report.html")
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "visualizer.py",
                    ),
                    "--input-before", before_path,
                    "--input-after", after_path,
                    "--output", out_path,
                ],
                capture_output=True, text=True, timeout=15,
                env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))},
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.isfile(out_path))
            with open(out_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<html", content)
            self.assertGreater(len(content), 1000)
        finally:
            for p in [before_path, after_path]:
                if os.path.isfile(p):
                    os.unlink(p)


class TestArgParsing(unittest.TestCase):
    def test_arg_parsing(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "visualizer", "--help"],
            capture_output=True, text=True, timeout=10,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))},
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--input-before", result.stdout)
        self.assertIn("--input-after", result.stdout)


if __name__ == "__main__":
    unittest.main()
