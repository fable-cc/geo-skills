#!/usr/bin/env python3
"""
GEO 文件监控自动处理 — 监控目录，自动将 .md/.txt 文件 GEO 改写

纯 Python 标准库轮询实现，不依赖 watchdog。

用法：
  python3 geo_watch.py --dir ./input --output-dir ./output
  python3 geo_watch.py --dir ./input --platform zhihu --brand "景一"
  python3 geo_watch.py --dir ./input --once                     # 仅处理一次
  python3 geo_watch.py --dir ./input --daemon --interval 10     # 后台运行
"""

import argparse
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_script(name):
    return os.path.join(SCRIPT_DIR, name)


def process_file(file_path, output_dir, platform, brand, dry_run):
    """Run geo_rewrite.py on a single file."""
    base = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_dir, f"{base}-geo.md")

    cmd = [
        sys.executable,
        resolve_script("geo_rewrite.py"),
        "--input", file_path,
        "--output", output_path,
    ]
    if platform:
        cmd += ["--platform", platform]
    if brand:
        cmd += ["--brand", brand]
    if dry_run:
        cmd.append("--dry-run")

    print(f"  [{time.strftime('%H:%M:%S')}] 处理: {os.path.basename(file_path)}")
    if dry_run:
        print(f"    [DRY-RUN] {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy(), timeout=300)
        if result.returncode == 0:
            print(f"    [OK] → {output_path}")
            return True
        else:
            print(f"    [FAIL] {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    [TIMEOUT] 处理超时")
        return False
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False


def scan_and_process(watch_dir, output_dir, processed_dir, platform, brand, dry_run, once):
    """Scan directory and process new .md/.txt files."""
    os.makedirs(watch_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    known_files = set()

    while True:
        try:
            entries = list(os.scandir(watch_dir))
        except OSError as e:
            print(f"[WARN] 扫描目录失败: {e}", file=sys.stderr)
            if once:
                break
            time.sleep(5)
            continue

        new_files = []
        for entry in entries:
            if not entry.is_file():
                continue
            name = entry.name
            ext = os.path.splitext(name)[1].lower()
            if ext not in (".md", ".txt"):
                continue
            if entry.path in known_files:
                continue

            new_files.append(entry.path)
            known_files.add(entry.path)

        if new_files:
            print(f"\n[{time.strftime('%H:%M:%S')}] 发现 {len(new_files)} 个新文件")
            for fpath in new_files:
                success = process_file(fpath, output_dir, platform, brand, dry_run)
                if success:
                    # Move to processed/
                    dest = os.path.join(processed_dir, os.path.basename(fpath))
                    try:
                        os.rename(fpath, dest)
                        print(f"    已归档 → {processed_dir}/")
                    except OSError as e:
                        print(f"    [WARN] 归档失败: {e}")

        if once:
            break

        time.sleep(args.interval)


def daemonize():
    """Fork into background (Unix only)."""
    if os.name != "posix":
        print("[WARN] --daemon 仅支持 Unix 系统", file=sys.stderr)
        return

    pid = os.fork()
    if pid > 0:
        print(f"守护进程已启动 (PID: {pid})")
        sys.exit(0)

    os.setsid()
    # Redirect stdio to /dev/null
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)


def main():
    parser = argparse.ArgumentParser(
        description="GEO 文件监控自动处理 — 监控目录 .md/.txt 自动改写",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --dir ./input --output-dir ./output
  %(prog)s --dir ./input --platform zhihu --brand "景一"
  %(prog)s --dir ./input --once
  %(prog)s --dir ./input --daemon --interval 10
        """,
    )

    parser.add_argument("--dir", default="./input", help="监控目录 (默认 ./input/)")
    parser.add_argument("--output-dir", default="./output", help="输出目录 (默认 ./output/)")
    parser.add_argument("--platform", default="", help="目标平台 (zhihu/wechat/baijiahao/xiaohongshu)")
    parser.add_argument("--brand", default="", help="品牌实体名称")
    parser.add_argument("--daemon", action="store_true", help="后台运行 (仅 Unix)")
    parser.add_argument("--interval", type=int, default=5, help="轮询间隔秒数 (默认 5)")
    parser.add_argument("--once", action="store_true", help="仅处理当前已有文件后退出")
    parser.add_argument("--dry-run", action="store_true", help="只打印命令不执行")

    args = parser.parse_args()

    watch_dir = os.path.abspath(args.dir)
    output_dir = os.path.abspath(args.output_dir)
    processed_dir = os.path.abspath(os.path.join(watch_dir, "..", "processed"))

    if args.daemon:
        daemonize()

    print("GEO Watch — 文件监控自动处理")
    print(f"  监控目录:   {watch_dir}")
    print(f"  输出目录:   {output_dir}")
    print(f"  归档目录:   {processed_dir}")
    print(f"  轮询间隔:   {args.interval}s")
    if args.platform:
        print(f"  目标平台:   {args.platform}")
    if args.brand:
        print(f"  品牌实体:   {args.brand}")
    if args.once:
        print(f"  模式:       单次处理")
    if args.dry_run:
        print(f"  模式:       DRY-RUN")

    if not args.daemon:
        print(f"  PID:         {os.getpid()}")

    print()

    try:
        scan_and_process(
            watch_dir, output_dir, processed_dir,
            args.platform, args.brand, args.dry_run, args.once,
        )
    except KeyboardInterrupt:
        print("\n[STOP] 已停止监控")


if __name__ == "__main__":
    main()
