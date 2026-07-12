# v1.1.0 Release Notes

## 新增 (v1.0.0 → v1.1.0)

### 测试套件
- 28 个单元+集成测试全绿 (tests/test_core.py + tests/test_pipeline.py)
- CI 配置 (.github/workflows/test.yml) 自动运行语法检查 + dry-run 验证

### 配置中心化
- config.py + .env.example，geo_rewrite.py 已接入环境变量配置
- 支持 API Key / Base URL / Model / Timeout 通过环境变量注入

### 多语言提示词
- prompts/geo-rewrite-prompt-ja.md — 完整日文版 GEO 改写提示词（五维规则 + 平台规则 + 60点満点评分卡）
- prompts/geo-rewrite-prompt-ko.md — 完整韩文版 GEO 改写提示词

### 性能压测
- geo_bench.py — 纯标准库压测脚本，支持 mock/dry/real 三种模式
- 20 个中文内容模板随机组合生成 mock 文章（300~800 字），输出吞吐量/内存峰值/阶段耗时 + ASCII 柱状图

### 文档站点
- MkDocs 完整文档站点（Material 主题/slate 配色）
- docs/ 下 11 个脚本参考页 + 4 种提示词索引 + index/quickstart/methodology/changelog

### Webhook 通知
- geo_notify.py — 纯标准库 Webhook 通知，支持 Slack/钉钉/企业微信三种通道
- URL 自动检测，--file 自动解析审计/改写文件提取评分

### 验收录
- results/demo-{health,tech,business}/ 含验收 README + 原始文章 + 评判标准 + 结果记录表

### CLI 扩展
- geo_compare.py — 多模型对比脚本，模拟 4 模型（GPT-4o-Mini / DeepSeek / Claude-3-Haiku / Qwen-Turbo）展示 prompt 差异和预估 token/费用
- geo_tracker.py 新增 `--export csv` / `--export json` 导出功能
- geo_cost.py 新增 `--dashboard` HTML 费用看板（暗色主题，纯内联 CSS，无外部依赖）

### 部署
- setup.py — PyPI 打包就绪，兼容旧版 pip
- install.sh — 一键安装脚本（环境检测 + pip 安装 + .env 配置 + shell 补全提示）
- INSTALL.md — 三种安装方式完整文档

### 文档
- README.md 四枚徽章（CI / Python / License / Version）
- RELEASE_v1.1.0.md 本文件

## 修复

- 无（本版本为功能性新增）

## 兼容性

- Python >= 3.10
- pip >= 21.0（推荐），setup.py 兼容旧版 pip
- macOS / Linux / Windows
