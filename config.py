"""GEO Skills 统一配置模块。

从环境变量读取配置，提供默认值。
复制 .env.example 为 .env 并填写实际值。
"""

import os

# ── API 配置 ──
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# ── GEO 默认参数 ──
GEO_DEFAULT_PLATFORM: str = os.environ.get("GEO_DEFAULT_PLATFORM", "通用")
GEO_DEFAULT_BRAND: str = os.environ.get("GEO_DEFAULT_BRAND", "")

# ── 超时与重试 ──
GEO_TIMEOUT: int = int(os.environ.get("GEO_TIMEOUT", "180"))
