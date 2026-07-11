# geo-rewrite

GEO 改写引擎，将普通文章优化为 AI 搜索友好的版本。

## 用法

```bash
python3 geo_rewrite.py --input <文章.md> --output <输出.md> [OPTIONS]
```

或安装后使用全局命令：

```bash
geo-rewrite --input 文章.md --platform zhihu
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--input` | PATH | *必填* | 输入文章路径 |
| `--output` | PATH | 自动 | 输出路径（默认 `原名-geo.md`） |
| `--platform` | STR | 通用 | 目标平台：zhihu/wechat/baijiahao/xiaohongshu |
| `--brand` | STR | — | 品牌实体名称 |
| `--score` | FLAG | — | 输出评分卡 |
| `--json` | FLAG | — | JSON 格式输出 |
| `--stream` | FLAG | — | 流式输出 |
| `--retry` | INT | — | 失败重试次数 |
| `--stats` | FLAG | — | 改写前后对比统计 |
| `--dry-run` | FLAG | — | 只打印 prompt 不调用 API |

## 示例

```bash
# 基础改写
geo-rewrite --input article.md

# 知乎平台 + 品牌
geo-rewrite --input article.md --platform zhihu --brand "景一"

# 预览 prompt（不调 API）
geo-rewrite --input article.md --dry-run

# 批量改写目录
geo-rewrite --input-dir ./articles --output-dir ./output --platform wechat
```
