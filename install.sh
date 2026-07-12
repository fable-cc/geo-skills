#!/usr/bin/env bash
#
# GEO Skills 一键安装脚本
# 用途：自动检测环境，安装 geo-skills 及其依赖
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

ok()   { echo -e "  ${GREEN}[OK]${NC}   $1"; }
skip() { echo -e "  ${YELLOW}[SKIP]${NC} $1"; }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; }

echo ""
echo "================================="
echo "  GEO Skills v1.1.0 安装脚本"
echo "================================="
echo ""

# ---- Step 1: Python version check ----
echo "[1/5] 检测 Python 版本..."

PYTHON=""
for py in python3 python; do
    if command -v "$py" &>/dev/null; then
        ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        if [ -n "$ver" ]; then
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                PYTHON="$py"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    fail "需要 Python >= 3.10，当前未检测到符合要求的版本。"
    echo "  请先安装 Python 3.10+ 后再运行本脚本。"
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1)
ok "$PY_VER"

# ---- Step 2: pip check ----
echo "[2/5] 检测 pip..."

if "$PYTHON" -m pip --version &>/dev/null; then
    PIP_VER=$("$PYTHON" -m pip --version 2>&1 | cut -d' ' -f1,2)
    ok "pip 可用 ($PIP_VER)"
else
    fail "pip 不可用，请先安装 pip。"
    exit 1
fi

# ---- Step 3: pip install -e . ----
echo "[3/5] 安装 geo-skills（开发模式）..."

cd "$SCRIPT_DIR"

if "$PYTHON" -m pip install -e . --quiet 2>&1; then
    ok "geo-skills 安装成功"
else
    fail "安装失败，请检查错误输出。"
    exit 1
fi

# ---- Step 4: .env setup ----
echo "[4/5] 配置 .env..."

if [ -f "$SCRIPT_DIR/.env" ]; then
    skip ".env 已存在，跳过"
else
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        ok ".env 已从 .env.example 创建，请编辑填入 API Key"
    else
        skip ".env.example 不存在，跳过"
    fi
fi

# ---- Step 5: shell completions ----
echo "[5/5] 配置 Shell 补全..."

CURRENT_SHELL="$(basename "$SHELL" 2>/dev/null || echo "unknown")"

case "$CURRENT_SHELL" in
    bash)
        if [ -f "$SCRIPT_DIR/completions/geo-rewrite.bash" ]; then
            echo ""
            echo "  检测到 bash，运行以下命令启用补全："
            echo ""
            echo "    source $SCRIPT_DIR/completions/geo-rewrite.bash"
            echo ""
            echo "  建议将上述命令追加到 ~/.bashrc 中。"
        fi
        ;;
    zsh)
        if [ -f "$SCRIPT_DIR/completions/geo-rewrite.zsh" ]; then
            echo ""
            echo "  检测到 zsh，运行以下命令启用补全："
            echo ""
            echo "    source $SCRIPT_DIR/completions/geo-rewrite.zsh"
            echo ""
            echo "  建议将上述命令追加到 ~/.zshrc 中。"
        fi
        ;;
    *)
        skip "当前 shell ($CURRENT_SHELL) 无预置补全，可手动 source completions/ 下脚本"
        ;;
esac

echo ""
echo "================================="
echo "  安装完成！"
echo "================================="
echo ""
echo "  验证安装:"
echo "    geo-rewrite --help"
echo "    geo-audit --help"
echo "    geo-expand --help"
echo ""
