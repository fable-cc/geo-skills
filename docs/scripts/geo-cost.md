# geo-cost

用量 / 成本估算器，估算单篇或批量 GEO 改写的 token 消耗和 API 费用。

## 定价表

| 模型 | 输入 $/1M tokens | 输出 $/1M tokens |
|------|-----------------|-----------------|
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.00 |
| deepseek-v3 | $0.27 | $1.10 |
| claude-3.5-sonnet | $3.00 | $15.00 |

Token 估算策略：中文约 1.5 字符/token，输出按输入 1.3 倍估算。

## 用法

```bash
python3 geo_cost.py --<command> [OPTIONS]
```

## 模式

| 模式 | 参数 | 说明 |
|------|------|------|
| 单篇 | `--input` | 估算单篇文章各模型费用 |
| 批量 | `--input-dir` | 估算目录中所有文章费用 |
| 全流程 | `--keywords` | 估算 expand + rewrite + audit 全流程 |

## 参数

| 参数 | 适用 | 说明 |
|------|------|------|
| `--input` | 单篇 | 文章路径 |
| `--input-dir` | 批量 | 文章目录 |
| `--keywords` | 全流程 | 种子关键词 |
| `--count` | 全流程 | expand 数量（默认 100） |
| `--top` | 全流程 | 选取前 N 改写（默认 10） |
| `--model` | 全部 | 指定模型，不指定则全列表 |

## 示例

```bash
# 单篇（所有模型）
geo_cost.py --input article.md

# 单篇（指定模型）
geo_cost.py --input article.md --model gpt-4o-mini

# 批量
geo_cost.py --input-dir ./articles

# 全流程
geo_cost.py --keywords "AI工具" --count 100 --top 10
```
