# geo-tracker

GEO 评分追踪器，使用 SQLite 记录每次改写的评分卡数据，支持统计、趋势分析和 CSV 导出。

## 用法

```bash
python3 geo_tracker.py --<command> [OPTIONS]
```

## 命令

| 命令 | 说明 |
|------|------|
| `--add` | 添加评分记录（需 `--input`） |
| `--list` | 列出最近 20 条记录 |
| `--stats` | 汇总统计（总次数/平均分/最高/最低/各维度均分） |
| `--trend` | 纯 ASCII 折线图展示最近 20 次总分变化 |
| `--export` | 导出 CSV（需 `--output`） |

## 参数

| 参数 | 适用命令 | 说明 |
|------|---------|------|
| `--input` | `--add` | 审计/改写输出文件路径 |
| `--model` | `--add` | 模型名称 |
| `--duration` | `--add` | 处理时长（秒） |
| `--limit` | `--list` `--trend` | 条数上限（默认 20） |
| `--output` | `--export` | CSV 导出路径 |

## 示例

```bash
# 添加记录
geo_tracker.py --add --input article-audit.md

# 查看列表
geo_tracker.py --list

# 统计
geo_tracker.py --stats

# 趋势图
geo_tracker.py --trend

# 导出
geo_tracker.py --export scores.csv
```
