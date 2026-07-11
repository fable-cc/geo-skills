# geo-expand

关键词扩展脚本，从种子关键词生成长尾搜索问题（基于 6 个用户意图维度）。

## 用法

```bash
python3 geo_keyword_expander.py --keywords <关键词> --output <输出.csv> [OPTIONS]
```

或：

```bash
geo-expand --keywords "AI工具,效率提升" --output keywords.csv
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--keywords` | STR | *必填* | 种子关键词（逗号分隔） |
| `--count` | INT | 100 | 生成问题数量 |
| `--output` | PATH | *必填* | CSV 输出路径 |
| `--dry-run` | FLAG | — | 只打印 prompt |

## 输出 CSV

包含字段：搜索问题、意图维度、搜索量预估、AI 引用潜力、竞争度评分

## 示例

```bash
geo-expand --keywords "幽门螺杆菌,治疗" --output keywords.csv
geo-expand --keywords "Python编程" --count 50 --output python_kw.csv
```
