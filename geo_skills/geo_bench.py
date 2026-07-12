#!/usr/bin/env python3
"""
GEO Skills 性能压测 — 模拟真实管线负载，测量吞吐量/延迟/内存

纯 Python 标准库，不依赖任何第三方包。

用法：
  python3 geo_bench.py --count 100 --mode dry
  python3 geo_bench.py --count 50 --mode mock
  python3 geo_bench.py --count 20 --mode real
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 20 Chinese content templates ----
_TEMPLATES = [
    "随着人工智能技术的快速发展，{领域}正在经历一场前所未有的变革。从最初的规则引擎到如今的深度学习模型，AI已经渗透到我们生活的方方面面。",
    "在过去五年中，{领域}的增长率超过了200%，这一数字远超市场预期。专家认为，这主要得益于三大因素的共同推动：政策支持、技术进步和市场需求。",
    "很多人问我：{问题}？这个问题看似简单，但答案却涉及多个层面的分析。首先我们需要理解{概念}的基本原理，然后才能做出合理判断。",
    "根据最新发布的《{年份}年{报告名}》显示，中国{领域}市场规模已达到{数字}亿元，同比增长{增长率}%。这份报告还指出了几个值得关注的趋势。",
    "从用户体验的角度来看，{产品}最大的优势在于其简洁的界面设计和流畅的操作体验。相比之下，同类竞品在{方面}仍然存在明显短板。",
    "对于初学者来说，学习{技能}最好的方法是从实际项目入手。我建议先掌握{基础概念}，然后逐步深入到{进阶概念}。切忌贪多嚼不烂。",
    "最近一篇发表在《{期刊}》上的论文引起了广泛关注。研究者通过{方法}对{对象}进行了为期{时间}的跟踪研究，得出了令人惊讶的结论。",
    "在实际工作中，我经常遇到这样的情况：明明{方案A}看起来更优，但最终{方案B}却取得了更好的效果。这背后的原因在于{解释}。",
    "食品安全一直是公众关注的焦点。{食品名}作为一种常见食材，其营养价值和潜在风险都需要我们理性看待。适量食用对健康有益，但过量则可能带来隐患。",
    "数字化转型不是简单的技术升级，而是企业战略层面的系统性变革。成功的关键在于{关键因素}，而失败往往源于{失败原因}。",
    "在面试中，当被问到「{面试题}」时，很多候选人都会紧张。其实面试官真正想考察的是你的{能力}，而不是标准答案本身。",
    "健康管理是一个系统工程，不能头痛医头、脚痛医脚。{疾病}的预防需要从饮食、运动、作息、心理四个维度同时入手。",
    "创业者的第一课：不要过早追求完美。MVP（最小可行产品）的核心思想是{核心理念}。先验证需求，再打磨产品。",
    "在投资理财中，有一个经典的{投资策略}策略非常值得普通人学习。它的核心操作是{操作方式}，长期坚持下来的年化收益稳定在{收益率}左右。",
    "写作能力的提升没有捷径，但有一些方法可以加速这个过程。第一，每天坚持{习惯}；第二，建立{体系}；第三，主动寻求反馈并及时修正。",
    "在选择{产品类型}时，很多人只关注价格，却忽略了更重要的因素：{因素1}、{因素2}和{因素3}。这些隐性成本往往比价格差异大得多。",
    "团队管理中最难的环节不是制定战略，而是执行落地。我实践过的最有效方法是{方法名}，它通过{步骤}三个步骤确保每项任务都能追踪到底。",
    "Python 作为一门简洁优雅的编程语言，在{领域}有着广泛的应用。相比 Java 和 C++，Python 最大的优势在于{优势}。",
    "关于{话题}，网上流传着很多说法，但其中不少是误解。今天我们就来逐一澄清：误解一{误解1}；误解二{误解2}；误解三{误解3}。",
    "未来三年，{行业}将迎来三大趋势：{趋势1}、{趋势2}和{趋势3}。提前布局的企业将在竞争中占据先机。",
]

_PARAMS = {
    "领域": ["医疗健康", "金融科技", "在线教育", "新能源汽车", "人工智能", "跨境电商", "生物制药", "智能制造", "数字营销", "新能源"],
    "问题": ["AI真的会取代人类工作吗", "远程办公能提升效率吗", "预制菜安全吗", "冥想真的有效吗", "需要每天喝8杯水吗"],
    "概念": ["机器学习", "区块链", "碳中和", "复利效应", "边际成本", "协同效应", "飞轮效应", "长尾理论", "熵增定律", "第一性原理"],
    "年份": ["2023", "2024", "2025", "2026"],
    "报告名": ["中国互联网发展报告", "人工智能产业白皮书", "数字经济研究报告", "消费者行为洞察", "全球科技创新指数"],
    "数字": ["3.2", "15.8", "128", "470", "2.1", "89", "5600", "1.7", "24.5", "330"],
    "增长率": ["18.5", "32.1", "45.8", "12.3", "27.6", "9.8", "51.2", "63.4"],
    "产品": ["Notion", "飞书", "Obsidian", "ChatGPT", "Figma"],
    "方面": ["协作能力", "搜索功能", "插件生态", "离线支持", "价格策略"],
    "技能": ["Python编程", "数据分析", "UI设计", "项目管理", "内容创作"],
    "基础概念": ["变量和循环", "数据透视表", "设计原则", "WBS分解", "选题策略"],
    "进阶概念": ["装饰器和生成器", "机器学习算法", "设计系统", "关键路径法", "SEO方法论"],
    "期刊": ["Nature", "Science", "The Lancet", "Cell", "NEJM"],
    "方法": ["随机对照实验", "元分析", "队列研究", "系统综述", "A/B测试"],
    "对象": ["5000名志愿者", "200家企业", "全国30个城市", "三个年级学生", "100种植物"],
    "时间": ["三年", "18个月", "五年", "两个学期", "两年半"],
    "方案A": ["激进策略", "自研方案", "集中管理", "垂直整合", "先发制人"],
    "方案B": ["稳健策略", "外包方案", "去中心化", "横向合作", "后发制人"],
    "解释": ["短期成本与长期收益的错配", "市场窗口期的动态变化", "团队执行力差异", "用户习惯迁移成本"],
    "食品名": ["牛奶", "鸡蛋", "三文鱼", "蓝莓", "西兰花", "坚果", "酸奶", "燕麦"],
    "关键因素": ["一把手亲自推动", "数据治理先行", "组织架构匹配", "人才梯队建设"],
    "失败原因": ["目标不清", "技术选型失误", "员工抵触", "投入不足"],
    "面试题": ["你的最大缺点是什么", "为什么从上家公司离职", "如何处理团队冲突", "对未来五年的规划"],
    "能力": ["结构化思维能力", "抗压和适应能力", "跨部门沟通能力", "数据驱动决策能力"],
    "疾病": ["高血压", "糖尿病", "脂肪肝", "颈椎病", "焦虑症"],
    "核心理念": ["用最小的代价验证最关键的不确定性", "先做减法再做加法", "找到愿意付费的10个用户"],
    "投资策略": ["定投", "网格交易", "股债平衡", "价值平均", "全天候"],
    "操作方式": ["每月固定日期投入固定金额，无论涨跌",
               "设定价格区间，自动低买高卖",
               "根据市场波动动态调整股债比例"],
    "收益率": ["8%", "12%", "15%", "10%", "7%"],
    "习惯": ["写500字", "阅读一篇长文", "复盘工作日志", "录制一条语音笔记"],
    "体系": ["知识管理系统", "素材分类库", "定期写作计划", "反馈循环机制"],
    "产品类型": ["笔记本电脑", "手机", "投影仪", "空气净化器", "保险"],
    "因素1": ["售后服务质量", "生态兼容性", "长期使用成本", "数据隐私保护"],
    "因素2": ["能耗", "配件价格", "软件更新周期", "二手残值"],
    "因素3": ["使用场景匹配度", "扩展性", "维修便利性", "品牌口碑"],
    "方法名": ["OKR工作法", "PDCA循环", "GTD方法", "Scrum敏捷"],
    "步骤": ["目标设定、关键结果定义、每周复盘", "计划、执行、检查、改进", "收集、整理、执行、回顾"],
    "行业": ["半导体", "元宇宙", "储能", "合成生物学", "卫星互联网"],
    "趋势1": ["AI+垂直行业深度融合", "分布式能源普及", "基因编辑技术突破", "低轨卫星星座组网"],
    "趋势2": ["数据资产化加速", "供应链区域化重构", "人才市场两极分化", "监管框架逐步完善"],
    "趋势3": ["跨界融合创新", "绿色低碳转型", "个性化定制规模化", "数字孪生全面落地"],
    "话题": ["冥想", "轻断食", "冷萃咖啡", "早睡早起", "正念饮食"],
    "误解1": ["必须盘腿打坐才有用", "等于绝食", "比热咖啡更健康", "睡得越早越好", "就是只吃素"],
    "误解2": ["一学就会", "适合所有人", "自己在家就能做好", "周末补觉就行", "不能吃任何碳水"],
    "误解3": ["需要特殊天赋", "会让代谢变慢", "必须买专业设备", "老年人不适合", "影响社交生活"],
}


def _fill(template):
    """Fill a template by replacing {key} with random values."""
    import re
    result = template
    placeholders = re.findall(r'\{(\w+)\}', template)
    for key in placeholders:
        if key in _PARAMS:
            result = result.replace(f"{{{key}}}", random.choice(_PARAMS[key]), 1)
    return result


def generate_mock(n, output_dir):
    """Generate n mock Chinese articles."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i in range(n):
        # Randomly select 4-7 templates
        k = random.randint(4, 7)
        selected = random.sample(_TEMPLATES, k)
        paragraphs = []
        for t in selected:
            paragraphs.append(_fill(t))

        # Add a title
        title_templates = [
            "深度解析：{topic}的现状与未来",
            "{topic}完全指南：从入门到精通",
            "为什么你应该关注{topic}？",
            "{topic}终极科普：你需要知道的一切",
            "关于{topic}，这5个真相你必须了解",
        ]
        topic = random.choice(["AI写作", "远程办公", "个人成长", "投资理财",
                               "健康生活", "技术趋势", "创业方法论", "团队管理"])
        title = random.choice(title_templates).replace("{topic}", topic)

        article = f"# {title}\n\n" + "\n\n".join(paragraphs) + "\n"

        path = os.path.join(output_dir, f"mock_{i:04d}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(article)
        paths.append(path)

    return paths


def run_phase(phase_name, cmd, timeout=120):
    """Run a phase and return elapsed time."""
    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.perf_counter() - start
        ok = result.returncode == 0
        if not ok:
            stderr_short = result.stderr[:200] if result.stderr else ""
            print(f"  [{phase_name}] FAILED: {stderr_short}")
        return elapsed, ok
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        print(f"  [{phase_name}] TIMEOUT after {timeout}s")
        return elapsed, False
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"  [{phase_name}] ERROR: {e}")
        return elapsed, False


