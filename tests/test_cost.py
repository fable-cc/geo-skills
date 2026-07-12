#!/usr/bin/env python3
"""Tests for geo_cost.py — pricing / token estimation / dashboard output."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geo_cost


class TestPricingModel(unittest.TestCase):
    def test_pricing_model_exists(self):
        self.assertIn("gpt-4o-mini", geo_cost.PRICING)
        self.assertIn("input", geo_cost.PRICING["gpt-4o-mini"])
        self.assertIn("output", geo_cost.PRICING["gpt-4o-mini"])


class TestTokenEstimation(unittest.TestCase):
    def test_token_estimation(self):
        result = geo_cost.chars_to_tokens(1000)
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)
        self.assertLess(result, 2000)


class TestDashboardOutput(unittest.TestCase):
    def test_dashboard_output(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "-c", "import geo_cost; geo_cost.cmd_dashboard(None)"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=15,
            env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))},
        )

        dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "results", "cost-dashboard.html",
        )
        self.assertTrue(
            os.path.isfile(dashboard_path),
            f"Dashboard not found at {dashboard_path}",
        )
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<html", content)
        self.assertIn("GEO Skills", content)


if __name__ == "__main__":
    unittest.main()
