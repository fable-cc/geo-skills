#!/usr/bin/env python3
"""Tests for geo_notify.py — URL detection / import."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geo_notify


class TestSlackUrlDetection(unittest.TestCase):
    def test_slack_url_detection(self):
        result = geo_notify.detect_platform(
            "https://hooks.slack.com/services/T000/B000/xxxx"
        )
        self.assertEqual(result, "slack")


class TestDingtalkUrlDetection(unittest.TestCase):
    def test_dingtalk_url_detection(self):
        result = geo_notify.detect_platform(
            "https://oapi.dingtalk.com/robot/send?access_token=xxx"
        )
        self.assertEqual(result, "dingtalk")


class TestImportModule(unittest.TestCase):
    def test_import_module(self):
        self.assertTrue(hasattr(geo_notify, "main"))
        self.assertTrue(hasattr(geo_notify, "detect_platform"))


if __name__ == "__main__":
    unittest.main()