def bar_chart(data, max_width=40):
    """Generate ASCII bar chart from list of (name, value) pairs."""
    if not data:
        return ""

    max_val = max(v for _, v in data)
    if max_val == 0:
        max_val = 1

    lines = []
    max_name_len = max(len(n) for n, _ in data)
    for name, value in data:
        bar_len = int(value / max_val * max_width)
        bar = "█" * bar_len
        lines.append(f"  {name:<{max_name_len}} │ {bar} {value:.2f}s")

    return "\n".join(lines)


def cmd_mock(args):
    """Generate mock files only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        start = time.perf_counter()
        paths = generate_mock(args.count, tmpdir)
        elapsed = time.perf_counter() - start
        total_chars = sum(os.path.getsize(p) for p in paths)
        print(f"生成 {len(paths)} 篇 mock 文章")
        print(f"  总字符: {total_chars:,}")
        print(f"  平均:   {total_chars // len(paths):,} 字符/篇")
        print(f"  耗时:   {elapsed:.3f}s")
        print(f"  吞吐:   {len(paths) / elapsed:.1f} 篇/s")


def cmd_dry(args):
    """Dry-run benchmark: simulate 4-stage pipeline elapsed time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"生成 {args.count} 篇 mock 文章...")
        t0 = time.perf_counter()
        paths = generate_mock(args.count, tmpdir)
        t_gen = time.perf_counter() - t0
        total_chars = sum(os.path.getsize(p) for p in paths)
        print(f"  生成耗时: {t_gen:.3f}s ({args.count / t_gen:.1f} 篇/s)")

        outdir = os.path.join(tmpdir, "output")
        os.makedirs(outdir, exist_ok=True)

        # Simulate 4 phases
        phases = [
            ("关键词扩展", 0.15),
            ("GEO 改写", 0.50),
            ("内容审计", 0.25),
            ("报告生成", 0.10),
        ]

        results = []
        total_elapsed = 0.0
        for phase_name, weight in phases:
            # Simulate processing proportional to count
            sim_time = args.count * weight * 0.01
            time.sleep(min(sim_time, 0.5))  # cap sleep
            results.append((phase_name, sim_time))
            total_elapsed += sim_time

        print(f"\n压测结果 (mode=dry, n={args.count})")
        print(f"{'='*60}")
        print(f"  总文章数:   {args.count}")
        print(f"  总字符数:   {total_chars:,}")
        print(f"  总耗时:     {total_elapsed:.2f}s")
        print(f"  吞吐量:     {args.count / total_elapsed:.1f} 篇/s")
        print()
        print("  各阶段耗时分布:")
        print(bar_chart(results))
        print()

        # Scale estimates
        for scale in [100, 500, 1000, 5000]:
            est = scale * total_elapsed / args.count
            rate = scale / est if est > 0 else 0
            unit = "s"
            if est >= 60:
                est /= 60
                unit = "min"
            print(f"  预估 ×{scale:>5}: {est:.1f}{unit} (if linear)  → {rate:.0f} 篇/s")


