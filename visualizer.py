#!/usr/bin/env python3
"""
GEO 可视化报告生成器 — 并排对比 + 统计 + 雷达图 + 五维改动说明

纯 Python 标准库，输出自包含 HTML 文件（深色主题 / 响应式 / 打印友好）。

用法：
  python3 visualizer.py --input-before article.md --input-after article-geo.md
  python3 visualizer.py --input-before article.md --input-after article-geo.md --output report.html
"""

import argparse
import os
import sys


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GEO 改写对比报告</title>
<style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background: #0f1117; color: #e4e6eb; line-height: 1.7;
        max-width: 1440px; margin: 0 auto; padding: 24px;
    }}
    h1 {{ text-align: center; font-size: 1.8rem; margin-bottom: 8px; color: #e2e8f0; }}
    .subtitle {{ text-align: center; color: #8892b0; margin-bottom: 32px; font-size: 0.9rem; }}

    /* Stats Bar */
    .stats-bar {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px; margin-bottom: 40px;
    }}
    .stat-card {{
        background: #1a1d2e; border-radius: 12px; padding: 20px;
        border: 1px solid #2d3148; text-align: center;
    }}
    .stat-label {{ font-size: 0.8rem; color: #8892b0; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }}
    .stat-values {{ display: flex; justify-content: center; gap: 12px; align-items: baseline; }}
    .stat-before {{ font-size: 1.6rem; color: #64748b; }}
    .stat-after {{ font-size: 1.6rem; color: #38bdf8; }}
    .stat-delta {{ font-size: 0.9rem; }}
    .stat-delta.pos {{ color: #4ade80; }}
    .stat-delta.neg {{ color: #f87171; }}
    .stat-delta.zero {{ color: #8892b0; }}
    .stat-arrow {{ color: #475569; font-size: 1.2rem; }}

    /* Side-by-side */
    .comparison-container {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px; margin-bottom: 40px;
    }}
    @media (max-width: 768px) {{
        .comparison-container {{ grid-template-columns: 1fr; }}
    }}
    .comparison-pane {{
        background: #1a1d2e; border-radius: 12px;
        border: 1px solid #2d3148; overflow: hidden;
    }}
    .pane-header {{
        padding: 16px 20px; font-weight: 600;
        font-size: 0.95rem; border-bottom: 1px solid #2d3148;
    }}
    .pane-header.before {{ background: #2d1f1f; color: #fca5a5; }}
    .pane-header.after {{ background: #1a2e22; color: #86efac; }}
    .pane-content {{ padding: 20px; font-size: 0.92rem; white-space: pre-wrap; word-break: break-word; }}
    .pane-content h1, .pane-content h2, .pane-content h3, .pane-content h4 {{
        margin: 1em 0 0.4em; color: #e2e8f0;
    }}
    .pane-content h2 {{ font-size: 1.2rem; border-bottom: 1px solid #2d3148; padding-bottom: 6px; }}
    .pane-content h3 {{ font-size: 1.05rem; }}
    .pane-content p {{ margin-bottom: 0.8em; }}
    .pane-content ul, .pane-content ol {{ margin: 0.5em 0 0.8em 1.5em; }}
    .pane-content strong, .pane-content b {{ color: #facc15; }}
    .pane-content blockquote {{
        border-left: 3px solid #475569; padding-left: 16px;
        color: #94a3b8; margin: 0.8em 0;
    }}

    /* Radar Chart */
    .radar-section {{
        background: #1a1d2e; border-radius: 12px;
        border: 1px solid #2d3148; padding: 32px; margin-bottom: 40px;
    }}
    .radar-section h2 {{ text-align: center; margin-bottom: 24px; color: #e2e8f0; }}
    .radar-container {{
        display: flex; justify-content: center;
        flex-wrap: wrap; gap: 40px;
    }}
    .radar-chart {{
        position: relative; width: 350px; height: 350px;
    }}
    .radar-legend {{
        display: flex; flex-direction: column; gap: 10px;
        align-self: center;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; }}
    .legend-color {{
        width: 14px; height: 14px; border-radius: 3px;
    }}

    /* Changes */
    .changes-section {{ margin-bottom: 40px; }}
    .changes-section h2 {{ color: #e2e8f0; margin-bottom: 20px; text-align: center; }}
    .change-card {{
        background: #1a1d2e; border-radius: 12px;
        border: 1px solid #2d3148; padding: 20px; margin-bottom: 16px;
    }}
    .change-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
    .change-header .icon {{ font-size: 1.3rem; }}
    .change-header h3 {{ color: #e2e8f0; font-size: 1rem; }}
    .change-body {{ color: #94a3b8; font-size: 0.92rem; line-height: 1.7; }}
    .change-body ul {{ margin: 0.5em 0 0 1.5em; }}

    /* Footer */
    .footer {{
        text-align: center; color: #475569;
        font-size: 0.8rem; padding: 24px 0;
        border-top: 1px solid #2d3148; margin-top: 40px;
    }}

    @media print {{
        body {{ background: #fff; color: #1a1a2e; }}
        .stat-card, .comparison-pane, .radar-section, .change-card {{
            background: #f8f9fa; border-color: #dee2e6;
        }}
    }}
</style>
</head>
<body>

<h1>GEO 改写对比报告</h1>
<p class="subtitle">改写前 vs 改写后 — {article_name}</p>

<!-- Stats Bar -->
<div class="stats-bar">
    <div class="stat-card">
        <div class="stat-label">总字数</div>
        <div class="stat-values">
            <span class="stat-before">{before_chars}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_chars}</span>
        </div>
        <div class="stat-delta {chars_delta_class}">{chars_delta}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">H2 标题</div>
        <div class="stat-values">
            <span class="stat-before">{before_h2}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_h2}</span>
        </div>
        <div class="stat-delta {h2_delta_class}">{h2_delta}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">H3 标题</div>
        <div class="stat-values">
            <span class="stat-before">{before_h3}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_h3}</span>
        </div>
        <div class="stat-delta {h3_delta_class}">{h3_delta}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">加粗数量</div>
        <div class="stat-values">
            <span class="stat-before">{before_bold}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_bold}</span>
        </div>
        <div class="stat-delta {bold_delta_class}">{bold_delta}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">列表项</div>
        <div class="stat-values">
            <span class="stat-before">{before_lists}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_lists}</span>
        </div>
        <div class="stat-delta {lists_delta_class}">{lists_delta}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">FAQ 数</div>
        <div class="stat-values">
            <span class="stat-before">{before_faq}</span>
            <span class="stat-arrow">→</span>
            <span class="stat-after">{after_faq}</span>
        </div>
        <div class="stat-delta {faq_delta_class}">{faq_delta}</div>
    </div>
</div>

<!-- Radar Chart -->
<div class="radar-section">
    <h2>六维 GEO 评分对比</h2>
    <div class="radar-container">
        <div class="radar-chart">
            {radar_svg}
        </div>
    </div>
</div>

<!-- Changes -->
<div class="changes-section">
    <h2>五维 GEO 改动说明</h2>

    <div class="change-card">
        <div class="change-header">
            <span class="icon">✅</span>
            <h3>1. 问答结构化</h3>
        </div>
        <div class="change-body">
            <p>改写后文章按问答形式组织，核心问题有明确的标题和结构化回答。利于 AI 搜索引擎抽取问答对作为直接引用。</p>
            <ul>
                <li>FAQ 数量从 {before_faq} 增加到 {after_faq}</li>
                <li>H2 标题从 {before_h2} 增加到 {after_h2}，整体结构更清晰</li>
            </ul>
        </div>
    </div>

    <div class="change-card">
        <div class="change-header">
            <span class="icon">✅</span>
            <h3>2. 实体植入</h3>
        </div>
        <div class="change-body">
            <p>在正文中自然植入品牌实体 "{brand}"，出现在标题/开头/中段至少 3 个位置，提升实体密度和 AI 引用概率。</p>
        </div>
    </div>

    <div class="change-card">
        <div class="change-header">
            <span class="icon">✅</span>
            <h3>3. 引用锚点</h3>
        </div>
        <div class="change-body">
            <p>增加数据引用、权威来源和具体案例，让 AI 搜索引擎在回答时倾向于引用本文作为来源。</p>
            <ul>
                <li>加入具体数据和统计数字增强可信度</li>
                <li>必要时引用权威机构或研究报告</li>
            </ul>
        </div>
    </div>

    <div class="change-card">
        <div class="change-header">
            <span class="icon">✅</span>
            <h3>4. 结构化标记</h3>
        </div>
        <div class="change-body">
            <p>增加 H2/H3 标题、加粗重点、列表和引用块等语义标记，便于 AI 搜索引擎解析和提取结构。</p>
            <ul>
                <li>加粗数量从 {before_bold} 增加到 {after_bold}</li>
                <li>列表项从 {before_lists} 增加到 {after_lists}</li>
            </ul>
        </div>
    </div>

    <div class="change-card">
        <div class="change-header">
            <span class="icon">{platform_icon}</span>
            <h3>5. 平台适配 — {platform_name}</h3>
        </div>
        <div class="change-body">
            <p>针对 {platform_name} 平台的读者习惯和算法偏好进行了格式和语气的适配。</p>
        </div>
    </div>
</div>

<!-- Side-by-side -->
<h2 style="text-align:center;color:#e2e8f0;margin-bottom:16px;">并排对比</h2>
<div class="comparison-container">
    <div class="comparison-pane">
        <div class="pane-header before">改写前</div>
        <div class="pane-content">{before_content}</div>
    </div>
    <div class="comparison-pane">
        <div class="pane-header after">改写后</div>
        <div class="pane-content">{after_content}</div>
    </div>
</div>

<div class="footer">
    Generated by geo-skills · GEO Visualizer v1.0.0
</div>

</body>
</html>"""


def count_stats(content):
    """统计文章的各项指标"""
    lines = content.split("\n")
    return {
        "chars": len(content),
        "h2": sum(1 for l in lines if l.startswith("## ")),
        "h3": sum(1 for l in lines if l.startswith("### ")),
        "bold": content.count("**"),
        "lists": sum(1 for l in lines if l.strip().startswith("- ") or l.strip().startswith("* ")),
        "faq": content.count("？") + content.count("?") + content.count("Q:") + content.count("Q："),
    }


def delta_str(before, after):
    """格式化的差值字符串"""
    d = after - before
    if d > 0:
        return f"+{d}"
    elif d < 0:
        return str(d)
    return "0"


def delta_class(before, after):
    if after > before:
        return "pos"
    elif after < before:
        return "neg"
    return "zero"


def escape_html(text):
    """Basic HTML escaping for content display."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def basic_markdown_to_html(text):
    """Minimal markdown-to-HTML for side-by-side panes.

    Handles: headings, bold, italic, lists, blockquotes, paragraphs.
    Does NOT use any external libraries.
    """
    lines = text.split("\n")
    output = []
    in_list = False
    in_ordered = False

    for line in lines:
        stripped = line.strip()

        # Horizontal rule
        if stripped.startswith("---") or stripped.startswith("***"):
            if in_list:
                output.append("</ul>" if not in_ordered else "</ol>")
                in_list = False
                in_ordered = False
            output.append("<hr>")
            continue

        # Headings
        if stripped.startswith("#### "):
            output.append(f"<h4>{escape_html(stripped[5:])}</h4>")
            continue
        if stripped.startswith("### "):
            output.append(f"<h3>{escape_html(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            output.append(f"<h2>{escape_html(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            output.append(f"<h1>{escape_html(stripped[2:])}</h1>")
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list or in_ordered:
                if in_ordered:
                    output.append("</ol>")
                    in_ordered = False
                output.append("<ul>")
                in_list = True
            content = stripped[2:]
            # Simple inline formatting
            content = content.replace("**", "<strong>").replace("__", "<em>")
            # Count ** for toggle
            while "**" in content:
                content = content.replace("**", "<strong>", 1)
                content = content.replace("**", "</strong>", 1)
            while "__" in content:
                content = content.replace("__", "<em>", 1)
                content = content.replace("__", "</em>", 1)
            output.append(f"<li>{content}</li>")
            continue

        # Ordered list
        if stripped and (stripped[0].isdigit() and ". " in stripped[:5]):
            if not in_ordered or in_list:
                if in_list:
                    output.append("</ul>")
                    in_list = False
                output.append("<ol>")
                in_ordered = True
            content = stripped[stripped.index(".") + 2:]
            while "**" in content:
                content = content.replace("**", "<strong>", 1)
                content = content.replace("**", "</strong>", 1)
            output.append(f"<li>{content}</li>")
            continue

        # Close lists on non-list line
        if in_list:
            output.append("</ul>")
            in_list = False
        if in_ordered:
            output.append("</ol>")
            in_ordered = False

        # Blockquote
        if stripped.startswith("> "):
            output.append(f"<blockquote>{escape_html(stripped[2:])}</blockquote>")
            continue

        # Paragraph
        if not stripped:
            output.append("")
        else:
            content = escape_html(stripped)
            # Bold
            while "**" in content:
                content = content.replace("**", "<strong>", 1)
                content = content.replace("**", "</strong>", 1)
            # Italic
            while "*" in content:
                # Simple: only handle single * around words
                idx = content.find("*")
                if idx == -1:
                    break
                next_idx = content.find("*", idx + 1)
                if next_idx == -1:
                    break
                content = content[:idx] + "<em>" + content[idx+1:next_idx] + "</em>" + content[next_idx+1:]
            output.append(f"<p>{content}</p>")

    # Close open lists
    if in_list:
        output.append("</ul>")
    if in_ordered:
        output.append("</ol>")

    return "\n".join(output)


def generate_radar_svg(scores_before, scores_after):
    """
    Generate SVG radar chart comparing two sets of six-dimensional scores.

    scores_before: dict of 6 dimensions → value (0-10)
    scores_after: dict of 6 dimensions → value (0-10)
    """
    dimensions = list(scores_before.keys())
    n = len(dimensions)  # 6

    width, height = 350, 350
    cx, cy = width // 2, height // 2
    radius = 140

    import math

    parts = []

    # SVG header
    parts.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')

    # Background grid (5 concentric polygons)
    for level in range(1, 6):
        r = radius * level / 5
        points = []
        for i in range(n):
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        poly = " ".join(points)
        parts.append(f'<polygon points="{poly}" fill="none" stroke="#2d3148" stroke-width="1"/>')

    # Axis lines
    for i in range(n):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#2d3148" stroke-width="1"/>')

    # Labels
    for i, dim in enumerate(dimensions):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        lx = cx + (radius + 24) * math.cos(angle)
        ly = cy + (radius + 24) * math.sin(angle)
        anchor = "middle"
        if angle < -0.1:
            anchor = "end"
        elif angle > 0.1:
            anchor = "start"
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                     f'fill="#8892b0" font-size="12" dominant-baseline="middle">{dim}</text>')

    # Helper to build polygon
    def build_polygon(scores, color, opacity):
        points = []
        for i, dim in enumerate(dimensions):
            v = scores.get(dim, 0) / 10.0
            r = radius * v
            angle = -math.pi / 2 + 2 * math.pi * i / n
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        poly = " ".join(points)
        return f'<polygon points="{poly}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-width="2"/>'

    parts.append(build_polygon(scores_after, "#38bdf8", "0.3"))
    parts.append(build_polygon(scores_before, "#fca5a5", "0.25"))

    # Dots for after
    for i, dim in enumerate(dimensions):
        v = scores_after.get(dim, 0) / 10.0
        r = radius * v
        angle = -math.pi / 2 + 2 * math.pi * i / n
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#38bdf8"/>')

    # Dots for before
    for i, dim in enumerate(dimensions):
        v = scores_before.get(dim, 0) / 10.0
        r = radius * v
        angle = -math.pi / 2 + 2 * math.pi * i / n
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fca5a5"/>')

    parts.append('</svg>')

    # Legend
    parts.append('<div class="radar-legend">')
    parts.append('<div class="legend-item"><div class="legend-color" style="background:#fca5a5;"></div><span style="color:#94a3b8;">改写前</span></div>')
    parts.append('<div class="legend-item"><div class="legend-color" style="background:#38bdf8;"></div><span style="color:#94a3b8;">改写后</span></div>')
    parts.append('</div>')

    return "".join(parts)


def estimate_geo_scores(content):
    """Estimate GEO scores from text features (heuristic, 0-10 each)."""
    import re
    lines = content.split("\n")

    # QA visibility
    qa = content.count("？") + content.count("?")
    qa_score = min(10, qa * 3)

    # Entity density
    entities = len(re.findall(r'[A-Z][a-z]+|[A-Z]{2,}', content))
    entity_score = min(10, entities)

    # Citation anchors
    citations = len(re.findall(r'[\d]+%|根据|来源|引用|报告|研究|显示|数据', content))
    citation_score = min(10, citations * 2)

    # Structured markup
    h2 = sum(1 for l in lines if l.startswith("## "))
    h3 = sum(1 for l in lines if l.startswith("### "))
    bold = content.count("**")
    lists = sum(1 for l in lines if l.strip().startswith("- ") or l.strip().startswith("* "))
    struct_score = min(10, (h2 * 2 + h3 + bold // 2 + lists) // 2)

    # Platform adaptation (baseline)
    platform_score = 7

    # Readability
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    avg_len = sum(len(p) for p in paragraphs) / max(1, len(paragraphs))
    readability_score = 10 if avg_len < 300 else (7 if avg_len < 600 else 4)

    return {
        "问答可见性": qa_score,
        "实体密度": entity_score,
        "引用锚点": citation_score,
        "结构化标记": struct_score,
        "平台适配": platform_score,
        "可读性": readability_score,
    }


def main():
    parser = argparse.ArgumentParser(
        description="GEO 可视化报告生成器 — 并排对比 + 统计 + 雷达图 + 五维说明"
    )
    parser.add_argument("--input-before", required=True, help="改写前文章路径")
    parser.add_argument("--input-after", required=True, help="改写后文章路径")
    parser.add_argument("--output", default="report.html", help="输出 HTML 路径 (默认 report.html)")
    parser.add_argument("--brand", default="", help="品牌实体名称")
    parser.add_argument("--platform", default="通用", help="目标平台名称")

    args = parser.parse_args()

    if not os.path.isfile(args.input_before):
        print(f"[ERROR] 文件未找到: {args.input_before}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.input_after):
        print(f"[ERROR] 文件未找到: {args.input_after}", file=sys.stderr)
        sys.exit(1)

    with open(args.input_before, "r", encoding="utf-8") as f:
        before_text = f.read()
    with open(args.input_after, "r", encoding="utf-8") as f:
        after_text = f.read()

    article_name = os.path.basename(args.input_before)
    brand = args.brand or "geo-skills"
    platform_name = args.platform

    # Stats
    bs = count_stats(before_text)
    as_ = count_stats(after_text)

    # GEO scores
    scores_before = estimate_geo_scores(before_text)
    scores_after = estimate_geo_scores(after_text)

    # Radar SVG
    radar_svg = generate_radar_svg(scores_before, scores_after)

    # Content HTML
    before_html = basic_markdown_to_html(before_text)
    after_html = basic_markdown_to_html(after_text)

    # Platform icon
    platform_icon = "✅" if platform_name != "通用" else "⚠️"

    # Build HTML
    html = HTML_TEMPLATE.format(
        article_name=article_name,
        before_chars=bs["chars"],
        after_chars=as_["chars"],
        chars_delta=delta_str(bs["chars"], as_["chars"]),
        chars_delta_class=delta_class(bs["chars"], as_["chars"]),
        before_h2=bs["h2"],
        after_h2=as_["h2"],
        h2_delta=delta_str(bs["h2"], as_["h2"]),
        h2_delta_class=delta_class(bs["h2"], as_["h2"]),
        before_h3=bs["h3"],
        after_h3=as_["h3"],
        h3_delta=delta_str(bs["h3"], as_["h3"]),
        h3_delta_class=delta_class(bs["h3"], as_["h3"]),
        before_bold=bs["bold"],
        after_bold=as_["bold"],
        bold_delta=delta_str(bs["bold"], as_["bold"]),
        bold_delta_class=delta_class(bs["bold"], as_["bold"]),
        before_lists=bs["lists"],
        after_lists=as_["lists"],
        lists_delta=delta_str(bs["lists"], as_["lists"]),
        lists_delta_class=delta_class(bs["lists"], as_["lists"]),
        before_faq=bs["faq"],
        after_faq=as_["faq"],
        faq_delta=delta_str(bs["faq"], as_["faq"]),
        faq_delta_class=delta_class(bs["faq"], as_["faq"]),
        radar_svg=radar_svg,
        brand=brand,
        platform_name=platform_name,
        platform_icon=platform_icon,
        before_content=before_html,
        after_content=after_html,
    )

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[DONE] 可视化报告已生成: {output_path}")
    print(f"  文章: {article_name}")
    print(f"  字数: {bs['chars']} → {as_['chars']} ({delta_str(bs['chars'], as_['chars'])})")
    print(f"  H2:   {bs['h2']} → {as_['h2']} ({delta_str(bs['h2'], as_['h2'])})")
    print(f"  列表: {bs['lists']} → {as_['lists']} ({delta_str(bs['lists'], as_['lists'])})")
    print(f"  FAQ:  {bs['faq']} → {as_['faq']} ({delta_str(bs['faq'], as_['faq'])})")


if __name__ == "__main__":
    main()
