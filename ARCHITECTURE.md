# GEO Skills 架构文档

## 模块分层

```
GEO Skills
│
├── 核心引擎
│   ├── geo_rewrite.py       — GEO 改写引擎（种子词→改写→评分）
│   ├── geo_audit.py         — 内容审计引擎（合规/质量/可读性）
│   ├── geo_expand.py        — 关键词扩展（种子词→长尾词CSV）
│   ├── geo_flow.py          — 编排调度（串联扩展→改写→审计→入库）
│   └── geo_compare.py       — 多模型对比（GPT-4o Mini / DeepSeek V3 / Claude 3 Haiku / Qwen Turbo）
│
├── 基础设施
│   ├── config.py            — 全局配置（API Key、模型、路径）
│   ├── api_server.py        — FastAPI 服务端点
│   ├── geo_tracker.py       — 评分追踪与 SQLite 持久化
│   └── visualizer.py        — HTML 可视化报告（并排对比+雷达图+统计）
│
├── 运营工具
│   ├── geo_cost.py          — 费用控制看板
│   ├── geo_watch.py         — 文件监控自动处理
│   ├── geo_notify.py        — Webhook 通知（Slack/钉钉/企业微信）
│   └── geo_bench.py         — 基准评测
│
├── 测试套件
│   └── tests/
│       ├── test_rewrite.py
│       ├── test_audit.py
│       ├── test_expand.py
│       ├── test_flow.py
│       ├── test_compare.py
│       ├── test_tracker.py
│       ├── test_cost.py
│       ├── test_watch.py
│       ├── test_notify.py
│       ├── test_visualizer.py
│       └── conftest.py
│
├── 提示词模板
│   └── prompts/
│       ├── zhihu.txt
│       ├── xiaohongshu.txt
│       └── ...
│
└── 部署
    ├── Dockerfile
    ├── docker-compose.yml
    ├── setup.py
    ├── pyproject.toml
    ├── install.sh
    └── Makefile
```

## 数据流

```
种子词
  │
  ▼
geo_expand（关键词扩展）
  │  长尾词 CSV
  ▼
geo_flow（编排调度）
  │  选择文章
  ▼
geo_rewrite（改写+评分）
  │  改写后文章
  ▼
geo_audit（内容审计）
  │  审计报告
  ▼
geo_tracker（入库）
  │  SQLite
  ▼
geo_compare（多模型对比）
  │  对比报告
  ▼
geo_cost（费控看板）
  │  HTML Dashboard
  ▼
visualizer（可视化报告）+ geo_notify（消息推送）
```

## 扩展指南

### 如何新增一个平台规则？

1. 在 `prompts/` 目录下创建平台提示词文件，如 `prompts/douyin.txt`
2. 在 `geo_rewrite.py` 的 `rewrite()` 函数中增加 platform 分支：

```python
if platform == "douyin":
    prompt_path = os.path.join(SCRIPT_DIR, "prompts", "douyin.txt")
```

### 如何新增一个评测模型？

在 `geo_compare.py` 的 `MODELS` 列表中添加一行模型定义：

```python
{"name": "新模型名", "model": "model-id", "input_price": 0.15, "output_price": 0.60},
```

## 目录总览

| 文件 | 用途 |
|------|------|
| `geo_rewrite.py` | GEO 改写核心引擎 |
| `geo_audit.py` | 内容审计与评分 |
| `geo_expand.py` | 关键词长尾扩展 |
| `geo_flow.py` | 全链路编排调度 |
| `geo_compare.py` | 多模型对比评测 |
| `geo_tracker.py` | 评分追踪 SQLite |
| `config.py` | 全局配置管理 |
| `api_server.py` | FastAPI REST 服务 |
| `visualizer.py` | HTML 可视化报告 |
| `geo_cost.py` | 费用控制看板 |
| `geo_watch.py` | 文件监控处理 |
| `geo_notify.py` | Webhook 消息通知 |
| `geo_bench.py` | 基准测试工具 |
| `demo.sh` | 一键零 API Key 演示 |
| `Makefile` | 构建/测试/部署/代码检查 |
| `Dockerfile` | 容器化部署 |
| `install.sh` | 一键安装脚本 |
| `setup.py` | 包构建元数据 |
| `pyproject.toml` | 现代 PyPI 打包配置 |
| `RELEASE_v1.1.0.md` | 版本发布说明 |
