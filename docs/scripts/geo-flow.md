# geo-flow

管线编排器，将关键词扩展 → GEO 改写 → 内容审计串联为完整流水线。

## 管线模式

| 模式 | 说明 |
|------|------|
| `full` | 四阶段全流程：expand → rewrite → audit → report |
| `single` | 单篇处理：rewrite + audit → 双报告 |
| `matrix` | 批量改写：多文章 × 多平台矩阵 |

## 用法

```bash
python3 geo_flow.py --mode <模式> [OPTIONS]
```

或：

```bash
geo-flow --mode full --keywords "AI工具" --top 10
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--mode` | STR | full | 管线模式：full/single/matrix |
| `--keywords` | STR | — | 种子关键词（逗号分隔） |
| `--input` | PATH | — | 单篇文章路径（single 模式） |
| `--count` | INT | 100 | 关键词扩展数量 |
| `--top` | INT | 10 | 选取前 N 个改写 |
| `--platform` | STR | — | 目标平台 |
| `--brand` | STR | — | 品牌实体 |
| `--output-dir` | PATH | — | 输出目录 |
| `--dry-run` | FLAG | — | 只打印执行计划 |

## 示例

```bash
# 全流程（预览）
geo-flow --mode full --keywords "AI工具,效率提升" --top 10 --dry-run

# 单篇
geo-flow --mode single --input article.md --platform zhihu

# 批量矩阵
geo-flow --mode matrix --input-dir ./articles --platform zhihu --platform wechat
```
