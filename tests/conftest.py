"""测试共享 fixture。兼容 pytest 和 unittest。"""

import os
import tempfile
from pathlib import Path

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def sample_article():
    """返回健康类测试文章内容。"""
    path = TEST_DATA_DIR / "article_health.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def tmp_db():
    """创建临时 SQLite 数据库，返回路径，用后删除。"""
    import sqlite3
    fd, path = tempfile.mkstemp(suffix=".db", prefix="geo_test_")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article TEXT,
            total_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()
    return path


def mock_env(**kwargs):
    """临时修改环境变量，返回原始值字典。"""
    original = {}
    for k, v in kwargs.items():
        original[k] = os.environ.get(k)
        os.environ[k] = str(v)
    return original


def restore_env(original):
    """恢复 mock_env 修改的环境变量。"""
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