def cmd_real(args):
    """Real benchmark: run geo_flow.py on mock files."""
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("[SKIP] 未设置 OPENAI_API_KEY，无法执行真实压测")
        print("  请先设置: export OPENAI_API_KEY=sk-xxx")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"生成 {args.count} 篇 mock 文章...")
        t0 = time.perf_counter()
        paths = generate_mock(args.count, tmpdir)
        t_gen = time.perf_counter() - t0
        print(f"  生成耗时: {t_gen:.3f}s")

        outdir = os.path.join(tmpdir, "output")
        os.makedirs(outdir, exist_ok=True)

        # pick a subset for real API (avoid massive cost)
        real_count = min(args.count, args.real_limit or 5)
        print(f"\n真实执行 geo_flow.py (取 {real_count} 篇样本)...")

        tracemalloc.start()
        flow_script = os.path.join(SCRIPT_DIR, "geo_flow.py")

        results = []
        for i in range(real_count):
            cmd = [
                sys.executable, flow_script,
                "--mode", "single",
                "--input", paths[i],
                "--output-dir", outdir,
                "--dry-run",
            ]
            elapsed, ok = run_phase(f"Article {i+1}", cmd, timeout=60)
            results.append((f"article_{i:03d}", elapsed, ok))

        total_elapsed = sum(e for _, e, _ in results)
        success_count = sum(1 for _, _, ok in results if ok)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n压测结果 (mode=real, n={real_count})")
        print(f"{'='*60}")
        print(f"  处理篇数:   {real_count}")
        print(f"  成功:       {success_count}/{real_count}")
        print(f"  总耗时:     {total_elapsed:.2f}s")
        print(f"  平均每篇:   {total_elapsed / real_count:.3f}s" if real_count else "")
        print(f"  吞吐量:     {real_count / total_elapsed:.1f} 篇/s" if total_elapsed > 0 else "")
        print(f"  内存峰值:   {peak / 1024 / 1024:.1f} MB")
        print()
        print("  各篇耗时:")
        for name, elapsed, ok in results:
            status = "OK" if ok else "FAIL"
            bar_len = int(elapsed / max(e for _, e, _ in results) * 30) if results else 0
            print(f"  {name} │ {'█' * bar_len} {elapsed:.2f}s [{status}]")


def main():
    parser = argparse.ArgumentParser(
        description="GEO Skills 性能压测 — 模拟真实管线负载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --count 100 --mode mock     # 只生成 mock 文章
  %(prog)s --count 100 --mode dry      # 模拟调度耗时
  %(prog)s --count 20 --mode real      # 真实管线压测
        """,
    )

    parser.add_argument("--count", type=int, default=100, help="测试文章数量 (默认 100)")
    parser.add_argument("--mode", default="dry",
                        choices=["mock", "dry", "real"],
                        help="压测模式: mock=仅生成, dry=模拟调度, real=真实管线 (默认 dry)")
    parser.add_argument("--real-limit", type=int, default=5,
                        help="real 模式最多执行篇数 (默认 5，避免大量 API 调用)")

    args = parser.parse_args()

    if args.mode == "mock":
        cmd_mock(args)
    elif args.mode == "dry":
        cmd_dry(args)
    elif args.mode == "real":
        cmd_real(args)


if __name__ == "__main__":
    main()
