# 验收 Demo：AI 工具效率对比

## 原始文章

[`original.md`](original.md) — AI 工具效率提升科普文章（约 600 字）。

## 验收脚本

```bash
cd /path/to/geo-skills/results/demo-tech

OPENAI_API_KEY=sk-your-key-here \
python3 ../../geo_flow.py \
  --mode single \
  --input original.md \
  --platform zhihu \
  --brand "景一·寓言城堡" \
  --score \
  --json
```

## 预期结果

| 指标 | 合格线 | 优秀线 |
|------|--------|--------|
| GEO 总评分 | ≥ 45 / 60 | ≥ 50 / 60 |
| 问答可见性 | ≥ 6 / 10 | ≥ 8 / 10 |
| 实体密度 | ≥ 6 / 10 | ≥ 8 / 10 |
| 引用锚点 | ≥ 6 / 10 | ≥ 8 / 10 |
| 结构化标记 | ≥ 6 / 10 | ≥ 8 / 10 |
| 平台适配 | ≥ 6 / 10 | ≥ 8 / 10 |
| 可读性 | ≥ 6 / 10 | ≥ 8 / 10 |

## 结果记录

| 日期 | 模型 | 总评分 | 耗时 | 备注 |
|------|------|--------|------|------|
| — | — | — | — | 待运行 |
