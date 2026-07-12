#!/usr/bin/env python3
"""
GEO API Server — Flask 薄封装

依赖: pip install flask

路由:
  GET  /health          — 健康检查
  POST /api/audit       — 内容审计 → geo_content_audit.py
  POST /api/rewrite     — 内容改写 → geo_rewrite.py
  POST /api/expand      — 关键词扩展 → geo_keyword_expander.py
  POST /api/flow        — 管道编排 → geo_flow.py

启动:
  python3 api_server.py
  python3 api_server.py --port 8080
"""

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import tempfile

# --- Flask dependency (install: pip install flask) ---
try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Flask 未安装。请运行: pip install flask", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION = "1.0.0"

app = Flask(__name__)


def resolve_script(name):
    return os.path.join(SCRIPT_DIR, name)


def run_script(script_name, args_list, timeout=120):
    """Run a geo-skills script as subprocess and return stdout."""
    script_path = resolve_script(script_name)
    cmd = [sys.executable, script_path] + args_list
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy(), timeout=timeout)
        if result.returncode != 0:
            return None, result.stderr.strip()
        return result.stdout.strip(), None
    except subprocess.TimeoutExpired:
        return None, "Request timeout"
    except FileNotFoundError:
        return None, f"Script not found: {script_name}"
    except Exception as e:
        return None, str(e)


def print_routes():
    """Print Swagger-style route table on startup."""
    print("=" * 56)
    print("  GEO API Server v" + VERSION)
    print("=" * 56)
    print(f"  {'方法':<8} {'路由':<22} {'说明'}")
    print(f"  {'-'*6} {'-'*20} {'-'*26}")
    print(f"  GET     /health              健康检查")
    print(f"  POST    /api/audit           内容GEO审计")
    print(f"  POST    /api/rewrite         内容GEO改写")
    print(f"  POST    /api/expand          关键词扩展")
    print(f"  POST    /api/flow            管道编排")
    print("=" * 56)


# --- Routes ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": VERSION})


@app.route("/api/audit", methods=["POST"])
def api_audit():
    data = request.get_json(silent=True) or {}
    article = data.get("article", "")
    platform = data.get("platform", "")

    if not article:
        return jsonify({"success": False, "error": "缺少必填字段: article"}), 400

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(article)
        input_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        output_path = f.name

    args = ["--input", input_path, "--output", output_path]
    if platform:
        args += ["--platform", platform]

    stdout, error = run_script("geo_content_audit.py", args)

    # Cleanup input temp file
    try:
        os.unlink(input_path)
    except OSError:
        pass

    if error:
        return jsonify({"success": False, "error": error}), 500

    # Read output
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            result_text = f.read()
        os.unlink(output_path)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "data": {"audit_result": result_text}})


@app.route("/api/rewrite", methods=["POST"])
def api_rewrite():
    data = request.get_json(silent=True) or {}
    article = data.get("article", "")
    platform = data.get("platform", "")
    brand = data.get("brand", "")

    if not article:
        return jsonify({"success": False, "error": "缺少必填字段: article"}), 400

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(article)
        input_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        output_path = f.name

    args = ["--input", input_path, "--output", output_path]
    if platform:
        args += ["--platform", platform]
    if brand:
        args += ["--brand", brand]

    stdout, error = run_script("geo_rewrite.py", args)

    try:
        os.unlink(input_path)
    except OSError:
        pass

    if error:
        return jsonify({"success": False, "error": error}), 500

    try:
        with open(output_path, "r", encoding="utf-8") as f:
            result_text = f.read()
        os.unlink(output_path)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "data": {"rewritten": result_text}})


@app.route("/api/expand", methods=["POST"])
def api_expand():
    data = request.get_json(silent=True) or {}
    keywords = data.get("keywords", "")
    count = data.get("count", 50)

    if not keywords:
        return jsonify({"success": False, "error": "缺少必填字段: keywords"}), 400

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        output_path = f.name

    args = ["--keywords", keywords, "--count", str(count), "--output", output_path]
    stdout, error = run_script("geo_keyword_expander.py", args)

    if error:
        try:
            os.unlink(output_path)
        except OSError:
            pass
        return jsonify({"success": False, "error": error}), 500

    # Parse CSV → JSON
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader]
        os.unlink(output_path)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "data": {"count": len(rows), "keywords": rows}})


@app.route("/api/flow", methods=["POST"])
def api_flow():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "single")

    if mode not in ("full", "single", "matrix"):
        return jsonify({"success": False, "error": f"无效 mode: {mode}"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        args = ["--mode", mode, "--output-dir", tmpdir]

        if mode == "single":
            article = data.get("article", "")
            if not article:
                return jsonify({"success": False, "error": "single 模式需要 article"}), 400
            input_path = os.path.join(tmpdir, "input.md")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(article)
            args += ["--input", input_path]
        else:
            keywords = data.get("keywords", "")
            if not keywords:
                return jsonify({"success": False, "error": f"{mode} 模式需要 keywords"}), 400
            args += ["--keywords", keywords]
            args += ["--count", str(data.get("count", 100))]
            args += ["--top", str(data.get("top", 10))]

        platform = data.get("platform", "")
        if platform:
            args += ["--platform", platform]
        brand = data.get("brand", "")
        if brand:
            args += ["--brand", brand]

        stdout, error = run_script("geo_flow.py", args, timeout=300)

        if error:
            return jsonify({"success": False, "error": error}), 500

        # Read report
        report_path = os.path.join(tmpdir, "flow_report.json")
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = {"raw_output": stdout}

        return jsonify({"success": True, "data": report})


def main():
    parser = argparse.ArgumentParser(description="GEO API Server")
    parser.add_argument("--port", type=int, default=8899, help="服务端口 (默认 8899)")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址 (默认 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    print_routes()
    print(f"\n  Listening on http://{args.host}:{args.port}")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
