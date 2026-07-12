#!/usr/bin/env python3
"""
GEO Webhook 通知脚本 — 支持 Slack / 钉钉 / 企业微信三种通道

纯 Python 标准库，不依赖任何第三方包。

用法：
  python3 geo_notify.py --test --platform slack --webhook-url https://hooks.slack.com/...
  python3 geo_notify.py --file output-audit.md --platform dingtalk --webhook-url https://oapi.dingtalk.com/...
  python3 geo_notify.py --message "全部改写完成" --platform wecom --webhook-url https://qyapi.weixin.qq.com/...
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def detect_platform(url):
    """Auto-detect platform from webhook URL."""
    if "hooks.slack.com" in url:
        return "slack"
    if "oapi.dingtalk.com" in url:
        return "dingtalk"
    if "qyapi.weixin.qq.com" in url:
        return "wecom"
    return None


def parse_file_for_score(file_path):
    """Extract score info from audit or rewrite output."""
    if not os.path.isfile(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    info = {
        "file_name": os.path.basename(file_path),
        "total_score": None,
        "platform": "通用",
        "summary": "",
    }

    # Extract total score
    m = re.search(r'(?:総合得点|综合得分|종합 점수|GEO 得点|总分|総合スコア)\s*[:：]\s*(\d+)\s*/\s*60', content)
    if m:
        info["total_score"] = int(m.group(1))

    # Extract platform
    m_plat = re.search(r'プラットフォーム適応\s*\|?\s*(\S+)', content)
    if m_plat:
        info["platform"] = m_plat.group(1)
    else:
        m_plat = re.search(r'適用したプラットフォーム\s*\|?\s*\**\s*(\S+)', content)
        if m_plat:
            info["platform"] = m_plat.group(1)

    # Extract summary (last "まとめ"/"总结"/"요약" section)
    for marker in ["## まとめ", "## 总结", "## 요약", "## Summary"]:
        idx = content.rfind(marker)
        if idx != -1:
            summary = content[idx + len(marker):].strip()
            # Take first 3 lines
            lines = summary.split("\n")[:3]
            info["summary"] = " ".join(l.strip() for l in lines if l.strip())[:200]
            break

    return info


def build_slack_payload(message, file_info):
    """Build Slack Block Kit JSON payload."""
    blocks: list[dict[str, object]] = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": message or "GEO 改写完成"}
    })

    # Fields section
    fields = []
    if file_info and file_info.get("platform"):
        fields.append({"type": "mrkdwn", "text": f"*平台:* {file_info['platform']}"})
    if file_info and file_info.get("total_score") is not None:
        fields.append({"type": "mrkdwn", "text": f"*GEO 评分:* {file_info['total_score']}/60"})
    if file_info and file_info.get("file_name"):
        fields.append({"type": "mrkdwn", "text": f"*文件:* {file_info['file_name']}"})

    if fields:
        blocks.append({"type": "section", "fields": fields})

    # Summary
    if file_info and file_info.get("summary"):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": file_info["summary"]}
        })

    # Divider & footer
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "GEO Skills · 自动通知"}]
    })

    return json.dumps({"blocks": blocks}, ensure_ascii=False).encode("utf-8")


def build_dingtalk_payload(message, file_info):
    """Build DingTalk Markdown JSON payload."""
    lines = [f"## {message or 'GEO 改写完成'}", ""]
    if file_info and file_info.get("file_name"):
        lines.append(f"**文件:** {file_info['file_name']}")
    if file_info and file_info.get("platform"):
        lines.append(f"**平台:** {file_info['platform']}")
    if file_info and file_info.get("total_score") is not None:
        lines.append(f"**GEO 评分:** {file_info['total_score']}/60")
    if file_info and file_info.get("summary"):
        lines.append("")
        lines.append(file_info["summary"])
    lines.append("")
    lines.append("---")
    lines.append("*GEO Skills · 自动通知*")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": message or "GEO 改写完成",
            "text": "\n".join(lines),
        }
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def build_wecom_payload(message, file_info):
    """Build WeCom Markdown JSON payload."""
    lines = [f"## {message or 'GEO 改写完成'}"]
    if file_info and file_info.get("file_name"):
        lines.append(f"> 文件: <font color=\"info\">{file_info['file_name']}</font>")
    if file_info and file_info.get("platform"):
        lines.append(f"> 平台: {file_info['platform']}")
    if file_info and file_info.get("total_score") is not None:
        lines.append(f"> GEO 评分: <font color=\"warning\">{file_info['total_score']}/60</font>")
    if file_info and file_info.get("summary"):
        lines.append("")
        lines.append(file_info["summary"])
    lines.append("")
    lines.append("<font color=\"comment\">GEO Skills · 自动通知</font>")

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": "\n".join(lines),
        }
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


BUILDERS = {
    "slack": build_slack_payload,
    "dingtalk": build_dingtalk_payload,
    "wecom": build_wecom_payload,
}


def send_notification(webhook_url, payload, platform):
    """Send HTTP POST to webhook."""
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            code = resp.getcode()
            print(f"[OK] {platform} 通知发送成功 (HTTP {code})")
            if body:
                print(f"  响应: {body[:200]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[FAIL] HTTP {e.code}: {body[:300]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[FAIL] 网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_test(args):
    """Send test notification."""
    platform = args.platform or detect_platform(args.webhook_url)
    if platform not in BUILDERS:
        print(f"[ERROR] 无法识别平台，请使用 --platform 指定 (slack/dingtalk/wecom)", file=sys.stderr)
        sys.exit(1)

    test_info = {
        "file_name": "test-article-geo.md",
        "platform": "zhihu",
        "total_score": 52,
        "summary": "这是一条测试通知。GEO Skills 通知系统运行正常。",
    }

    builder = BUILDERS[platform]
    payload = builder("GEO 测试通知", test_info)
    print(f"发送测试通知 → {platform}")
    print(f"  Webhook: {args.webhook_url[:50]}...")
    send_notification(args.webhook_url, payload, platform)


def cmd_notify(args):
    """Send notification with optional file info."""
    platform = args.platform or detect_platform(args.webhook_url)
    if platform not in BUILDERS:
        print(f"[ERROR] 无法识别平台，请使用 --platform 指定 (slack/dingtalk/wecom)", file=sys.stderr)
        sys.exit(1)

    file_info = None
    if args.file:
        file_info = parse_file_for_score(args.file)
        if file_info:
            print(f"解析文件: {file_info['file_name']}")
            if file_info["total_score"]:
                print(f"  GEO 评分: {file_info['total_score']}/60")
            if file_info["platform"]:
                print(f"  平台: {file_info['platform']}")
        else:
            print(f"[WARN] 无法解析文件得分信息，将发送基础通知")

    builder = BUILDERS[platform]
    payload = builder(args.message or "GEO 改写完成", file_info)
    send_notification(args.webhook_url, payload, platform)


def main():
    parser = argparse.ArgumentParser(
        description="GEO Webhook 通知脚本 — Slack / 钉钉 / 企业微信",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持平台:
  Slack        https://hooks.slack.com/services/...
  钉钉          https://oapi.dingtalk.com/robot/send?access_token=...
  企业微信       https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...

示例:
  %(prog)s --test --platform slack --webhook-url https://hooks.slack.com/...
  %(prog)s --file output-audit.md --webhook-url https://oapi.dingtalk.com/...
  %(prog)s --message "10篇全部改写完成" --webhook-url https://qyapi.weixin.qq.com/...
        """,
    )

    parser.add_argument("--webhook-url", default="", help="Webhook URL")
    parser.add_argument("--platform", default="",
                        choices=["slack", "dingtalk", "wecom"],
                        help="平台类型（URL 可自动检测时可省略）")
    parser.add_argument("--message", default="", help="自定义通知消息")
    parser.add_argument("--file", default="", help="附加文件摘要（读取改写/审计结果）")
    parser.add_argument("--test", action="store_true", help="发送测试通知")

    args = parser.parse_args()

    if not args.webhook_url:
        print("[ERROR] 需要 --webhook-url", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if args.test:
        cmd_test(args)
    else:
        cmd_notify(args)


if __name__ == "__main__":
    main()
