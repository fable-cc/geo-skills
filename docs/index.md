# GEO Skills

> 生成式引擎优化（Generative Engine Optimization）方法论与工具集

## 这是什么

GEO Skills 帮助你把普通文章改写为 AI 搜索引擎（ChatGPT Search、Perplexity、DeepSeek 等）更愿意抓取、引用和推荐的版本。

**核心理念**：AI 搜索引擎的排序逻辑是「相关性 > 权威性 > 结构化程度 > 引用密度」。GEO 不改变文章的灵魂，只增加一扇让 AI 能看见的窗。

## 架构总览

```
geo-skills/
├── geo_rewrite.py          # GEO 改写引擎（核心）
├── geo_content_audit.py    # 内容 GEO 审计
├── geo_keyword_expander.py # 关键词扩展（长尾问题）
├── geo_flow.py             # 管线编排器
├── geo_tracker.py          # 评分追踪（SQLite）
├── geo_watch.py            # 文件监控自动处理
├── geo_cost.py             # 用量/成本估算
├── geo_bench.py            # 性能压测
├── geo_notify.py           # Webhook 通知
├── api_server.py           # Flask Web API
├── visualizer.py           # HTML 可视化报告
├── prompts/                # 多语言提示词（中/英/日/韩）
├── docs/                   # MkDocs 在线文档
├── completions/            # Shell 自动补全
├── tests/                  # 测试用例 + 压测
├── mkdocs.yml              # 文档站点配置
└── pyproject.toml          # 项目元数据
```

## 模块一览

| 模块 | 类型 | 说明 |
|------|------|------|
| `geo_rewrite.py` | 核心 | 五维 GEO 改写，支持多平台、流式输出、dry-run |
| `geo_content_audit.py` | 核心 | 六维评分卡 + 逐段标注 + 优先级改进清单 |
| `geo_keyword_expander.py` | 核心 | 从种子关键词生成 100 个长尾搜索问题 |
| `geo_flow.py` | 编排 | 三条管线：full/single/matrix，汇总 JSON 报告 |
| `geo_tracker.py` | 工具 | SQLite 评分库，统计 + ASCII 趋势图 + CSV 导出 |
| `geo_watch.py` | 工具 | 目录监控，自动改写并归档，支持 daemon |
| `geo_cost.py` | 工具 | 4 模型定价表，单篇/批量/全流程费用估算 |
| `geo_bench.py` | 工具 | 性能压测，吞吐量/内存/阶段耗时 + ASCII 柱状图 |
| `geo_notify.py` | 工具 | Slack/钉钉/企业微信 Webhook 通知 |
| `api_server.py` | 服务 | Flask 5 路由 API，端口 8899 |
| `visualizer.py` | 服务 | 纯标准库 HTML 生成器，雷达图 + 并排对比 |

## 快速导航

- [快速开始](quickstart.md) — 三步上手
- [脚本参考](scripts/geo-rewrite.md) — 全部 CLI 工具文档
- [提示词](prompts/cn.md) — 多语言 GEO 改写提示词
- [方法论](methodology.md) — 五维规则原理
- [竞品分析](competitor-analysis.md) — 5 款竞品拆解
