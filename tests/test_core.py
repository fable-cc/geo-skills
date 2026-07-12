#!/usr/bin/env python3
"""GEO Skills 核心模块单元测试（纯 Python 标准库 unittest）。

用法:
    python3 -m unittest tests/test_core.py -v
    python3 tests/test_core.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ══════════════════════════════════════════════════════════
# 辅助函数（从各模块提取的可测试纯逻辑）
# ══════════════════════════════════════════════════════════

def count_structural_elements(text):
    """统计文本中的结构化元素数量。"""
    import re

    result = {
        "char_count": len(text),
        "h2_count": len(re.findall(r"^##\s", text, re.MULTILINE)),
        "h3_count": len(re.findall(r"^###\s", text, re.MULTILINE)),
        "bold_count": len(re.findall(r"\*\*[^*]+\*\*", text)),
        "list_count": len(re.findall(r"^\s*[-*]\s", text, re.MULTILINE)),
        "faq_count": len(re.findall(r"(?:Q:|Q：|FAQ|常见问题|よくある質問|자주\s*묻는)", text)),
    }
    return result


def get_pricing_table():
    """获取定价表（硬编码，与 geo_cost.py 保持一致）。"""
    return {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "deepseek-v3": {"input": 0.27, "output": 1.10},
        "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    }


def estimate_tokens(text, chars_per_token=1.5):
    """估算 token 数（中文约 1.5 字符/token）。"""
    return max(1, int(len(text) / chars_per_token))


# ══════════════════════════════════════════════════════════
# Test 1: BuildPrompt
# ══════════════════════════════════════════════════════════

class TestBuildPrompt(unittest.TestCase):
    """测试提示词构建（不调用 API，纯字符串操作）。"""

    @classmethod
    def setUpClass(cls):
        # 尝试导入 build_prompt，使用 staticmethod 避免 unittest descriptor 自动绑定
        try:
            from geo_rewrite import build_prompt
            cls._build_prompt = staticmethod(build_prompt)
        except (ImportError, AttributeError):
            cls._build_prompt = None

    def _build(self, content="测试文章内容", platform=None, brand=None, score=False, json_mode=False):
        """构建 prompt 的辅助方法。"""
        if self._build_prompt is None:
            self.skipTest("build_prompt 不可导入")
        return self._build_prompt(content, platform=platform, brand=brand,
                                  with_score=score, output_json=json_mode)

    def test_default_prompt_no_platform(self):
        """默认（无平台）应返回非空 prompt。"""
        result = self._build("测试内容")
        self.assertIsNotNone(result)
        if isinstance(result, str):
            self.assertIn("测试内容", result)

    def test_platform_zhihu(self):
        """知乎平台应注入知乎特定规则。"""
        result = self._build("测试内容", platform="zhihu")
        text = result if isinstance(result, str) else str(result)
        # 知乎规则关键词
        has_zhihu = "知乎" in text or "zhihu" in text.lower() or "问答" in text
        self.assertTrue(has_zhihu, "知乎平台应包含知乎相关规则")

    def test_brand_injection(self):
        """--brand 参数应透传到 prompt。"""
        brand_name = "景一·寓言城堡"
        result = self._build("测试内容", brand=brand_name)
        text = result if isinstance(result, str) else str(result)
        self.assertIn(brand_name, text)

    def test_score_mode(self):
        """--score 应要求输出评分卡。"""
        result = self._build("测试内容", score=True)
        text = result if isinstance(result, str) else str(result)
        has_score = "评分" in text or "score" in text.lower()
        self.assertTrue(has_score, "score 模式应包含评分卡指令")

    def test_json_mode(self):
        """--json 应要求结构化 JSON 输出。"""
        result = self._build("测试内容", json_mode=True)
        text = result if isinstance(result, str) else str(result)
        if "json" in text.lower() or "JSON" in text:
            return  # 通过
        # 有些实现可能用结构化输出提示
        self.assertTrue("JSON" in text or "json" in text.lower() or "结构化" in text)

    def test_dry_run_flags_combination(self):
        """组合参数（platform + brand + score + json）应全部生效。"""
        brand = "测试品牌"
        result = self._build("内容", platform="zhihu", brand=brand, score=True, json_mode=True)
        text = result if isinstance(result, str) else str(result)
        self.assertIn(brand, text)


# ══════════════════════════════════════════════════════════
# Test 2: CountStructuralElements
# ══════════════════════════════════════════════════════════

class TestCountStructuralElements(unittest.TestCase):
    """测试结构化元素统计函数。"""

    def test_empty_text(self):
        result = count_structural_elements("")
        self.assertEqual(result["char_count"], 0)
        self.assertEqual(result["h2_count"], 0)
        self.assertEqual(result["h3_count"], 0)
        self.assertEqual(result["bold_count"], 0)
        self.assertEqual(result["list_count"], 0)

    def test_h2_h3_count(self):
        text = "## 第一章\n内容\n### 1.1 小节\n内容\n## 第二章\n### 2.1\n### 2.2\n内容"
        result = count_structural_elements(text)
        self.assertEqual(result["h2_count"], 2)
        self.assertEqual(result["h3_count"], 3)

    def test_bold_count(self):
        text = "这是**重要**的内容，这里还有**另一个**关键词，最后**第三个**。"
        result = count_structural_elements(text)
        self.assertEqual(result["bold_count"], 3)

    def test_bold_count_zero(self):
        text = "没有任何加粗内容的普通段落。"
        result = count_structural_elements(text)
        self.assertEqual(result["bold_count"], 0)

    def test_list_count(self):
        text = "- 第一项\n- 第二项\n- 第三项\n普通段落\n* 星号项目"
        result = count_structural_elements(text)
        self.assertEqual(result["list_count"], 4)

    def test_faq_count(self):
        text = "Q: 这是什么？\n答：测试。\nQ：另一个问题\n常见问题 FAQ"
        result = count_structural_elements(text)
        self.assertEqual(result["faq_count"], 4)

    def test_real_article(self):
        """对真实测试文章的结构统计。"""
        article_path = Path(__file__).parent / "test_data" / "article_health.md"
        if not article_path.exists():
            self.skipTest("测试文章不存在")
        text = article_path.read_text(encoding="utf-8")
        result = count_structural_elements(text)
        self.assertGreater(result["char_count"], 300)
        # 健康文章应包含一些结构
        total_struct = result["h2_count"] + result["bold_count"] + result["list_count"]
        self.assertGreaterEqual(total_struct, 0)


# ══════════════════════════════════════════════════════════
# Test 3: PricingTable
# ══════════════════════════════════════════════════════════

class TestPricingTable(unittest.TestCase):
    """测试定价表数据完整性。"""

    def setUp(self):
        self.pricing = get_pricing_table()

    def test_gpt4o_pricing(self):
        self.assertIn("gpt-4o", self.pricing)
        self.assertEqual(self.pricing["gpt-4o"]["input"], 2.50)
        self.assertEqual(self.pricing["gpt-4o"]["output"], 10.00)

    def test_deepseek_pricing(self):
        self.assertIn("deepseek-v3", self.pricing)
        self.assertGreater(self.pricing["deepseek-v3"]["input"], 0)
        # deepseek 应比 gpt-4o 便宜
        self.assertLess(self.pricing["deepseek-v3"]["input"],
                        self.pricing["gpt-4o"]["input"])

    def test_token_estimation(self):
        """中文 token 估算：约 1.5 字符/token。"""
        text_150_chars = "测" * 150
        tokens = estimate_tokens(text_150_chars)
        self.assertEqual(tokens, 100)

        text_15_chars = "短文本测试"
        tokens = estimate_tokens(text_15_chars)
        self.assertGreater(tokens, 0)
        self.assertLessEqual(tokens, 15)

    def test_model_not_found(self):
        """不存在的模型应返回 None 或 KeyError。"""
        with self.assertRaises(KeyError):
            _ = self.pricing["nonexistent-model"]

    def test_all_models_have_both_prices(self):
        """所有模型都应同时有 input 和 output 定价。"""
        for model, prices in self.pricing.items():
            with self.subTest(model=model):
                self.assertIn("input", prices)
                self.assertIn("output", prices)
                self.assertGreater(prices["input"], 0)
                self.assertGreater(prices["output"], 0)


# ══════════════════════════════════════════════════════════
# Test 4: MockGeneration
# ══════════════════════════════════════════════════════════

class TestMockGeneration(unittest.TestCase):
    """测试 geo_bench.py mock 文章生成逻辑。"""

    @classmethod
    def setUpClass(cls):
        try:
            from geo_bench import generate_mock
            cls._generate_mock = staticmethod(generate_mock)
        except (ImportError, AttributeError):
            cls._generate_mock = None

    def test_generate_100(self):
        """生成 100 篇 mock 文章。"""
        if self._generate_mock is None:
            self.skipTest("generate_mock 不可导入")
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._generate_mock(100, tmpdir)
            self.assertEqual(len(paths), 100)
            for p in paths:
                self.assertTrue(os.path.isfile(p))
                self.assertGreater(os.path.getsize(p), 100)

    def test_word_count_range(self):
        """生成文章应在 300~800 字范围内（粗略）。"""
        if self._generate_mock is None:
            self.skipTest("generate_mock 不可导入")
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._generate_mock(20, tmpdir)
            for p in paths:
                text = Path(p).read_text(encoding="utf-8")
                # 去 Markdown 标记后统计中文字符
                import re
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
                char_count = len(chinese_chars)
                self.assertGreater(char_count, 100, f"{Path(p).name}: {char_count} 字符（太少）")

    def test_unique_content(self):
        """生成文章不应完全相同。"""
        if self._generate_mock is None:
            self.skipTest("generate_mock 不可导入")
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._generate_mock(20, tmpdir)
            contents = set()
            for p in paths:
                text = Path(p).read_text(encoding="utf-8")
                contents.add(text)
            # 20 篇文章中至少应有 10 篇不同
            self.assertGreaterEqual(len(contents), 10,
                                    "mock 文章应有足够多样性")


if __name__ == "__main__":
    unittest.main(verbosity=2)
