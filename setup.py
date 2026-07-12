#!/usr/bin/env python3
"""
geo-skills setup.py — 兼容旧版 pip（< 21.3）的安装入口。
元数据主源仍是 pyproject.toml；此文件仅提供 setup() 调用。
"""

from setuptools import find_packages, setup

setup(
    name="geo-skills",
    version="1.1.0",
    description="GEO (Generative Engine Optimization) toolset — optimize articles for AI search engines",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="景一·寓言城堡",
    url="https://github.com/fable-cc/geo-skills",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "geo-rewrite=geo_skills.geo_rewrite:main",
            "geo-audit=geo_skills.geo_content_audit:main",
            "geo-expand=geo_skills.geo_keyword_expander:main",
            "geo-flow=geo_skills.geo_flow:main",
            "geo-tracker=geo_skills.geo_tracker:main",
            "geo-watch=geo_skills.geo_watch:main",
            "geo-cost=geo_skills.geo_cost:main",
            "geo-bench=geo_skills.geo_bench:main",
            "geo-notify=geo_skills.geo_notify:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Text Processing :: Markup",
    ],
)
