# visualizer

HTML 可视化报告生成器，纯标准库实现。生成改写前后的并排对比页面，含统计栏和 SVG 雷达图。

## 功能

- 并排对比（改写前 / 改写后）
- 六项统计栏（字数 / H2 数 / H3 数 / 加粗数 / 列表数 / FAQ 数）
- SVG 雷达图（六维 GEO 评分可视化）
- 五维改动说明表
- 深色主题 + 响应式 + 打印友好

## 用法

```bash
python3 visualizer.py --input <改写结果.md> --output <报告.html>
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--input` | PATH | *必填* | 改写结果文件路径 |
| `--output` | PATH | 自动 | HTML 输出路径 |

## 示例

```bash
python3 visualizer.py --input article-geo.md --output report.html
open report.html
```
