#!/usr/bin/env python3
"""GEO 改写脚本 v3.0 —— 调用 OpenAI 兼容 API，将普通文章优化为 AI 搜索引擎友好版本。

用法:
    # 单篇改写
    python3 geo_rewrite.py --input 文章.md --output 文章-geo.md

    # 批量改写（目录）
    python3 geo_rewrite.py --input-dir ./articles --output-dir ./geo-output

    # 批量改写（多文件）
    python3 geo_rewrite.py --input a.md b.md c.md --output-dir ./geo-output

    # 指定平台
    python3 geo_rewrite.py --input 文章.md --platform zhihu

    # 指定品牌实体（自动注入）
    python3 geo_rewrite.py --input 文章.md --brand "景一·寓言城堡"

    # 附带 GEO 评分卡
    python3 geo_rewrite.py --input 文章.md --score

    # JSON 结构化输出（供下游消费）
    python3 geo_rewrite.py --input 文章.md --json

    # 启用流式输出
    python3 geo_rewrite.py --input 文章.md --stream

    # 启用自动重试
    python3 geo_rewrite.py --input 文章.md --retry 3

    # 仅预览 prompt（不调用 API）
    python3 geo_rewrite.py --input 文章.md --dry-run

    # 输出对比统计
    python3 geo_rewrite.py --input 文章.md --stats
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════
# GEO 改写提示词（内嵌为字符串常量，不依赖外部文件）
# ═══════════════════════════════════════════════════

GEO_SYSTEM_PROMPT = """你是一名 GEO（Generative Engine Optimization，生成式引擎优化）内容优化专家。你的任务是接收一篇普通文章，将其改写为 AI 搜索引擎（如 ChatGPT Search、Perplexity、DeepSeek、豆包、Kimi）更愿意抓取、引用和推荐的版本。你精通五维改写规则：问答结构化、实体植入、引用锚点、结构化标记、平台适配。改写后的文章仍然是一篇人读得懂、读得舒服的文章，但机器会优先提取和推荐它。"""

GEO_REWRITE_INSTRUCTION = """
### 第一步：结构分析
阅读原文，识别核心问题、关键词、实体词。

### 第二步：GEO 改造（5 条规则）

