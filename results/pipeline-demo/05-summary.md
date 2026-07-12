# 全链路摘要

**管道模式**：full (mock)  
**执行时间**：2026-07-12T10:30:00  

| 步骤 | 输入 | 输出 | 耗时 |
|------|------|------|------|
| 1. 关键词扩展 | 种子词: AI工具 | `01-keywords.csv` (3行) | 0.2s |
| 2. 内容改写 | 原始文章 → geo_rewrite | `02-rewritten.md` | 0.5s |
| 3. GEO 审计 | 改写后文章 → audit | `03-audit.md` (53/70) | 0.3s |
| 4. 结果入库 | 审计结果 → tracker | `04-tracker.json` | 0.1s |
| 5. 摘要汇总 | 全链路数据 | `05-summary.md` | 0.1s |

**总耗时**：1.2s (mock)  
**输出目录**：`results/pipeline-demo/`
