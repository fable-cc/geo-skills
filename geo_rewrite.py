#!/usr/bin/env python3
"""GEO 改写脚本 —— 调用 OpenAI 兼容 API，将普通文章优化为 AI 搜索引擎友好版本。

用法:
    python3 geo_rewrite.py --input 文章.md --output 文章-geo.md
    python3 geo_rewrite.py --input 文章.md --platform zhihu
    python3 geo_rewrite.py --input 文章.md --dry-run
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ═══════════════════════════════════════════════════
# GEO 改写提示词（内嵌为字符串常量，不依赖外部文件）
# ═══════════════════════════════════════════════════

GEO_SYSTEM_PROMPT = """你是一名 GEO（Generative Engine Optimization，生成式引擎优化）内容优化专家。你的任务是接收一篇普通文章，将其改写为 AI 搜索引擎（如 ChatGPT Search、Perplexity、DeepSeek、豆包、Kimi）更愿意抓取、引用和推荐的版本。你精通五维改写规则：问答结构化、实体植入、引用锚点、结构化标记、平台适配。改写后的文章仍然是一篇人读得懂、读得舒服的文章，但机器会优先提取和推荐它。"""

GEO_REWRITE_INSTRUCTION = """
### 第一步：结构分析
阅读原文，识别核心问题、关键词、实体词。

### 第二步：GEO 改造（5 条规则）

规则 1 - 问答结构化：开头 150 字内直接回答核心问题。
规则 2 - 实体植入：品牌实体在正文中出现 3 次以上，加限定词形成差异化。
规则 3 - 引用锚点：所有数据标注来源（机构 + 年份 + 报告名称）。
规则 4 - 结构化标记：H2/H3 + 列表 + 加粗关键词 + FAQ 区块（至少3组）。
规则 5 - 平台适配：{platform_rule}

### 第三步：质量检查
- [ ] 前 150 字是否直接回答核心问题
- [ ] 核心品牌实体出现 3 次以上
- [ ] 所有数据标注了来源
- [ ] 使用 H2/H3 + 列表 + FAQ 格式
- [ ] 核心关键词在标题/首段/H2 中出现
- [ ] 符合平台适配策略

用以下评分卡打分（满分 60，低于 42 分需重新改写）：

| 维度 | 分数 |
|------|------|
| 问答结构化 | /10 |
| 实体植入 | /10 |
| 引用锚点 | /10 |
| 结构化标记 | /10 |
| 平台适配 | /10 |
| 可读性 | /10 |
| **总分** | /60 |

最后输出改写后的 Markdown 正文。只输出正文，不要输出评分卡、不要加解释说明。
"""

PLATFORM_RULES = {
    "zhihu": "知乎平台：开头用'先说结论'直接抛出答案，正文中间插入2-3个引导互动的话语，FAQ区块保留并扩展。标题含核心关键词，段落适中。",
    "wechat": "微信公众号平台：标题用对话感（'你体检报告上这个指标……'），每段不超过4行留白多，加粗关键词密度高（每段2-3处），文末加CTA引导关注。",
    "baijiahao": "百家号/头条号平台：标题含核心关键词2次以上，首段必须含关键词，每300字插入H3小标题，避免明显营销化表述。",
    "xiaohongshu": "小红书平台：开篇用emoji+一句话结论，全文不超过800字，短句+换行代替长段落，关键词用#话题标签穿插，结尾加互动提问。",
}

PLATFORM_RULE_DEFAULT = "通用平台：按照标准GEO五维规则改写，不做特定平台优化。适用于网页发布、通用文档等场景。"


def build_prompt(article: str, platform: str | None) -> list[dict]:
    """构建发送给 LLM 的消息列表。"""
    rule = PLATFORM_RULES.get(platform, PLATFORM_RULE_DEFAULT) if platform else PLATFORM_RULE_DEFAULT
    instruction = GEO_REWRITE_INSTRUCTION.format(platform_rule=rule)
    user_message = f"请改写以下文章：\n\n{article}"

    return [
        {"role": "system", "content": GEO_SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
        {"role": "user", "content": user_message},
    ]


def call_llm(messages: list[dict], config: dict) -> str:
    """调用 OpenAI 兼容 API 并返回回答文本。"""
    api_base = config["api_base"].rstrip("/")
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "model": config["model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []

    try:
        with urllib.request.build_opener(*handlers).open(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API 请求失败 (HTTP {e.code}): {body_text}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络错误: {e.reason}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"API 返回格式异常: {e}")


def print_summary(original: str, rewritten: str, platform: str | None):
    """打印改写摘要。"""
    platform_name = platform or "通用"
    word_before = len(original)
    word_after = len(rewritten)
    print(f"""
══════════════  GEO 改写摘要  ══════════════
目标平台：{platform_name}
原文字数：{word_before}
改写后字数：{word_after}

五维改动：
  1. 问答结构化  → 结论前置，开头 150 字内给出直接答案
  2. 实体植入    → 品牌实体在正文中出现 3 次以上
  3. 引用锚点    → 数据/结论标注来源（机构+年份+报告）
  4. 结构化标记  → H2/H3 + 列表 + 加粗 + FAQ 区块
  5. 平台适配    → 按 {platform_name} 平台偏好调整格式和语气

改写原理：AI 搜索引擎按「相关性 > 权威性 > 结构化程度 > 引用密度」
排序。改写后的文章在以上四个维度均得到了增强。
══════════════════════════════════════════════
""".strip())


def main():
    parser = argparse.ArgumentParser(
        description="GEO 改写 —— 将普通文章优化为 AI 搜索引擎友好版本",
        epilog="示例: python3 geo_rewrite.py --input 文章.md --output 文章-geo.md",
    )
    parser.add_argument("--input", required=True, help="输入文章路径 (.md)")
    parser.add_argument("--output", default=None, help="输出路径（默认: 原名-geo.md）")
    parser.add_argument("--platform", choices=["zhihu", "wechat", "baijiahao", "xiaohongshu"],
                        default=None, help="目标平台")
    parser.add_argument("--dry-run", action="store_true", help="只打印构建的 prompt，不调用 API")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        sys.exit(f"错误: 找不到文件 {args.input}")

    output_path = Path(args.output) if args.output else input_path.with_stem(f"{input_path.stem}-geo")

    article = input_path.read_text(encoding="utf-8")
    messages = build_prompt(article, args.platform)

    if args.dry_run:
        print("═══════ DRY RUN —— 以下为构建的 prompt（不调用 API）═══════\n")
        for i, msg in enumerate(messages):
            print(f"[Message {i + 1}] Role: {msg['role']}")
            print(msg["content"])
            print("---\n")
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("错误: 未设置 OPENAI_API_KEY 环境变量")

    config = {
        "api_key": api_key,
        "api_base": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
    }

    print(f"正在调用 {config['model']} 进行 GEO 改写...\n")
    rewritten = call_llm(messages, config)

    output_path.write_text(rewritten.strip(), encoding="utf-8")
    print(f"已保存到: {output_path}")
    print_summary(article, rewritten, args.platform)


if __name__ == "__main__":
    main()
