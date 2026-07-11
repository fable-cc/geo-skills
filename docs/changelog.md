# 更新日志

所有 GEO Skills 的重要变更记录。

---

## [2.0.0] — 2026-07-11

### Added — 第二批迭代 (G~AA)

- **管线编排**: `geo_flow.py` — 三条管线（full/single/matrix），汇总 JSON 报告
- **内容审计**: `geo_content_audit.py` — 六维评分卡 + 逐段标注 + 优先级改进清单
- **关键词扩展**: `geo_keyword_expander.py` — 长尾问题生成，CSV 输出
- **GEO 评分追踪**: `geo_tracker.py` — SQLite 评分库，统计 + 趋势图 + CSV 导出
- **文件监控**: `geo_watch.py` — 目录监控自动改写，daemon 模式
- **成本估算**: `geo_cost.py` — 4 模型定价表，单篇/批量/全流程费用估算
- **性能压测**: `geo_bench.py` — 吞吐量/内存/阶段耗时 + ASCII 柱状图
- **Webhook 通知**: `geo_notify.py` — Slack/钉钉/企业微信
- **Web API**: `api_server.py` — Flask 5 路由，端口 8899
- **可视化**: `visualizer.py` — HTML 并排对比 + SVG 雷达图
- **多语言提示词**: 英文版 + 日文版 + 韩文版
- **CI/CD**: GitHub Actions 完整 CI（4 个 Python 版本 + flake8 + AST）
- **Pre-commit**: `.pre-commit-config.yaml`
- **Shell 补全**: Bash + Zsh 自动补全脚本
- **MkDocs 文档站点**: 在线文档体系

### Project Infrastructure

- `pyproject.toml`: console_scripts entry points
- `.github/workflows/ci.yml`: GitHub Actions CI
- `.pre-commit-config.yaml`: Pre-commit hooks
- `mkdocs.yml`: MkDocs 文档站点配置

---

## [1.0.0] — 2026-07-11

### Added — 初始发布

- `geo-rewrite-prompt.md`: GEO 改写提示词模板
- `geo-rewrite-prompt-en.md`: 英文版 GEO 改写提示词
- `geo-rewrite-skill.md`: Hermes Agent Skill 定义
- `geo_rewrite.py`: 可执行 CLI 改写脚本
- `geo-annotated-demo.md`: 标注演示（17 处 GEO 特征）
- `skills/geo-rewrite/`: GEO 改写 Skill 子包
- `skills/geo-content-audit/`: 内容审计 Skill 子包
- `skills/geo-keyword-expander/`: 关键词扩展 Skill 子包

### Features

- 批量处理（`--input-dir`）
- 重试机制（`--retry N`）
- 流式输出（`--stream`）
- 统计对比（`--stats`）
- 多行业改写示例（电商/B2B SaaS/学术）
- 语义深度标注（处方级建议 + 文献引用）
