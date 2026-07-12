#!/usr/bin/env python3
"""Tests for geo_watch.py — dry-run / arg parsing / import."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWatchDryRun(unittest.TestCase):
    def test_watch_dry_run(self):
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "geo_watch.py",
                    ),
                    "--dir", tmpdir,
                    "--dry-run",
                    "--once",
                ],
                capture_output=True, text=True, timeout=15,
                env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))},
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("DRY-RUN", result.stdout + result.stderr)


class TestWatchArgParsing(unittest.TestCase):
    def test_watch_arg_parsing(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "geo_watch", "--help"],
            capture_output=True, text=True, timeout=10,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))},
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--dry-run", result.stdout)


class TestImportModule(unittest.TestCase):
    def test_import_module(self):
        import geo_watch

        self.assertTrue(hasattr(geo_watch, "main"))
        self.assertTrue(hasattr(geo_watch, "process_file"))


if __name__ == "__main__":
    unittest.main()