规则 1 - 问答结构化：开头 150 字内直接回答核心问题。
规则 2 - 实体植入：{brand_rule}
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
{score_instruction}
最后输出改写后的 Markdown 正文。{extra_note}
"""

PLATFORM_RULES = {
    "zhihu": "知乎平台：开头用'先说结论'直接抛出答案，正文中间插入2-3个引导互动的话语，FAQ区块保留并扩展。标题含核心关键词，段落适中。",
    "wechat": "微信公众号平台：标题用对话感（'你体检报告上这个指标……'），每段不超过4行留白多，加粗关键词密度高（每段2-3处），文末加CTA引导关注。",
    "baijiahao": "百家号/头条号平台：标题含核心关键词2次以上，首段必须含关键词，每300字插入H3小标题，避免明显营销化表述。",
    "xiaohongshu": "小红书平台：开篇用emoji+一句话结论，全文不超过800字，短句+换行代替长段落，关键词用#话题标签穿插，结尾加互动提问。",
}

PLATFORM_RULE_DEFAULT = "通用平台：按照标准GEO五维规则改写，不做特定平台优化。适用于网页发布、通用文档等场景。"


# ═══════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════

@dataclass
class RewriteStats:
    """改写统计信息。"""
    file_name: str = ""
    platform: str = "通用"
    model: str = ""
    word_count_before: int = 0
    word_count_after: int = 0
    h2_count_before: int = 0
    h2_count_after: int = 0
    h3_count_before: int = 0
    h3_count_after: int = 0
    faq_count_before: int = 0
    faq_count_after: int = 0
    bold_count_before: int = 0
    bold_count_after: int = 0
    list_count_before: int = 0
    list_count_after: int = 0
    retries: int = 0
    duration_seconds: float = 0.0
    success: bool = False
    error: str = ""


# ═══════════════════════════════════════════════════
# 提示词构建
# ═══════════════════════════════════════════════════

def build_prompt(
    article: str, platform: Optional[str],
    brand: Optional[str] = None,
    with_score: bool = False,
    output_json: bool = False,
) -> list[dict]:
    """构建发送给 LLM 的消息列表。

    Args:
        article: 待改写文章内容
        platform: 目标平台（zhihu/wechat/baijiahao/xiaohongshu/None=通用）
        brand: 指定品牌实体名称，会自动注入改写指令
        with_score: True 时 LLM 会在输出末尾附带评分卡
        output_json: True 时 LLM 以 JSON 格式输出（含 body + score）
    """
    platform_rule = PLATFORM_RULES.get(platform, PLATFORM_RULE_DEFAULT) if platform else PLATFORM_RULE_DEFAULT

    if brand:
        brand_rule = (
            f'品牌实体「{brand}」在正文中出现 3 次以上，'
            f'每次搭配不同限定词形成差异化（如"{brand}的研究表明"、"根据{brand}的数据"、"{brand}专家建议"）。'
        )
    else:
        brand_rule = "品牌实体在正文中出现 3 次以上，加限定词形成差异化。"

    score_instruction = (
        "改写完成后务必在正文末尾附上完整的评分卡（含各项得分+总分）。" if with_score or output_json
        else "只输出正文，不要输出评分卡、不要加解释说明。"
    )
    extra_note = (
        "以 JSON 格式输出，结构为 {\"body\": \"...\", \"score\": {\"问答结构化\": N, \"实体植入\": N, \"引用锚点\": N, \"结构化标记\": N, \"平台适配\": N, \"可读性\": N, \"总分\": N}}。"
        if output_json
        else ""
    )

    instruction = GEO_REWRITE_INSTRUCTION.format(
        brand_rule=brand_rule,
        platform_rule=platform_rule,
        score_instruction=score_instruction,
        extra_note=extra_note,
    )
    user_message = f"请改写以下文章：\n\n{article}"

    return [
        {"role": "system", "content": GEO_SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
        {"role": "user", "content": user_message},
    ]


# ═══════════════════════════════════════════════════
# API 调用（支持重试与流式）
# ═══════════════════════════════════════════════════

def call_llm_normal(messages: list[dict], config: dict) -> str:
    """非流式调用 OpenAI 兼容 API。"""
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

    with urllib.request.build_opener(*handlers).open(req, timeout=config.get("timeout", 120)) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def call_llm_stream(messages: list[dict], config: dict):
    """流式调用 OpenAI 兼容 API，逐块 yield 文本。"""
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
        "stream": True,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []

    with urllib.request.build_opener(*handlers).open(req, timeout=config.get("timeout", 120)) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                try:
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


def call_llm_with_retry(messages: list[dict], config: dict) -> str:
    """带重试机制的 LLM 调用。"""
    max_retries = config.get("max_retries", 0)
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if config.get("stream"):
                chunks = []
                for chunk in call_llm_stream(messages, config):
                    chunks.append(chunk)
                    print(chunk, end="", flush=True)
                print()  # final newline
                return "".join(chunks)
            else:
                return call_llm_normal(messages, config)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** attempt  # 指数退避: 1s, 2s, 4s...
                print(f"\n  重试 {attempt + 1}/{max_retries}（{wait}s 后）...", file=sys.stderr)
                time.sleep(wait)
        except (KeyError, IndexError) as e:
            last_error = RuntimeError(f"API 返回格式异常: {e}")
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"\n  重试 {attempt + 1}/{max_retries}（{wait}s 后）...", file=sys.stderr)
                time.sleep(wait)

    if isinstance(last_error, urllib.error.HTTPError):
        body_text = last_error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API 请求失败 (HTTP {last_error.code}): {body_text}")
    elif isinstance(last_error, urllib.error.URLError):
        raise RuntimeError(f"网络错误: {last_error.reason}")
    raise last_error


# ═══════════════════════════════════════════════════
# 统计分析
# ═══════════════════════════════════════════════════

def count_structural_elements(text: str) -> dict:
    """统计文本中的结构化元素。"""
    import re
    return {
        "h2": len(re.findall(r'^##\s', text, re.MULTILINE)),
        "h3": len(re.findall(r'^###\s', text, re.MULTILINE)),
        "bold": len(re.findall(r'\*\*[^*]+\*\*', text)),
        "lists": len(re.findall(r'^\d+\.\s', text, re.MULTILINE)),
        "faq": text.lower().count("faq"),
    }


def compute_stats(
    original: str, rewritten: str, file_name: str,
    platform: str, model: str, retries: int, duration: float,
    success: bool, error: str = "",
) -> RewriteStats:
    """计算改写前后的对比统计。"""
    before = count_structural_elements(original)
    after = count_structural_elements(rewritten)
    return RewriteStats(
        file_name=file_name,
        platform=platform,
        model=model,
        word_count_before=len(original),
        word_count_after=len(rewritten),
        h2_count_before=before["h2"],
        h2_count_after=after["h2"],
        h3_count_before=before["h3"],
        h3_count_after=after["h3"],
        bold_count_before=before["bold"],
        bold_count_after=after["bold"],
        list_count_before=before["lists"],
        list_count_after=after["lists"],
        faq_count_before=before["faq"],
        faq_count_after=after["faq"],
        retries=retries,
        duration_seconds=duration,
        success=success,
        error=error,
    )


def print_statistics(all_stats: list[RewriteStats]):
    """打印批量改写统计报告。"""
    success_count = sum(1 for s in all_stats if s.success)
    fail_count = len(all_stats) - success_count

    print("\n" + "=" * 60)
    print("  GEO 批量改写统计报告")
    print("=" * 60)
    print(f"  总文件数: {len(all_stats)}  成功: {success_count}  失败: {fail_count}")
    print(f"  总耗时: {sum(s.duration_seconds for s in all_stats):.1f}s")
    print()

    if success_count > 0:
        # 汇总表
        print(f"  {'文件':<25} {'字数(前→后)':<16} {'H2':<8} {'加粗':<8} {'列表':<8} {'耗时':<8}")
        print("  " + "-" * 75)
        for s in all_stats:
            if s.success:
                name = s.file_name[:24]
                wc = f"{s.word_count_before}→{s.word_count_after}"
                h2 = f"{s.h2_count_before}→{s.h2_count_after}"
                bold = f"{s.bold_count_before}→{s.bold_count_after}"
                lst = f"{s.list_count_before}→{s.list_count_after}"
                dur = f"{s.duration_seconds:.1f}s"
                print(f"  {name:<25} {wc:<16} {h2:<8} {bold:<8} {lst:<8} {dur:<8}")
        print()

    if fail_count > 0:
        print(f"  失败列表:")
        for s in all_stats:
            if not s.success:
                print(f"    ✗ {s.file_name}: {s.error}")
        print()

    print("=" * 60)


# ═══════════════════════════════════════════════════
# 输出摘要
# ═══════════════════════════════════════════════════

def print_summary(original: str, rewritten: str, platform: Optional[str]):
    """打印改写摘要。"""
    platform_name = platform or "通用"
    word_before = len(original)
    word_after = len(rewritten)
    before = count_structural_elements(original)
    after = count_structural_elements(rewritten)

    print(f"""
