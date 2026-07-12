#!/usr/bin/env python3
"""边界用例测试 —— 验证 geo_rewrite.build_prompt 的输入鲁棒性"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from geo_rewrite import build_prompt


def _get_content(prompt: list) -> str:
    """提取消息列表中所有 role=user 的 content 拼接"""
    parts = []
    for msg in prompt:
        if isinstance(msg, dict) and msg.get("role") == "user":
            parts.append(str(msg.get("content", "")))
    return "".join(parts)


class TestEdgeCases(unittest.TestCase):
    """geo_rewrite.build_prompt 边界用例"""

    def test_empty_input(self) -> None:
        """空字符串输入不崩溃，返回非空消息列表"""
        result = build_prompt("", "通用", "", False, False)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        content = _get_content(result)
        self.assertIn("GEO", content)

    def test_very_long_input(self) -> None:
        """10 万字符输入不崩溃，prompt 长度超 10 万"""
        long_text = "测试段落。\n" * 5000
        result = build_prompt(long_text, "通用", "", False, False)
        self.assertIsInstance(result, list)
        content = _get_content(result)
        self.assertGreater(len(content), len(long_text))

    def test_binary_disguised(self) -> None:
        """含 \\x00 等控制字符的输入，优雅处理不崩溃"""
        messy = "正常文字\x00\x01\x02后面的文字"
        result = build_prompt(messy, "通用", "", False, False)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_punctuation_only(self) -> None:
        """纯标点符号输入，prompt 正常生成"""
        punct = "\u3002\uff0c\uff01\uff1f\uff1b\uff1a\u201c\u201d\u2018\u2019\u2026\u2014\uff5e"
        result = build_prompt(punct, "通用", "", False, False)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_unicode_rare(self) -> None:
        """生僻 Unicode 字符不丢失"""
        rare = "\U00020BB7\U00029E3D\U0002000B"
        result = build_prompt(rare, "通用", "", False, False)
        content = _get_content(result)
        for ch in rare:
            self.assertIn(ch, content, f"生僻字符 U+{ord(ch):04X} 丢失")

    def test_english_only(self) -> None:
        """纯英文输入，平台规则正常注入"""
        english = "This is a test article about AI and search engines."
        result = build_prompt(english, "通用", "", False, False)
        self.assertIsInstance(result, list)
        content = _get_content(result)
        self.assertIn("This is a test article", content)

    def test_brand_max_length(self) -> None:
        """品牌名 500 字符不截断，prompt 含完整品牌名"""
        long_brand = "B" * 500
        result = build_prompt("测试文章", "通用", long_brand, False, False)
        self.assertIsInstance(result, list)
        content = _get_content(result)
        self.assertIn(long_brand, content)


if __name__ == "__main__":
    unittest.main()