══════════════  GEO 改写摘要  ══════════════
目标平台：{platform_name}
字数变化：{word_before} → {word_after}（{"+" if word_after >= word_before else ""}{word_after - word_before}）

结构变化：
  H2 标题：{before['h2']} → {after['h2']}
  H3 标题：{before['h3']} → {after['h3']}
  加粗关键词：{before['bold']} → {after['bold']}
  列表项：{before['lists']} → {after['lists']}
  FAQ 区块：{before['faq']} → {after['faq']}

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


# ═══════════════════════════════════════════════════
# 单篇改写流程
# ═══════════════════════════════════════════════════

def rewrite_single(
    input_path: Path, output_path: Path, platform: Optional[str],
    config: dict, dry_run: bool, show_stats: bool,
    brand: Optional[str] = None,
    with_score: bool = False,
    output_json: bool = False,
) -> Optional[RewriteStats]:
    """改写单篇文章，返回统计信息。"""
    article = input_path.read_text(encoding="utf-8")
    messages = build_prompt(article, platform, brand=brand, with_score=with_score, output_json=output_json)

    if dry_run:
        print(f"═══════ DRY RUN [{input_path.name}] ═══════\n")
        brand_label = f" (品牌: {brand})" if brand else ""
        score_label = " (含评分卡)" if with_score or output_json else ""
        json_label = " (JSON 输出)" if output_json else ""
        print(f"模式: {platform or '通用'}{brand_label}{score_label}{json_label}\n")
        for i, msg in enumerate(messages):
            print(f"[Message {i + 1}] Role: {msg['role']}")
            print(msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"])
            print("---\n")
        return None

    t0 = time.time()
    retries = 0
    success = True
    error = ""

    print(f"正在改写: {input_path.name} ", end="", flush=True)

    try:
        rewritten = call_llm_with_retry(messages, config)
    except Exception as e:
        rewritten = ""
        success = False
        error = str(e)
        print(f"\n✗ 失败: {error}", file=sys.stderr)

    duration = time.time() - t0

    if success:
        if output_json:
            # 尝试解析 JSON 响应，提取 body 作为正文写入 .md
            try:
                parsed = json.loads(rewritten)
                body = parsed.get("body", rewritten)
                score = parsed.get("score", {})
                # 写入纯正文 .md
                output_path.write_text(body.strip(), encoding="utf-8")
                # 同时写入 .json（完整结构化数据）
                json_path = output_path.with_suffix(".json")
                json.dump(parsed, json_path.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
                if show_stats:
                    summary = []
                    for k, v in score.items():
                        if k != "总分":
                            summary.append(f"  {k}: {v}/10")
                    summary.append(f"  总分: {score.get('总分', 'N/A')}/60")
                    print(f"\n评分卡:\n" + "\n".join(summary))
                print(f"\n已保存到: {output_path}  + {json_path}")
            except (json.JSONDecodeError, KeyError):
                output_path.write_text(rewritten.strip(), encoding="utf-8")
                print(f"\n已保存到: {output_path}（JSON 解析失败，已写入原始返回）")
        else:
            output_path.write_text(rewritten.strip(), encoding="utf-8")
            print(f"\n已保存到: {output_path}")

    if not dry_run and show_stats:
        stats = compute_stats(
            article, rewritten, input_path.name, platform or "通用",
            config["model"], retries, duration, success, error,
        )
        if success:
            print_summary(article, rewritten, platform)
        return stats

    if not dry_run:
        print_summary(article, rewritten, platform)

    return compute_stats(
        article, rewritten, input_path.name, platform or "通用",
        config["model"], retries, duration, success, error,
    )


# ═══════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="GEO 改写 v3.0 —— 将普通文章优化为 AI 搜索引擎友好版本",
        epilog="示例: python3 geo_rewrite.py --input 文章.md --output 文章-geo.md --brand '景一·寓言城堡'",
    )

    # 输入源（三选一）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", nargs="+", help="输入文章路径（支持多个 .md 文件）")
    input_group.add_argument("--input-dir", help="输入目录（递归处理所有 .md/.txt 文件）")

    # 输出
    parser.add_argument("--output", default=None, help="输出路径（单文件时可用，默认: 原名-geo.md）")
    parser.add_argument("--output-dir", default=None, help="输出目录（批量时使用，默认: 与输入同目录）")

    # 平台
    parser.add_argument("--platform", choices=["zhihu", "wechat", "baijiahao", "xiaohongshu"],
                        default=None, help="目标平台")

    # 品牌实体
    parser.add_argument("--brand", default=None, help="指定品牌实体名称，自动注入正文（如 '景一·寓言城堡'）")

    # 评分卡
    parser.add_argument("--score", action="store_true", help="输出附带 GEO 六维评分卡")

    # JSON 输出
    parser.add_argument("--json", action="store_true", help="JSON 结构化输出（含 body + score），同时写入 .md 和 .json")

    # 新功能 flag
    parser.add_argument("--stream", action="store_true", help="启用流式输出（边生成边显示）")
    parser.add_argument("--retry", type=int, default=0, help="API 调用失败时自动重试次数")
    parser.add_argument("--stats", action="store_true", help="输出对比统计报告")
    parser.add_argument("--dry-run", action="store_true", help="只打印构建的 prompt，不调用 API")

    args = parser.parse_args()

    # 收集输入文件
    input_files: list[Path] = []
    if args.input:
        for p in args.input:
            path = Path(p)
            if not path.is_file():
                sys.exit(f"错误: 找不到文件 {p}")
            input_files.append(path)
    elif args.input_dir:
        input_dir = Path(args.input_dir)
        if not input_dir.is_dir():
            sys.exit(f"错误: 找不到目录 {args.input_dir}")
        input_files = sorted(input_dir.rglob("*.md")) + sorted(input_dir.rglob("*.txt"))
        if not input_files:
            sys.exit(f"错误: 目录 {args.input_dir} 中没有 .md 或 .txt 文件")

    # 确定输出目录
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # 单文件 + 指定 output 路径的特殊处理
    if len(input_files) == 1 and args.output and not output_dir:
        output_path = Path(args.output)
    else:
        output_path = None

    # API 配置
    if not args.dry_run:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            sys.exit("错误: 未设置 OPENAI_API_KEY 环境变量")
        config = {
            "api_key": api_key,
            "api_base": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            "stream": args.stream,
            "max_retries": args.retry,
            "timeout": 180,
        }
    else:
        config = {}

    all_stats: list[RewriteStats] = []

    for i, input_path in enumerate(input_files):
        if len(input_files) > 1:
            print(f"\n[{i + 1}/{len(input_files)}] ", end="")

        # 确定输出路径
        if output_path and len(input_files) == 1:
            out = output_path
        elif output_dir:
            out = output_dir / f"{input_path.stem}-geo{input_path.suffix}"
        else:
            out = input_path.with_stem(f"{input_path.stem}-geo")

        stats = rewrite_single(
            input_path, out, args.platform, config, args.dry_run, args.stats,
            brand=args.brand,
            with_score=args.score,
            output_json=args.json,
        )
        if stats:
            all_stats.append(stats)

    # 打印批量统计
    if args.stats and len(all_stats) > 1:
        print_statistics(all_stats)

    if not args.dry_run and not args.stats and len(all_stats) == 0 and len(input_files) > 0:
        # dry-run 不出统计
        pass


if __name__ == "__main__":
    main()
